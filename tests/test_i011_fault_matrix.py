from __future__ import annotations

import unittest

from tools.i011_history_fault_matrix import run_matrix


class I011HistoryFaultMatrixTest(unittest.TestCase):
    def test_snapshot_exception_and_process_crash_roll_back_atomically(self) -> None:
        result = run_matrix()
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(len(result["scenarios"]), 2)
        self.assertTrue(all(item["pass"] for item in result["scenarios"]))


if __name__ == "__main__":
    unittest.main()
