from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from runtime.faults import RuntimeContext
from runtime.model import RuntimeState
from runtime.orchestrator import StartOrchestrator


ROOT = Path(__file__).resolve().parents[1]


class I003StateMachineTests(unittest.TestCase):
    def run_case(self, faults=()):
        with tempfile.TemporaryDirectory(prefix="provoware-i003-") as tmp:
            workspace = Path(tmp) / "workspace"
            ctx = RuntimeContext(
                repo_root=ROOT,
                workspace=workspace,
                faults=set(faults),
                allow_fault_injection=bool(faults),
            )
            report = StartOrchestrator(ctx).run()
            snapshot = report.to_dict()
            if report.state == RuntimeState.READY:
                self.assertTrue((workspace / ".runtime-ready.json").exists())
            return snapshot

    def test_happy_path_ready(self):
        report = self.run_case()
        self.assertEqual(report["state"], "READY")
        self.assertEqual(report["state_history"][0], "INIT")
        self.assertIn("CHECKING", report["state_history"])
        self.assertEqual(report["state_history"][-1], "READY")

    def test_phase_order(self):
        report = self.run_case()
        for step in report["steps"]:
            phases = [item["phase"] for item in step["phases"]]
            if len(phases) == 3:
                self.assertEqual(phases, ["PRECHECK", "ACTION", "POSTCHECK"])

    def test_workspace_missing_recovers(self):
        report = self.run_case(["workspace_missing"])
        self.assertEqual(report["state"], "READY")
        self.assertIn("RECOVERY_REQUIRED", report["state_history"])
        self.assertIn("workspace_created", report["recovery_actions"])

    def test_corrupt_config_is_quarantined_and_recovered(self):
        report = self.run_case(["config_corrupt"])
        self.assertEqual(report["state"], "READY")
        self.assertTrue(any(item.startswith("config_quarantined:") for item in report["recovery_actions"]))

    def test_manifest_tamper_blocks(self):
        self.assertEqual(self.run_case(["manifest_tampered"])["state"], "BLOCKED")

    def test_missing_permissions_blocks(self):
        self.assertEqual(self.run_case(["missing_permissions"])["state"], "BLOCKED")

    def test_disk_full_blocks_before_write(self):
        self.assertEqual(self.run_case(["disk_full"])["state"], "BLOCKED")

    def test_locked_database_requires_recovery(self):
        self.assertEqual(self.run_case(["sqlite_locked"])["state"], "RECOVERY_REQUIRED")

    def test_corrupt_database_requires_recovery(self):
        self.assertEqual(self.run_case(["sqlite_corrupt"])["state"], "RECOVERY_REQUIRED")

    def test_optional_module_can_degrade(self):
        self.assertEqual(self.run_case(["optional_module_missing"])["state"], "DEGRADED")

    def test_fault_injection_requires_explicit_permission(self):
        with tempfile.TemporaryDirectory(prefix="provoware-i003-") as tmp:
            ctx = RuntimeContext(ROOT, Path(tmp) / "workspace", {"disk_full"}, False)
            report = StartOrchestrator(ctx).run()
            self.assertEqual(report.state, RuntimeState.BLOCKED)
            self.assertEqual(report.steps[0].step_id, "fault_safety")


if __name__ == "__main__":
    unittest.main()
