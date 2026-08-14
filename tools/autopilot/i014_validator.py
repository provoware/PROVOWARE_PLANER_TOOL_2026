from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.transport_profiles import load_contract, select_profile, validate_contract

REQUIRED_FILES = {
    ".gitignore",
    "NUTZERANLEITUNG.md",
    "contracts/TRANSPORT_PROFILE_CONTRACT.json",
    "standards/TRANSPORT_STANDARD.json",
    "tools/transport_profiles.py",
    "tools/package_transport.py",
    "tests/test_i014_transport_profiles.py",
    "tests/test_i014_runtime_package.py",
    "docs/I014_TRANSPORTPROFILE_TRENNUNG.md",
    ".github/workflows/i014-qualifikation.yml",
}


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _iteration(value: object) -> int:
    try:
        return int(str(value).removeprefix("I"))
    except ValueError:
        return 0


def validate() -> dict:
    errors: list[str] = []
    files = {
        str(path.relative_to(ROOT))
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and "__pycache__" not in path.parts
        and ".pytest_cache" not in path.parts
        and "dist_transport" not in path.parts
    }
    for path in sorted(REQUIRED_FILES - files):
        errors.append(f"I014_DATEI_FEHLT: {path}")

    version = load("VERSION.json")
    status = load("PROJEKTSTATUS.json")
    project = load("PROJECT_CONTRACT.json")
    plan = load("ITERATION_PLAN.json")
    standard = load("standards/TRANSPORT_STANDARD.json")
    contract = load_contract(ROOT)

    current = _iteration(version.get("iteration"))
    if current < 14:
        errors.append("I014_VERSION_UNTER_MINDESTSTAND")
    if current == 14 and version.get("version") != "0.14.0-dev.1":
        errors.append("I014_VERSION_FALSCH")
    if _iteration(status.get("iteration")) < 14:
        errors.append("I014_STATUS_UNTER_MINDESTSTAND")
    if _iteration(project.get("foundation", {}).get("current_iteration")) < 14:
        errors.append("I014_PROJEKTVERTRAG_UNTER_MINDESTSTAND")

    if standard.get("standard_id") != "PROVOWARE-TRANSPORT" or standard.get("version") != "1.0.0":
        errors.append("I014_TRANSPORTSTANDARD_FALSCH")
    if contract.get("status") != "VERBINDLICH" or contract.get("default_profile") != "NUTZER":
        errors.append("I014_TRANSPORTVERTRAG_FALSCH")

    profile_validation = validate_contract(ROOT)
    if profile_validation.get("status") != "PASS":
        errors.extend(f"I014_KLASSIFIKATION: {item}" for item in profile_validation.get("errors", []))

    try:
        user = set(select_profile("NUTZER", ROOT))
        developer = set(select_profile("ENTWICKLER", ROOT))
        evidence = set(select_profile("EVIDENCE", ROOT))
    except Exception as exc:
        errors.append(f"I014_PROFILAUSWAHL_FEHLER: {type(exc).__name__}: {exc}")
        user = developer = evidence = set()

    for required in (
        "VERSION.json",
        "requirements-gui.lock",
        "contracts/GUI_RUNTIME_CONTRACT.json",
        "tools/start_gui.py",
        "NUTZERANLEITUNG.md",
    ):
        if required not in user:
            errors.append(f"I014_NUTZER_RUNTIME_FEHLT: {required}")

    forbidden_user_prefixes = (".github/", "docs/", "standards/", "tests/", "tools/autopilot/")
    for path in sorted(user):
        if path.startswith(forbidden_user_prefixes):
            errors.append(f"I014_ENTWICKLERDATEI_IM_NUTZERPAKET: {path}")
    for forbidden in ("QUALIFICATION_REPORT.json", "REMOTE_TREE_RECEIPT.json", "PROJECT_CONTRACT.json", "ITERATION_PLAN.json"):
        if forbidden in user:
            errors.append(f"I014_NACHWEIS_IM_NUTZERPAKET: {forbidden}")

    if "tests/test_standard_validator.py" not in developer or "tools/autopilot/autopilot.py" not in developer:
        errors.append("I014_ENTWICKLERPROFIL_UNVOLLSTAENDIG")
    if "QUALIFICATION_REPORT.json" in developer or "REMOTE_TREE_RECEIPT.json" in developer:
        errors.append("I014_EVIDENCE_IM_ENTWICKLERPAKET")
    if "QUALIFICATION_REPORT.json" not in evidence or "calendar_core/model.py" in evidence:
        errors.append("I014_EVIDENCEPROFIL_FALSCH")

    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8") if (ROOT / ".gitignore").exists() else ""
    for token in ("*.sqlite3", "backups/", "Sicherungen/", "*.pre-restore", "dist_transport/"):
        if token not in ignore:
            errors.append(f"I014_GITIGNORE_SCHUTZ_FEHLT: {token}")

    builder = (ROOT / "tools/package_transport.py").read_text(encoding="utf-8") if (ROOT / "tools/package_transport.py").exists() else ""
    for token in ("FIXED_ZIP_TIME", "PAKETMANIFEST.json", "PAKET_INVENTAR.json", "runtime_compatibility_inventory", "select_profile", "validate_archive"):
        if token not in builder:
            errors.append(f"I014_PAKETBUILDER_HAERTUNG_FEHLT: {token}")

    guide = (ROOT / "NUTZERANLEITUNG.md").read_text(encoding="utf-8") if (ROOT / "NUTZERANLEITUNG.md").exists() else ""
    for token in ("Arbeitsbereich", "Sicherungen", "NUTZER", "PAKET_INVENTAR.json"):
        if token not in guide:
            errors.append(f"I014_NUTZERANLEITUNG_FEHLT: {token}")

    if plan.get("base", {}).get("commit") != "3ba56de67f3ae6bdedf4e52e8cd61d33562bd280":
        errors.append("I014_BASELINE_FALSCH")
    if plan.get("risk_class") != "HOCH":
        errors.append("I014_RISIKOKLASSE_FALSCH")
    criteria = {item.get("id") for item in plan.get("acceptance_criteria", [])}
    if criteria != {f"I014-A{number:02d}" for number in range(1, 11)}:
        errors.append("I014_AKZEPTANZKRITERIEN_UNVOLLSTAENDIG")

    workflow_path = ROOT / ".github/workflows/i014-qualifikation.yml"
    workflow = workflow_path.read_text(encoding="utf-8") if workflow_path.exists() else ""
    for token in (
        "preflight.py",
        "candidate_inventory.py --write-manifest",
        "test_i014_transport_profiles.py",
        "test_i014_runtime_package.py",
        "package_transport.py --profile NUTZER",
        "--offscreen-smoke",
        "verify_only",
        "verify_sha",
    ):
        if token not in workflow:
            errors.append(f"I014_WORKFLOW_GATE_FEHLT: {token}")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "repository_files": len(files),
        "classified_paths": profile_validation.get("classified_paths", 0),
        "user_files": len(user),
        "developer_files": len(developer),
        "evidence_files": len(evidence),
        "acceptance_criteria": len(criteria),
        "runtime_schema_unchanged": 4,
    }


def main() -> int:
    result = validate()
    print(f"I014-VALIDATOR: {result['status']}")
    print(
        f"Profile: Nutzer={result['user_files']} Entwickler={result['developer_files']} "
        f"Evidence={result['evidence_files']} | klassifiziert={result['classified_paths']}"
    )
    for error in result["errors"]:
        print(f"FEHLER: {error}")
    print("MASCHINENLESBAR:", json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
