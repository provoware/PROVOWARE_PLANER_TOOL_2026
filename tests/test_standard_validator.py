import json
import tempfile
import unittest
from pathlib import Path

from tools.autopilot.standard_validator import validate_repository


class StandardValidatorTests(unittest.TestCase):
    def test_current_repository_is_valid(self):
        root = Path(__file__).resolve().parents[1]
        result = validate_repository(root)
        self.assertTrue(result["ok"], result["errors"])

    def test_missing_manifest_file_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "REPOSITORY_MANIFEST.json").write_text(
                json.dumps({"files": ["REPOSITORY_MANIFEST.json", "FEHLT.txt"], "expected_file_count": 2}),
                encoding="utf-8",
            )
            result = validate_repository(root, foundation_checks=False)
            self.assertFalse(result["ok"])
            self.assertTrue(any("FEHLT.txt" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
