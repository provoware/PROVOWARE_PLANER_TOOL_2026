from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.start_gui import ROOT, _check_native_gui_runtime


class I005GuiRuntimeTest(unittest.TestCase):
    def test_runtime_contract_is_machine_readable(self) -> None:
        data = json.loads((Path(ROOT) / "contracts" / "GUI_RUNTIME_CONTRACT.json").read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "VERBINDLICH")
        self.assertEqual(data["python"]["version"], "6.9.1")
        self.assertIn("libEGL.so.1", data["native_shared_libraries"])
        self.assertTrue(data["startup"]["orchestrator_before_qt_import"])
        self.assertTrue(data["startup"]["raw_import_crash_forbidden"])

    def test_missing_native_library_is_caught_before_raw_qt_crash(self) -> None:
        with patch("tools.start_gui.ctypes.CDLL", side_effect=OSError("simuliert fehlend")):
            ok, detail = _check_native_gui_runtime()
        self.assertFalse(ok)
        self.assertIn("Fehlende Linux-Bibliotheken", detail)


if __name__ == "__main__":
    unittest.main()
