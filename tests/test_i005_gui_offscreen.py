from __future__ import annotations

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QComboBox, QDateEdit, QListWidget, QPushButton, QTableWidget

from services.factory import open_calendar_service
from ui.calendar_window import CalendarWindow
from viewmodel.calendar_viewmodel import CalendarViewMode

ROOT = Path(__file__).resolve().parents[1]


class I005GuiOffscreenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name)
        self.service = open_calendar_service(self.workspace / "planer.sqlite3")
        zone = ZoneInfo("Europe/Berlin")
        start = datetime(2026, 8, 14, 9, 0, tzinfo=zone)
        self.service.create_event(
            title="GUI-Testtermin",
            start_at=start,
            end_at=start + timedelta(hours=1),
            timezone_name="Europe/Berlin",
            marker_id=2,
        )
        self.window = CalendarWindow(self.service, repo_root=ROOT, workspace=self.workspace, timezone_name="Europe/Berlin")
        self.window.view_model.select_date(date(2026, 8, 14))
        self.window.show()
        self.app.processEvents()

    def tearDown(self) -> None:
        self.window.close()
        self.app.processEvents()
        self.temp.cleanup()

    def test_four_views_are_real_widgets_and_switchable(self) -> None:
        expected = {
            CalendarViewMode.DAY: self.window.day_view,
            CalendarViewMode.WEEK: self.window.week_view,
            CalendarViewMode.MONTH: self.window.month_view,
            CalendarViewMode.YEAR: self.window.year_view,
        }
        for mode, widget in expected.items():
            self.window._set_mode(mode)
            self.app.processEvents()
            self.assertIs(self.window.stack.currentWidget(), widget)

    def test_five_marker_labels_are_simultaneously_visible_with_text(self) -> None:
        self.window.refresh()
        self.app.processEvents()
        self.assertEqual(len(self.window.marker_labels), 5)
        for label in self.window.marker_labels:
            self.assertTrue(label.isVisible())
            self.assertTrue(label.text().strip())
            self.assertGreaterEqual(len(label.text().splitlines()), 2)

    def test_accessible_names_exist_for_interactive_widgets(self) -> None:
        interactive_types = (QPushButton, QComboBox, QDateEdit, QListWidget, QTableWidget)
        missing = []
        for widget_type in interactive_types:
            for widget in self.window.findChildren(widget_type):
                if widget.isVisible() and not widget.accessibleName().strip():
                    missing.append(type(widget).__name__)
        self.assertEqual(missing, [])

    def test_window_and_font_matrix_without_invalid_visible_geometry(self) -> None:
        sizes = ((1280, 720), (1366, 768), (1600, 900), (1920, 1080))
        scales = (90, 100, 110, 125, 150, 175, 200)
        for width, height in sizes:
            for scale in scales:
                self.window.resize(width, height)
                index = self.window.font_combo.findData(scale)
                self.window.font_combo.setCurrentIndex(index)
                self.window.refresh()
                self.app.processEvents()
                self.assertGreaterEqual(self.window.width(), 900)
                self.assertGreaterEqual(self.window.height(), 600)
                self.assertGreater(self.window.stack.width(), 100)
                self.assertGreater(self.window.stack.height(), 100)
                for widget_type in (QPushButton, QComboBox, QDateEdit):
                    for widget in self.window.findChildren(widget_type):
                        if widget.isVisible():
                            self.assertGreater(widget.width(), 0)
                            self.assertGreater(widget.height(), 0)

    def test_action_buttons_refit_after_every_font_scale(self) -> None:
        for scale in (90, 100, 110, 125, 150, 175, 200):
            index = self.window.font_combo.findData(scale)
            self.window.font_combo.setCurrentIndex(index)
            self.app.processEvents()
            for button in self.window.findChildren(QPushButton):
                if not button.isVisible():
                    continue
                required = button.fontMetrics().horizontalAdvance(button.text()) + 24
                self.assertGreaterEqual(
                    button.width(),
                    required,
                    f"{button.text()} ist bei {scale}% zu schmal",
                )

    def test_font_baseline_does_not_compound_between_fresh_windows(self) -> None:
        baseline_size = getattr(self.app, "_provoware_unscaled_base_font").pointSizeF()
        index = self.window.font_combo.findData(200)
        self.window.font_combo.setCurrentIndex(index)
        self.app.processEvents()
        self.assertGreater(self.app.font().pointSizeF(), baseline_size)
        with tempfile.TemporaryDirectory() as second_temp:
            second_workspace = Path(second_temp)
            fresh = CalendarWindow(
                open_calendar_service(second_workspace / "planer.sqlite3"),
                repo_root=ROOT,
                workspace=second_workspace,
                timezone_name="Europe/Berlin",
            )
            try:
                fresh.show()
                self.app.processEvents()
                self.assertEqual(fresh.view_model.font_scale_percent, 100)
                self.assertAlmostEqual(self.app.font().pointSizeF(), baseline_size, delta=0.2)
                self.assertGreater(fresh.stack.height(), 100)
            finally:
                fresh.close()
                self.app.processEvents()

    def test_status_is_symbol_plus_text_not_color_only(self) -> None:
        text = self.window.status_label.text()
        self.assertIn("●", text)
        self.assertIn("GRUEN", text)
        self.assertIn("BEREIT", text)

    def test_high_contrast_palette_keeps_textual_semantics(self) -> None:
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
            self.assertTrue(all(label.text().strip() for label in self.window.marker_labels))
        finally:
            self.app.setPalette(original)

    def test_gui_settings_persist_after_restart(self) -> None:
        self.window._set_mode(CalendarViewMode.WEEK)
        index = self.window.font_combo.findData(150)
        self.window.font_combo.setCurrentIndex(index)
        self.window.close()
        self.app.processEvents()
        reopened = CalendarWindow(open_calendar_service(self.workspace / "planer.sqlite3"), repo_root=ROOT, workspace=self.workspace, timezone_name="Europe/Berlin")
        try:
            self.assertEqual(reopened.view_model.mode, CalendarViewMode.WEEK)
            self.assertEqual(reopened.view_model.font_scale_percent, 150)
        finally:
            reopened.close()


if __name__ == "__main__":
    unittest.main()
