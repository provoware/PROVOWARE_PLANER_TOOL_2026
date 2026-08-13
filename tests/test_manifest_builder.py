import json
import unittest
from pathlib import Path

from tools.autopilot.manifest_builder import build, check


class ManifestBuilderTests(unittest.TestCase):
    def test_build_and_check(self):
        build()
        self.assertEqual(check(), [])

    def test_inventory_has_unique_paths(self):
        build()
        data = json.loads(Path("SHA256_DATEI_INVENTAR.json").read_text(encoding="utf-8"))
        paths = [item["path"] for item in data["entries"]]
        self.assertEqual(len(paths), len(set(paths)))


if __name__ == "__main__":
    unittest.main()
