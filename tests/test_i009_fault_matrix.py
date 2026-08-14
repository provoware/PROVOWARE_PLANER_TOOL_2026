from __future__ import annotations

import unittest

from tools.i009_fault_matrix import run_matrix


class I009FaultMatrixTest(unittest.TestCase):
    def test_all_sync_faults_and_process_crash_roll_back_atomically(self) -> None:
        result = run_matrix()
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(len(result["scenarios"]), 5)
        self.assertTrue(all(item["pass"] for item in result["scenarios"]), result)


if __name__ == "__main__":
    unittest.main()
