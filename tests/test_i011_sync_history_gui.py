from __future__ import annotations

import os
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from services.factory import open_planner_services
from todo_core.model import LinkDirection
from ui.sync_history_window import DETAIL_COLUMNS, HISTORY_COLUMNS, SyncHistoryWindow

ROOT = Path(__file__).resolve().parents[1]


class I011SyncHistoryGuiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="provoware-i011-gui-")
        self.services = open_planner_services(Path(self.temp.name) / "planer.sqlite3")
        zone = ZoneInfo("Europe/Berlin")
        start = datetime(2026, 8, 14, 15, 0, tzinfo=zone)
        end = start + timedelta(hours=1)
        todo = self.services.todos.create_todo(title="Basis", description="Text", start_at=start, due_at=end)
        event = self.services.calendar.create_event(
            title="Basis", description="Text", start_at=start, end_at=end, timezone_name="Europe/Berlin"
        )
        link = self.services.links.create_link(todo.todo_id, event.event_id, direction=LinkDirection.BIDIRECTIONAL)
        self.services.sync.initialize_baseline(link.link_id)
        self.services.todos.update_todo(replace(todo, title="Nachher"), expected_version=todo.version)
        self.receipt = self.services.sync.commit(self.services.sync.plan(link.link_id))
        self.window = SyncHistoryWindow(self.services.journal, repo_root=ROOT)
        self.window.show()
        self.app.processEvents()

    def tearDown(self) -> None:
        self.window.close()
        self.app.processEvents()
        self.temp.cleanup()

    def test_required_history_and_detail_columns_exist(self) -> None:
        self.assertEqual(self.window.history_table.columnCount(), len(HISTORY_COLUMNS))
        self.assertEqual(self.window.detail_table.columnCount(), len(DETAIL_COLUMNS))
        self.assertIn("Integrität", HISTORY_COLUMNS)
        self.assertIn("Recovery", HISTORY_COLUMNS)
        self.assertIn("Vorher Todo", DETAIL_COLUMNS)
        self.assertIn("Nachher Kalender", DETAIL_COLUMNS)

    def test_history_row_can_be_selected_and_shows_integrity(self) -> None:
        self.assertEqual(self.window.history_table.rowCount(), 1)
        self.window.history_table.selectRow(0)
        self.window.select_current()
        self.app.processEvents()
        self.assertEqual(self.window.detail_table.rowCount(), 4)
        self.assertIn("VERIFIED", self.window.status_label.text())
        self.assertIn(self.receipt.receipt_id, self.window.status_label.text())

    def test_controls_have_accessible_names(self) -> None:
        for widget in (
            self.window.link_filter,
            self.window.refresh_button,
            self.window.history_table,
            self.window.detail_table,
            self.window.reapply_button,
            self.window.restore_button,
            self.window.execute_button,
            self.window.status_label,
        ):
            self.assertTrue(widget.accessibleName().strip(), widget)

    def test_recovery_never_executes_without_prepared_plan(self) -> None:
        self.window.history_table.selectRow(0)
        self.window.select_current()
        self.window.execute()
        self.assertIn("zuerst ausdrücklich prüfen", self.window.status_label.text())


if __name__ == "__main__":
    unittest.main()
