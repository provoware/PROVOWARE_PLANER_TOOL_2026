from __future__ import annotations

import unittest

from tools.autopilot.candidate_inventory import compute_expected_paths


class I013CandidateInventoryTest(unittest.TestCase):
    def test_expected_paths_are_baseline_plus_declared_delta(self) -> None:
        base = {"a.txt", "b.txt", "c.txt"}
        expected, errors, _warnings = compute_expected_paths(
            base,
            {"add": ["d.txt"], "modify": ["b.txt"], "delete": ["c.txt"]},
        )
        self.assertEqual(errors, [])
        self.assertEqual(expected, {"a.txt", "b.txt", "d.txt"})

    def test_add_existing_file_is_rejected(self) -> None:
        _expected, errors, _warnings = compute_expected_paths(
            {"a.txt"},
            {"add": ["a.txt"], "modify": [], "delete": []},
        )
        self.assertTrue(any("DELTA-002" in error for error in errors))

    def test_modify_missing_baseline_file_is_rejected(self) -> None:
        _expected, errors, _warnings = compute_expected_paths(
            {"a.txt"},
            {"add": [], "modify": ["x.txt"], "delete": []},
        )
        self.assertTrue(any("DELTA-003" in error for error in errors))

    def test_delta_categories_must_be_disjoint(self) -> None:
        _expected, errors, _warnings = compute_expected_paths(
            {"a.txt"},
            {"add": ["x.txt"], "modify": ["x.txt"], "delete": []},
        )
        self.assertTrue(any("DELTA-001" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
