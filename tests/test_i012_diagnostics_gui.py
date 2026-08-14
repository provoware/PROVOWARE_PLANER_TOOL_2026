from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from services.diagnostics_service import DiagnosticsService
from services.factory import open_planner_services
from ui.diagnostics_window import DiagnosticsWindow


class I012DiagnosticsGuiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])
        cls.repo_root = Path(__file__).resolve().parents[1]

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="provoware-i012-gui-")
        workspace = Path(self.temp.name)
        services = open_planner_services(workspace / "planer.sqlite3")
        self.window = DiagnosticsWindow(
            DiagnosticsService(services.database, services.journal, workspace=workspace),
            repo_root=self.repo_root,
        )
        self.window.show()
        self.app.processEvents()

    def tearDown(self) -> None:
        self.window.close()
        self.temp.cleanup()

    def test_required_rows_are_visible(self) -> None:
        self.assertEqual(self.window.table.rowCount(), 5)
        names = {self.window.table.item(row, 0).text() for row in range(5)}
        self.assertEqual(
            names,
            {"Startzustand", "Datenbank", "Synchronisationsjournal", "Sicherungen", "Recovery-Pläne"},
        )

    def test_controls_have_accessible_names(self) -> None:
        self.assertTrue(self.window.refresh_button.accessibleName())
        self.assertTrue(self.window.table.accessibleName())
        self.assertTrue(self.window.overall_label.accessibleName())

    def test_dashboard_has_no_execution_control(self) -> None:
        texts = {button.text() for button in self.window.findChildren(type(self.window.refresh_button))}
        self.assertEqual(texts, {"Erneut prüfen"})
        self.assertNotIn("Restore", " ".join(texts))
        self.assertNotIn("ausführen", " ".join(texts).lower())

    def test_status_is_symbol_plus_text(self) -> None:
        state_texts = [self.window.table.item(row, 1).text() for row in range(self.window.table.rowCount())]
        self.assertTrue(all(text.startswith(("● ", "▲ ")) for text in state_texts))


if __name__ == "__main__":
    unittest.main()
