from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from diagnostics_core.model import DiagnosisState
from services.diagnostics_service import DiagnosticsService
from services.factory import open_planner_services
from storage.backup import create_backup


class I012DiagnosticsServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="provoware-i012-")
        self.workspace = Path(self.temp.name)
        self.database_path = self.workspace / "planer.sqlite3"
        self.services = open_planner_services(self.database_path)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def service(self) -> DiagnosticsService:
        return DiagnosticsService(
            self.services.database,
            self.services.journal,
            workspace=self.workspace,
        )

    def test_dashboard_snapshot_has_five_required_areas_and_no_data_write(self) -> None:
        todo = self.services.todos.create_todo(title="Unverändert")
        before = self.services.todos.get_todo(todo.todo_id)
        receipts_before = len(self.services.journal.list_records())
        snapshot = self.service().snapshot()
        after = self.services.todos.get_todo(todo.todo_id)
        receipts_after = len(self.services.journal.list_records())
        self.assertEqual(
            {item.item_id for item in snapshot.items},
            {"START", "DATABASE", "JOURNAL", "BACKUP", "RECOVERY"},
        )
        self.assertEqual(before, after)
        self.assertEqual(receipts_before, receipts_after)

    def test_database_check_is_read_only_and_ready(self) -> None:
        item = self.service().snapshot().item("DATABASE")
        self.assertEqual(item.state, DiagnosisState.READY)
        self.assertIn("quick_check", item.summary)
        self.assertIn("read-only", item.details)

    def test_missing_start_report_is_yellow_not_red(self) -> None:
        item = self.service().snapshot().item("START")
        self.assertEqual(item.state, DiagnosisState.LIMITED)

    def test_ready_start_report_is_green(self) -> None:
        (self.workspace / "LETZTER_STARTBERICHT.json").write_text(
            json.dumps({"state": "READY", "user_summary": "Startprüfung erfolgreich."}),
            encoding="utf-8",
        )
        item = self.service().snapshot().item("START")
        self.assertEqual(item.state, DiagnosisState.READY)
        self.assertIn("erfolgreich", item.summary)

    def test_valid_backup_is_green_and_hash_tamper_is_detected(self) -> None:
        backup_dir = self.workspace / "backups"
        backup = backup_dir / "manual.sqlite3"
        create_backup(self.services.database, backup)
        item = self.service().snapshot().item("BACKUP")
        self.assertEqual(item.state, DiagnosisState.READY)

        with backup.open("ab") as handle:
            handle.write(b"tamper")
        item = self.service().snapshot().item("BACKUP")
        self.assertEqual(item.state, DiagnosisState.BLOCKED)
        self.assertIn("Keine vorhandene Sicherung", item.summary)

    def test_recovery_without_i011_snapshot_is_yellow(self) -> None:
        item = self.service().snapshot().item("RECOVERY")
        self.assertEqual(item.state, DiagnosisState.LIMITED)
        self.assertIn("Noch keine I011", item.summary)


if __name__ == "__main__":
    unittest.main()
