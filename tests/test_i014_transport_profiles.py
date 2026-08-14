from __future__ import annotations

import unittest
from pathlib import Path

from tools.transport_profiles import (
    ROOT,
    classify_path,
    load_contract,
    never_transport,
    profile_report,
    select_profile,
    validate_contract,
)


class I014TransportProfileTests(unittest.TestCase):
    def test_all_registered_paths_have_exactly_one_class(self) -> None:
        result = validate_contract(ROOT)
        self.assertEqual(result["status"], "PASS", result["errors"])
        self.assertEqual(result["repository_paths"], result["classified_paths"])
        self.assertTrue(all(value > 0 for value in result["class_counts"].values()))

    def test_default_profile_is_user_package(self) -> None:
        contract = load_contract(ROOT)
        self.assertEqual(contract["default_profile"], "NUTZER")
        self.assertTrue(contract["safety"]["user_profile_is_default"])

    def test_user_profile_contains_runtime_but_no_developer_or_evidence_files(self) -> None:
        selected = set(select_profile("NUTZER", ROOT))
        for required in (
            "VERSION.json",
            "requirements-gui.lock",
            "contracts/GUI_RUNTIME_CONTRACT.json",
            "tools/start_gui.py",
            "tools/start_orchestrator.py",
            "NUTZERANLEITUNG.md",
            "storage/database.py",
            "ui/calendar_window.py",
        ):
            self.assertIn(required, selected)
        for forbidden in (
            "README.md",
            "TODO.md",
            "PROJECT_CONTRACT.json",
            "QUALIFICATION_REPORT.json",
            "REMOTE_TREE_RECEIPT.json",
            "ITERATION_PLAN.json",
            "standards/TEST_STANDARD.json",
            "tests/test_standard_validator.py",
            "tools/autopilot/autopilot.py",
            ".github/workflows/foundation-qualifikation.yml",
            "docs/I013_ENTWICKLUNGSAUTOPILOT_V2.md",
        ):
            self.assertNotIn(forbidden, selected)

    def test_developer_and_evidence_profiles_are_separate(self) -> None:
        developer = set(select_profile("ENTWICKLER", ROOT))
        evidence = set(select_profile("EVIDENCE", ROOT))
        self.assertIn("tests/test_standard_validator.py", developer)
        self.assertIn("standards/ENTWICKLUNGS_STANDARD.json", developer)
        self.assertNotIn("QUALIFICATION_REPORT.json", developer)
        self.assertIn("QUALIFICATION_REPORT.json", evidence)
        self.assertIn("REMOTE_TREE_RECEIPT.json", evidence)
        self.assertIn("VERSION.json", evidence)
        self.assertIn("PROJEKTSTATUS.json", evidence)
        self.assertNotIn("calendar_core/model.py", evidence)
        self.assertNotIn("tests/test_standard_validator.py", evidence)

    def test_runtime_overrides_are_not_ambiguous(self) -> None:
        contract = load_contract(ROOT)
        self.assertEqual(classify_path("contracts/GUI_RUNTIME_CONTRACT.json", contract), "PRODUKTKERN")
        self.assertEqual(classify_path("tools/start_gui.py", contract), "PRODUKTKERN")
        self.assertEqual(classify_path("tools/autopilot/autopilot.py", contract), "ENTWICKLUNG")

    def test_user_data_and_backups_are_never_transportable(self) -> None:
        contract = load_contract(ROOT)
        for path in (
            "planer.sqlite3",
            "backups/planer-2026.sqlite3",
            "Sicherungen/stand.sqlite3.json",
            "workspace/LETZTER_STARTBERICHT.json",
            "planer.sqlite3.pre-restore",
            "debug.log",
        ):
            self.assertTrue(never_transport(path, contract), path)

    def test_profile_report_has_no_unplanned_classification_gap(self) -> None:
        report = profile_report(ROOT)
        self.assertEqual(report["status"], "PASS", report["errors"])
        self.assertGreater(report["profile_counts"]["NUTZER"], 20)
        self.assertGreater(report["profile_counts"]["ENTWICKLER"], report["profile_counts"]["NUTZER"])
        self.assertLess(report["profile_counts"]["EVIDENCE"], report["profile_counts"]["NUTZER"])


if __name__ == "__main__":
    unittest.main()
