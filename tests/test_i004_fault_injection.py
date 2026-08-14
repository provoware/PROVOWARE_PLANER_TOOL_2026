from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from calendar_core.errors import DatabaseBusyError, DatabaseIntegrityError, RestoreRejectedError
from services.calendar_service import CalendarService
from storage.backup import create_backup, restore_backup
from storage.database import Database
from storage.migrations import MigrationRunner
from storage.repository import CalendarRepository

ROOT = Path(__file__).resolve().parents[1]


class CalendarFaultInjectionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db_path = self.root / "planner.sqlite3"
        self.database = Database(self.db_path, busy_timeout_ms=50)
        MigrationRunner(self.database, ROOT / "migrations").apply_all()
        self.repository = CalendarRepository(self.database)
        self.service = CalendarService(self.repository)
        self.berlin = ZoneInfo("Europe/Berlin")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _create_event(self, title: str = "Fault-Test"):
        start = datetime(2026, 8, 14, 12, 0, tzinfo=self.berlin)
        return self.service.create_event(
            title=title,
            start_at=start,
            end_at=start + timedelta(hours=1),
            timezone_name="Europe/Berlin",
        )

    def test_locked_database_becomes_explicit_busy_error(self) -> None:
        blocker = sqlite3.connect(self.db_path, timeout=0.05)
        try:
            blocker.execute("BEGIN IMMEDIATE")
            blocker.execute("UPDATE marker_types SET title = title WHERE marker_id = 1")
            with self.assertRaises(DatabaseBusyError):
                with self.database.transaction():
                    pass
        finally:
            blocker.rollback()
            blocker.close()

    def test_wrong_backup_hash_is_rejected_before_target_change(self) -> None:
        event = self._create_event("Original")
        backup = self.root / "backup.sqlite3"
        create_backup(self.database, backup)
        with self.assertRaises(RestoreRejectedError):
            restore_backup(backup, self.db_path, expected_sha256="0" * 64)
        self.assertEqual(self.repository.get(event.event_id).title, "Original")

    def test_restore_removes_stale_wal_sidecars(self) -> None:
        event = self._create_event("Backup-Zustand")
        backup = self.root / "backup.sqlite3"
        manifest = create_backup(self.database, backup)
        wal = Path(str(self.db_path) + "-wal")
        shm = Path(str(self.db_path) + "-shm")
        wal.touch(exist_ok=True)
        shm.touch(exist_ok=True)
        restore_backup(backup, self.db_path, expected_sha256=manifest["database_sha256"])
        self.assertFalse(wal.exists())
        self.assertFalse(shm.exists())
        restored = CalendarRepository(Database(self.db_path)).get(event.event_id)
        self.assertEqual(restored.title, "Backup-Zustand")

    def test_corrupt_active_database_fails_integrity_check(self) -> None:
        self.db_path.write_bytes(b"zerstoert")
        with self.assertRaises(DatabaseIntegrityError):
            self.database.quick_check()


if __name__ == "__main__":
    unittest.main()
