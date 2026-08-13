from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = {
    "SOURCE_MANIFEST.json",
    "BUILD_MANIFEST.json",
    "RELEASE_MANIFEST.json",
    "EVIDENCE_MANIFEST.json",
    "MANIFEST_INDEX.json",
    "SHA256_DATEI_INVENTAR.json",
    "REMOTE_TREE_RECEIPT.json",
    "QUALIFICATION_REPORT.json",
    "errors/FEHLERKATALOG.json",
    "standards/ERROR_HANDLING_STANDARD.json",
}


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def actual_files() -> set[str]:
    return {
        str(path.relative_to(ROOT))
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and "__pycache__" not in path.parts
        and ".pytest_cache" not in path.parts
    }


def validate() -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    files = actual_files()
    for path in sorted(REQUIRED - files):
        errors.append(f"I002_DATEI_FEHLT: {path}")

    inventory = load("SHA256_DATEI_INVENTAR.json")
    if inventory.get("state") == "PENDING_GENERATION":
        errors.append("I002_INVENTAR_NICHT_ERZEUGT")
    else:
        bound = {item["path"] for item in inventory.get("entries", [])}
        excluded = set(inventory.get("excluded", []))
        if bound | excluded != files:
            errors.append("I002_DATEIMENGE_WIDERSPRUCH")

    index = load("standards/STANDARD_INDEX.json")
    if not any(item.get("id") == "PROVOWARE-ERROR-HANDLING" for item in index.get("standards", [])):
        errors.append("I002_FEHLERSTANDARD_NICHT_REGISTRIERT")

    error_standard = load("standards/ERROR_HANDLING_STANDARD.json")
    if error_standard.get("status") != "VERBINDLICH":
        errors.append("I002_FEHLERSTANDARD_NICHT_VERBINDLICH")

    catalog = load("errors/FEHLERKATALOG.json")
    codes = [item.get("code") for item in catalog.get("errors", [])]
    if len(codes) != len(set(codes)):
        errors.append("I002_FEHLERCODE_DOPPELT")
    for item in catalog.get("errors", []):
        for field in ("code", "severity", "title", "effect", "user_action", "blocking"):
            if field not in item:
                errors.append(f"I002_FEHLERKATALOG_FELD_FEHLT: {field}")

    version = load("VERSION.json")
    if version.get("iteration") != "I002":
        warnings.append("METADATEN_PROMOTION_AUSSTEHEND: VERSION.json")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "actual_files": len(files),
        "sha256_bound_files": inventory.get("count", 0),
    }


def main() -> int:
    result = validate()
    print(f"I002-VALIDATOR: {result['status']}")
    print(f"Repository-Dateien: {result['actual_files']}")
    print(f"SHA-256-gebunden: {result['sha256_bound_files']}")
    for warning in result["warnings"]:
        print(f"WARNUNG: {warning}")
    for error in result["errors"]:
        print(f"FEHLER: {error}")
    print("MASCHINENLESBAR:", json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
