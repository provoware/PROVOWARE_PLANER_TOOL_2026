from __future__ import annotations

import unittest

from tools.i006_fault_matrix import run_matrix


class I006FaultMatrixTest(unittest.TestCase):
    def test_all_transaction_and_crash_scenarios_pass(self) -> None:
        result = run_matrix()
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(len(result["scenarios"]), 4)
        self.assertTrue(all(item["pass"] for item in result["scenarios"]))


if __name__ == "__main__":
    unittest.main()
