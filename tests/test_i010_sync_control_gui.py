from __future__ import annotations

import os
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QComboBox, QTableWidget

from services.factory import open_planner_services
from services.resolution_service import ResolutionService
from todo_core.model import LinkDirection
from ui.sync_control_window import COLUMNS, SyncControlWindow


ROOT = Path(__file__).resolve().parents[1]


class I010SyncControlGuiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="provoware-i010-gui-")
        self.services = open_planner_services(Path(self.temp.name) / "planer.sqlite3")
        zone = ZoneInfo("Europe/Berlin")
        start = datetime(2026, 8, 14, 13, 0, tzinfo=zone)
        end = start + timedelta(hours=1)
        self.todo = self.services.todos.create_todo(
            title="Basis", description="Basis", start_at=start, due_at=end
        )
        self.event = self.services.calendar.create_event(
            title="Basis", description="Basis", start_at=start, end_at=end, timezone_name="Europe/Berlin"
        )
        self.link = self.services.links.create_link(
            self.todo.todo_id, self.event.event_id, direction=LinkDirection.BIDIRECTIONAL
        )
        self.services.sync.initialize_baseline(self.link.link_id)
        self.services.todos.update_todo(replace(self.todo, title="Todo"), expected_version=self.todo.version)
        self.services.calendar.update_event(replace(self.event, title="Kalender"), expected_version=self.event.version)
        self.resolution = ResolutionService(self.services.sync, self.services.sync.repository)
        self.window = SyncControlWindow(self.services.sync, self.resolution, repo_root=ROOT)
        self.window.show()
        self.app.processEvents()
        index = self.window.link_combo.findText(self.link.link_id)
        self.window.link_combo.setCurrentIndex(index)
        self.window.inspect()
        self.app.processEvents()

    def tearDown(self) -> None:
        self.window.close()
        self.temp.cleanup()

    def test_required_field_table_columns_exist(self) -> None:
        table: QTableWidget = self.window.table
        headers = tuple(table.horizontalHeaderItem(i).text() for i in range(table.columnCount()))
        self.assertEqual(headers, COLUMNS)
        self.assertEqual(table.rowCount(), 4)

    def test_both_different_has_explicit_default_block_choice(self) -> None:
        title_row = next(
            row
            for row in range(self.window.table.rowCount())
            if self.window.table.item(row, 0).text() == "TITLE"
        )
        combo = self.window.table.cellWidget(title_row, 9)
        self.assertIsInstance(combo, QComboBox)
        self.assertEqual(combo.currentText(), "Blockiert lassen")
        self.window.preview_resolution()
        self.assertIn("BLOCKED", self.window.status_label.text())
        self.assertEqual(self.services.sync.receipt_count(self.link.link_id), 0)

    def test_no_conflict_row_has_no_decision_widget(self) -> None:
        description_row = next(
            row
            for row in range(self.window.table.rowCount())
            if self.window.table.item(row, 0).text() == "DESCRIPTION"
        )
        self.assertIsNone(self.window.table.cellWidget(description_row, 9))
        self.assertEqual(self.window.table.item(description_row, 9).text(), "Nicht erforderlich")

    def test_controls_have_accessible_names(self) -> None:
        self.assertTrue(self.window.link_combo.accessibleName())
        self.assertTrue(self.window.inspect_button.accessibleName())
        self.assertTrue(self.window.plan_button.accessibleName())
        self.assertTrue(self.window.execute_button.accessibleName())
        self.assertTrue(self.window.table.accessibleName())


if __name__ == "__main__":
    unittest.main()
