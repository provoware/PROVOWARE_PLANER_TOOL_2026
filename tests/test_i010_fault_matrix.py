from __future__ import annotations

import unittest

from tools.i010_resolution_fault_matrix import run_matrix


class I010FaultMatrixTest(unittest.TestCase):
    def test_resolution_faults_and_process_crash_roll_back_atomically(self) -> None:
        result = run_matrix()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(len(result["scenarios"]), 5)
        self.assertTrue(all(item["pass"] for item in result["scenarios"]))


if __name__ == "__main__":
    unittest.main()
