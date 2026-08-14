from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from services.factory import open_planner_services

ROOT = Path(__file__).resolve().parents[1]


class I008ContractGuardTest(unittest.TestCase):
    def test_contract_is_read_only_and_both_changed_is_blocked(self) -> None:
        data = json.loads((ROOT / "contracts/SYNC_CONFLICT_CONTRACT.json").read_text(encoding="utf-8"))
        self.assertEqual(data["mode"], "READ_ONLY_PREVIEW")
        self.assertTrue(data["architecture"]["preview_must_not_write"])
        self.assertFalse(data["architecture"]["write_api_present_in_i008"])
        self.assertFalse(data["architecture"]["automatic_sync_in_i008"])
        self.assertTrue(data["safety"]["both_changed_hard_block"])
        self.assertTrue(data["safety"]["baseline_divergence_hard_block"])

    def test_preview_service_exposes_no_apply_or_synchronize_method(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provoware-i008-guard-") as temp:
            services = open_planner_services(Path(temp) / "planer.sqlite3")
            self.assertFalse(hasattr(services.sync_preview, "apply"))
            self.assertFalse(hasattr(services.sync_preview, "synchronize"))
            self.assertFalse(hasattr(services.sync_preview, "execute"))
            self.assertEqual(services.database.schema_version(), 2)


if __name__ == "__main__":
    unittest.main()
