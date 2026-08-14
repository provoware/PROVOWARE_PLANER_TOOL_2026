from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "package_transport.py"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(profile: str, output: Path) -> Path:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--profile", profile, "--output-dir", str(output)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise AssertionError(f"Paketbau fehlgeschlagen: {result.stdout}\n{result.stderr}")
    matches = sorted(output.glob(f"PROVOWARE_PLANER_{profile}_*.zip"))
    if len(matches) != 1:
        raise AssertionError(f"Unerwartete Paketanzahl: {matches}")
    return matches[0]


class I014RuntimePackageTests(unittest.TestCase):
    def test_user_package_is_deterministic_and_self_validating(self) -> None:
        with tempfile.TemporaryDirectory(prefix="i014-package-") as temp:
            base = Path(temp)
            first = build("NUTZER", base / "a")
            second = build("NUTZER", base / "b")
            self.assertEqual(digest(first), digest(second))

            with zipfile.ZipFile(first) as handle:
                names = set(handle.namelist())
                self.assertIn("PAKETMANIFEST.json", names)
                self.assertIn("PAKET_INVENTAR.json", names)
                self.assertIn("SHA256_DATEI_INVENTAR.json", names)
                self.assertIn("NUTZERANLEITUNG.md", names)
                self.assertIn("tools/start_gui.py", names)
                self.assertNotIn("README.md", names)
                self.assertNotIn("QUALIFICATION_REPORT.json", names)
                self.assertFalse(any(name.startswith("tests/") for name in names))
                self.assertFalse(any(name.startswith("docs/") for name in names))
                self.assertFalse(any(name.startswith(".github/") for name in names))
                manifest = json.loads(handle.read("PAKETMANIFEST.json").decode("utf-8"))
                self.assertEqual(manifest["profile"], "NUTZER")
                self.assertFalse(manifest["user_data_included"])
                self.assertFalse(manifest["backup_data_included"])

            check = subprocess.run(
                [sys.executable, str(SCRIPT), "--validate", str(first)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

    def test_developer_package_excludes_evidence(self) -> None:
        with tempfile.TemporaryDirectory(prefix="i014-dev-") as temp:
            archive = build("ENTWICKLER", Path(temp))
            with zipfile.ZipFile(archive) as handle:
                names = set(handle.namelist())
                self.assertIn("tests/test_standard_validator.py", names)
                self.assertIn("standards/ENTWICKLUNGS_STANDARD.json", names)
                self.assertIn("tools/autopilot/autopilot.py", names)
                self.assertNotIn("QUALIFICATION_REPORT.json", names)
                self.assertNotIn("REMOTE_TREE_RECEIPT.json", names)

    def test_evidence_package_has_context_but_no_product_tree(self) -> None:
        with tempfile.TemporaryDirectory(prefix="i014-evidence-") as temp:
            archive = build("EVIDENCE", Path(temp))
            with zipfile.ZipFile(archive) as handle:
                names = set(handle.namelist())
                self.assertIn("VERSION.json", names)
                self.assertIn("PROJEKTSTATUS.json", names)
                self.assertIn("QUALIFICATION_REPORT.json", names)
                self.assertIn("REMOTE_TREE_RECEIPT.json", names)
                self.assertNotIn("calendar_core/model.py", names)
                self.assertNotIn("ui/calendar_window.py", names)
                self.assertNotIn("tests/test_standard_validator.py", names)


if __name__ == "__main__":
    unittest.main()
