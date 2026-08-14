from __future__ import annotations

import shutil
import sqlite3
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from calendar_core.errors import (
    ConcurrentUpdateError,
    DomainValidationError,
    EventNotFoundError,
    MigrationTamperedError,
    RestoreRejectedError,
)
from calendar_core.model import CalendarEvent
from services.calendar_service import CalendarService
from storage.backup import create_backup, restore_backup
from storage.database import Database
from storage.migrations import MigrationRunner
from storage.repository import CalendarRepository

ROOT = Path(__file__).resolve().parents[1]


class CalendarCoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db_path = self.root / "planner.sqlite3"
        self.database = Database(self.db_path, busy_timeout_ms=100)

        # Historischer I004-Test: bewusst nur die I004-Migration verwenden.
        # Spätere Migrationen dürfen die isolierten I004-Invarianten nicht verändern.
        self.i004_migrations = self.root / "i004_migrations"
        self.i004_migrations.mkdir()
        migration_0001 = ROOT / "migrations" / "0001_calendar_core.sql"
        shutil.copy2(migration_0001, self.i004_migrations / migration_0001.name)
        self.runner = MigrationRunner(self.database, self.i004_migrations)
        self.assertEqual(self.runner.apply_all(), [1])

        self.repository = CalendarRepository(self.database)
        self.service = CalendarService(self.repository)
        self.berlin = ZoneInfo("Europe/Berlin")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def create_event(self, title: str = "Termin") -> CalendarEvent:
        start = datetime(2026, 8, 14, 9, 0, tzinfo=self.berlin)
        return self.service.create_event(
            title=title,
            description="Test",
            start_at=start,
            end_at=start + timedelta(hours=1),
            timezone_name="Europe/Berlin",
            marker_id=1,
        )

    def test_schema_and_five_markers_exist(self) -> None:
        self.assertEqual(self.database.schema_version(), 1)
        markers = self.repository.marker_types()
        self.assertEqual(len(markers), 5)
        self.assertEqual([marker.marker_id for marker in markers], [1, 2, 3, 4, 5])

    def test_domain_rejects_empty_title(self) -> None:
        now = datetime.now(timezone.utc)
        with self.assertRaises(DomainValidationError):
            CalendarEvent("x", " ", "", now, now, "UTC")

    def test_domain_rejects_end_before_start(self) -> None:
        now = datetime.now(timezone.utc)
        with self.assertRaises(DomainValidationError):
            CalendarEvent("x", "Test", "", now, now - timedelta(seconds=1), "UTC")

    def test_create_get_and_range_query(self) -> None:
        created = self.create_event()
        loaded = self.service.get_event(created.event_id)
        self.assertEqual(loaded.title, "Termin")
        self.assertEqual(loaded.marker_id, 1)
        self.assertEqual(loaded.start_at.utcoffset(), timedelta(0))
        window_start = datetime(2026, 8, 14, 0, 0, tzinfo=self.berlin)
        window_end = window_start + timedelta(days=1)
        self.assertEqual([item.event_id for item in self.service.list_events(window_start, window_end)], [created.event_id])

    def test_dst_fallback_is_persisted_in_absolute_utc_order(self) -> None:
        start = datetime(2026, 10, 25, 2, 30, tzinfo=self.berlin, fold=0)
        end = datetime(2026, 10, 25, 2, 30, tzinfo=self.berlin, fold=1)
        event = self.service.create_event(
            title="Zeitumstellung",
            start_at=start,
            end_at=end,
            timezone_name="Europe/Berlin",
        )
        loaded = self.service.get_event(event.event_id)
        self.assertLess(loaded.start_at, loaded.end_at)
        self.assertEqual(loaded.timezone, "Europe/Berlin")

    def test_optimistic_lock_blocks_stale_update(self) -> None:
        created = self.create_event()
        changed = replace(created, title="Neu")
        saved = self.service.update_event(changed, expected_version=1)
        self.assertEqual(saved.version, 2)
        with self.assertRaises(ConcurrentUpdateError):
            self.service.update_event(replace(created, title="Veraltet"), expected_version=1)

    def test_soft_delete_hides_event_without_destroying_row(self) -> None:
        created = self.create_event()
        self.service.delete_event(created.event_id, expected_version=1)
        with self.assertRaises(EventNotFoundError):
            self.service.get_event(created.event_id)
        deleted = self.repository.get(created.event_id, include_deleted=True)
        self.assertIsNotNone(deleted.deleted_at)

    def test_transaction_rolls_back_after_crash_like_exception(self) -> None:
        with self.assertRaises(RuntimeError):
            with self.database.transaction() as connection:
                connection.execute(
                    "INSERT INTO calendar_events(event_id,title,description,start_at,end_at,timezone,all_day,marker_id,status,version,created_at,updated_at,deleted_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        "rollback", "Rollback", "", "2026-08-14T07:00:00+00:00", None,
                        "UTC", 0, None, "ACTIVE", 1,
                        "2026-08-14T07:00:00+00:00", "2026-08-14T07:00:00+00:00", None,
                    ),
                )
                raise RuntimeError("simulierter Prozessabbruch")
        with self.database.connect() as connection:
            count = connection.execute("SELECT COUNT(*) FROM calendar_events WHERE event_id='rollback'").fetchone()[0]
        self.assertEqual(count, 0)

    def test_backup_and_restore_roundtrip(self) -> None:
        created = self.create_event("Im Backup")
        backup = self.root / "backup.sqlite3"
        manifest = create_backup(self.database, backup)
        self.service.delete_event(created.event_id, expected_version=1)
        restore_backup(backup, self.db_path, expected_sha256=manifest["database_sha256"])
        restored = CalendarRepository(Database(self.db_path)).get(created.event_id)
        self.assertEqual(restored.title, "Im Backup")

    def test_corrupt_backup_is_rejected_and_active_database_survives(self) -> None:
        created = self.create_event("Bleibt erhalten")
        corrupt = self.root / "corrupt.sqlite3"
        corrupt.write_bytes(b"keine sqlite datenbank")
        with self.assertRaises(RestoreRejectedError):
            restore_backup(corrupt, self.db_path)
        self.database.quick_check()
        self.assertEqual(self.repository.get(created.event_id).title, "Bleibt erhalten")

    def test_migration_history_detects_modified_applied_file(self) -> None:
        migration_copy = self.root / "migrations"
        migration_copy.mkdir()
        source = ROOT / "migrations" / "0001_calendar_core.sql"
        copied = migration_copy / source.name
        shutil.copy2(source, copied)
        other_db = Database(self.root / "tamper.sqlite3")
        runner = MigrationRunner(other_db, migration_copy)
        runner.apply_all()
        copied.write_text(copied.read_text(encoding="utf-8") + "\n-- nachträglich manipuliert\n", encoding="utf-8")
        with self.assertRaises(MigrationTamperedError):
            runner.verify_history()

    def test_database_constraints_reject_unknown_marker(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            with self.database.transaction() as connection:
                connection.execute(
                    "INSERT INTO calendar_events(event_id,title,description,start_at,end_at,timezone,all_day,marker_id,status,version,created_at,updated_at,deleted_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        "bad-marker", "Test", "", "2026-08-14T07:00:00+00:00", None,
                        "UTC", 0, 99, "ACTIVE", 1,
                        "2026-08-14T07:00:00+00:00", "2026-08-14T07:00:00+00:00", None,
                    ),
                )


if __name__ == "__main__":
    unittest.main()
