from __future__ import annotations

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QComboBox, QListWidget, QPushButton, QSpinBox

from services.factory import open_planner_services
from todo_core.model import LinkDirection
from ui.todo_window import TodoWindow
from viewmodel.todo_query import TodoListMode

ROOT = Path(__file__).resolve().parents[1]


class I007TodoGuiOffscreenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name)
        self.services = open_planner_services(self.workspace / "planer.sqlite3")
        self.zone = ZoneInfo("Europe/Berlin")
        self.now = datetime.now(self.zone).replace(second=0, microsecond=0)
        self.todo = self.services.todos.create_todo(title="GUI-Aufgabe", due_at=self.now + timedelta(hours=1))
        self.window = TodoWindow(
            self.services.todos,
            self.services.links,
            self.services.calendar,
            repo_root=ROOT,
            workspace=self.workspace,
            timezone_name="Europe/Berlin",
        )
        self.window.show()
        self.app.processEvents()

    def tearDown(self) -> None:
        self.window.close()
        self.app.processEvents()
        self.temp.cleanup()

    def test_five_required_views_are_switchable(self) -> None:
        self.assertEqual(len(TodoListMode), 5)
        for mode in TodoListMode:
            index = self.window.mode_combo.findData(mode)
            self.assertGreaterEqual(index, 0)
            self.window.mode_combo.setCurrentIndex(index)
            self.app.processEvents()
            self.assertEqual(self.window.view_model.mode, mode)

    def test_accessible_names_exist_for_interactive_widgets(self) -> None:
        interactive_types = (QPushButton, QComboBox, QListWidget, QSpinBox)
        missing = []
        for widget_type in interactive_types:
            for widget in self.window.findChildren(widget_type):
                if widget.isVisible() and not widget.accessibleName().strip():
                    missing.append(f"{type(widget).__name__}:{getattr(widget, 'text', lambda: '')()}")
        self.assertEqual(missing, [])

    def test_window_and_font_matrix_has_valid_geometry(self) -> None:
        for width, height in ((1280, 720), (1366, 768), (1600, 900), (1920, 1080)):
            for scale in (90, 100, 110, 125, 150, 175, 200):
                self.window.resize(width, height)
                self.window.font_combo.setCurrentIndex(self.window.font_combo.findData(scale))
                self.window.refresh()
                self.app.processEvents()
                self.assertGreaterEqual(self.window.width(), 900)
                self.assertGreaterEqual(self.window.height(), 600)
                self.assertGreater(self.window.todo_list.width(), 100)
                self.assertGreater(self.window.links_list.width(), 100)
                for button in self.window.findChildren(QPushButton):
                    if button.isVisible():
                        needed = button.fontMetrics().horizontalAdvance(button.text()) + 24
                        self.assertGreaterEqual(button.width(), needed, f"{button.text()} ist bei {scale}% zu schmal")

    def test_status_is_symbol_plus_text_not_color_only(self) -> None:
        text = self.window.status_label.text()
        self.assertIn("●", text)
        self.assertIn("GRUEN", text)
        self.assertIn("BEREIT", text)

    def test_high_contrast_keeps_textual_semantics(self) -> None:
        original = self.app.palette()
        palette = QPalette(original)
        palette.setColor(QPalette.Window, QColor("black"))
        palette.setColor(QPalette.WindowText, QColor("white"))
        palette.setColor(QPalette.Base, QColor("black"))
        palette.setColor(QPalette.Text, QColor("white"))
        self.app.setPalette(palette)
        try:
            self.window.refresh()
            self.app.processEvents()
            self.assertIn("GRUEN", self.window.status_label.text())
            self.assertTrue(self.window.detail_label.text().strip())
        finally:
            self.app.setPalette(original)

    def test_both_changed_conflict_is_visible_without_auto_resolution(self) -> None:
        start = self.now + timedelta(hours=2)
        event = self.services.calendar.create_event(
            title="GUI-Termin",
            start_at=start,
            end_at=start + timedelta(hours=1),
            timezone_name="Europe/Berlin",
        )
        link = self.services.links.create_link(self.todo.todo_id, event.event_id, direction=LinkDirection.BIDIRECTIONAL)
        self.services.todos.update_todo(replace(self.todo, title="GUI-Aufgabe geändert"), expected_version=self.todo.version)
        self.services.calendar.update_event(replace(event, title="GUI-Termin geändert"), expected_version=event.version)
        self.window.refresh()
        self.app.processEvents()
        texts = [self.window.links_list.item(i).text() for i in range(self.window.links_list.count())]
        self.assertTrue(any("Manuelle Prüfung" in text for text in texts), texts)
        stored = self.services.links.get_link(link.link_id)
        self.assertEqual(stored.version, 1)
        self.assertEqual(stored.conflict_status.value, "CLEAN")

    def test_gui_settings_persist_after_restart(self) -> None:
        self.window.mode_combo.setCurrentIndex(self.window.mode_combo.findData(TodoListMode.WITHOUT_DATE))
        self.window.font_combo.setCurrentIndex(self.window.font_combo.findData(150))
        self.window.close()
        self.app.processEvents()
        reopened = TodoWindow(
            self.services.todos,
            self.services.links,
            self.services.calendar,
            repo_root=ROOT,
            workspace=self.workspace,
            timezone_name="Europe/Berlin",
        )
        try:
            self.assertEqual(reopened.view_model.mode, TodoListMode.WITHOUT_DATE)
            self.assertEqual(reopened.view_model.font_scale_percent, 150)
        finally:
            reopened.close()


if __name__ == "__main__":
    unittest.main()
