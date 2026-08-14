from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from services.factory import open_planner_services
from sync_core.history import JournalIntegrityState, JournalPlanKind
from todo_core.model import LinkDirection


class I011HistoryRepositoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="provoware-i011-history-")
        self.services = open_planner_services(Path(self.temp.name) / "planer.sqlite3")
        zone = ZoneInfo("Europe/Berlin")
        start = datetime(2026, 8, 14, 12, 0, tzinfo=zone)
        end = start + timedelta(hours=1)
        self.todo = self.services.todos.create_todo(
            title="Basis", description="Gemeinsam", start_at=start, due_at=end
        )
        self.event = self.services.calendar.create_event(
            title="Basis",
            description="Gemeinsam",
            start_at=start,
            end_at=end,
            timezone_name="Europe/Berlin",
        )
        self.link = self.services.links.create_link(
            self.todo.todo_id,
            self.event.event_id,
            direction=LinkDirection.BIDIRECTIONAL,
        )
        self.services.sync.initialize_baseline(self.link.link_id)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _commit_one_sided_title(self):
        todo = self.services.todos.update_todo(
            replace(self.todo, title="Neuer Titel"),
            expected_version=self.todo.version,
        )
        plan = self.services.sync.plan(self.link.link_id)
        receipt = self.services.sync.commit(plan)
        return todo, receipt

    def test_schema_four_and_atomic_value_snapshot_exist(self) -> None:
        _todo, receipt = self._commit_one_sided_title()
        self.assertEqual(self.services.database.schema_version(), 4)
        records = self.services.journal.list_records(self.link.link_id)
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record.receipt_id, receipt.receipt_id)
        self.assertEqual(record.integrity, JournalIntegrityState.VERIFIED)
        self.assertEqual(record.plan_kind, JournalPlanKind.SYNC)
        self.assertTrue(record.recovery_available)
        self.assertEqual(record.before_todo_values["TITLE"], "Neuer Titel")
        self.assertEqual(record.before_calendar_values["TITLE"], "Basis")
        self.assertEqual(record.after_todo_values["TITLE"], "Neuer Titel")
        self.assertEqual(record.after_calendar_values["TITLE"], "Neuer Titel")
        self.assertEqual(self.services.journal.history_repository.snapshot_count(self.link.link_id), 1)

    def test_legacy_receipt_without_snapshot_remains_auditable_but_not_recoverable(self) -> None:
        _todo, receipt = self._commit_one_sided_title()
        with self.services.database.transaction() as connection:
            connection.execute(
                "DELETE FROM sync_history_snapshots WHERE receipt_id=?",
                (receipt.receipt_id,),
            )
        record = self.services.journal.get_record(receipt.receipt_id)
        self.assertEqual(record.integrity, JournalIntegrityState.LEGACY_NO_SNAPSHOT)
        self.assertFalse(record.recovery_available)
        self.assertIn("nicht automatisch wiederherstellbar", record.integrity_reason)

    def test_tampered_snapshot_is_detected(self) -> None:
        _todo, receipt = self._commit_one_sided_title()
        with self.services.database.transaction() as connection:
            connection.execute(
                "UPDATE sync_history_snapshots SET after_json=? WHERE receipt_id=?",
                ('{"schema_version":1,"fields":{}}', receipt.receipt_id),
            )
        record = self.services.journal.get_record(receipt.receipt_id)
        self.assertEqual(record.integrity, JournalIntegrityState.TAMPERED)
        self.assertFalse(record.recovery_available)

    def test_journal_query_does_not_modify_database(self) -> None:
        _todo, _receipt = self._commit_one_sided_title()
        before = self.services.sync.receipt_count(self.link.link_id)
        for _ in range(3):
            self.services.journal.list_records()
            self.services.journal.list_records(self.link.link_id)
        self.assertEqual(self.services.sync.receipt_count(self.link.link_id), before)


if __name__ == "__main__":
    unittest.main()
