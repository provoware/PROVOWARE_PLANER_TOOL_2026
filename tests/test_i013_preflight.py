from __future__ import annotations

import unittest

from tools.autopilot.preflight import validate


class I013PreflightTest(unittest.TestCase):
    def test_current_repository_passes_static_preflight(self) -> None:
        result = validate()
        self.assertEqual(result["status"], "PASS", result["errors"])
        self.assertEqual(result["stage"], "P0_STATIC")
        self.assertEqual(result["candidate_inventory_status"], "PASS")

    def test_static_preflight_checks_real_files(self) -> None:
        result = validate()
        self.assertGreater(result["json_files_checked"], 10)
        self.assertGreater(result["python_files_compiled"], 10)
        self.assertGreater(result["standards_checked"], 10)


if __name__ == "__main__":
    unittest.main()
