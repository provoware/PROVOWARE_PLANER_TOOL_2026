from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.transport_profiles import load_contract, never_transport, select_profile

REQUIRED_FILES = {
    "backup_core/__init__.py",
    "backup_core/model.py",
    "services/restore_service.py",
    "contracts/BACKUP_RESTORE_PLAN_CONTRACT.json",
    "standards/BACKUP_RESTORE_STANDARD.json",
    "errors/BACKUP_RESTORE_FEHLERKATALOG.json",
    "tests/test_i015_restore_plan.py",
    "tests/test_i015_restore_faults.py",
    "tools/i015_restore_fault_matrix.py",
    "docs/I015_BACKUP_RESTOREPLAN.md",
    ".github/workflows/i015-qualifikation.yml",
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
        errors.append(f"I015_DATEI_FEHLT: {path}")

    version = load("VERSION.json")
    status = load("PROJEKTSTATUS.json")
    project = load("PROJECT_CONTRACT.json")
    standard = load("standards/BACKUP_RESTORE_STANDARD.json")
    contract = load("contracts/BACKUP_RESTORE_PLAN_CONTRACT.json")
    plan = load("ITERATION_PLAN.json")

    current = _iteration(version.get("iteration"))
    if current < 15:
        errors.append("I015_VERSION_UNTER_MINDESTSTAND")
    if current == 15 and version.get("version") != "0.15.0-dev.1":
        errors.append("I015_VERSION_FALSCH")
    if _iteration(status.get("iteration")) < 15:
        errors.append("I015_STATUS_UNTER_MINDESTSTAND")
    if _iteration(project.get("foundation", {}).get("current_iteration")) < 15:
        errors.append("I015_PROJEKTVERTRAG_UNTER_MINDESTSTAND")

    if standard.get("standard_id") != "PROVOWARE-BACKUP-RESTORE" or standard.get("version") != "1.0.0":
        errors.append("I015_BACKUP_STANDARD_FALSCH")
    if contract.get("physical_restore_core") != "storage.backup.restore_backup":
        errors.append("I015_PARALLELER_RESTOREPFAD")
    if contract.get("parallel_restore_path_forbidden") is not True:
        errors.append("I015_PARALLELVERBOT_FEHLT")
    if contract.get("candidate_qualification", {}).get("read_only") is not True:
        errors.append("I015_KANDIDAT_NICHT_READONLY")
    if contract.get("restore_plan", {}).get("immutable") is not True:
        errors.append("I015_PLAN_NICHT_IMMUTABLE")
    if contract.get("commit_protocol") != ["PRECHECK", "COMMIT", "POSTCHECK"]:
        errors.append("I015_COMMITPROTOKOLL_FALSCH")

    restore_source = (ROOT / "services/restore_service.py").read_text(encoding="utf-8") if (ROOT / "services/restore_service.py").exists() else ""
    for forbidden in ("os.replace(", "shutil.copy", "shutil.move", "Path.replace("):
        if forbidden in restore_source:
            errors.append(f"I015_PARALLELER_DATEIAUSTAUSCH: {forbidden}")
    for required in ("restore_backup(", "qualify_candidate", "prepare_restore", "commit_restore", "_database_state_sha256", "physical_core_precheck"):
        if required not in restore_source:
            errors.append(f"I015_RESTORESERVICE_FEHLT: {required}")

    storage_source = (ROOT / "storage/backup.py").read_text(encoding="utf-8") if (ROOT / "storage/backup.py").exists() else ""
    for required in ("def restore_backup(", "expected_sha256", "precheck", "postcheck", "rollback_copy", "os.replace(candidate, target)"):
        if required not in storage_source:
            errors.append(f"I015_PHYSISCHER_KERN_FEHLT: {required}")

    model_source = (ROOT / "backup_core/model.py").read_text(encoding="utf-8") if (ROOT / "backup_core/model.py").exists() else ""
    for required in ("@dataclass(frozen=True, slots=True)", "class RestorePlan", "plan_sha256", "verify_hash"):
        if required not in model_source:
            errors.append(f"I015_PLANMODELL_FEHLT: {required}")

    transport = load_contract(ROOT)
    user = set(select_profile("NUTZER", ROOT))
    for required in ("backup_core/model.py", "services/restore_service.py", "storage/backup.py"):
        if required not in user:
            errors.append(f"I015_RUNTIME_NICHT_IM_NUTZERPROFIL: {required}")
    for forbidden in ("backups/demo.sqlite3", "Sicherungen/demo.sqlite3", "planer.sqlite3.pre-restore", "planer.sqlite3.restore-candidate"):
        if not never_transport(forbidden, transport):
            errors.append(f"I015_TRANSPORTSCHUTZ_FEHLT: {forbidden}")

    if current == 15:
        if plan.get("base", {}).get("commit") != "1b684cc99d97cd2f00221b49a8ef606686d2453b":
            errors.append("I015_BASELINE_FALSCH")
        if plan.get("risk_class") != "KRITISCH":
            errors.append("I015_RISIKOKLASSE_FALSCH")
        criteria = {item.get("id") for item in plan.get("acceptance_criteria", [])}
        if criteria != {f"I015-A{number:02d}" for number in range(1, 12)}:
            errors.append("I015_AKZEPTANZKRITERIEN_UNVOLLSTAENDIG")
    else:
        criteria = set()

    workflow_path = ROOT / ".github/workflows/i015-qualifikation.yml"
    workflow = workflow_path.read_text(encoding="utf-8") if workflow_path.exists() else ""
    for token in (
        "preflight.py",
        "candidate_inventory.py --write-manifest",
        "test_i015_restore_plan.py",
        "test_i015_restore_faults.py",
        "i015_restore_fault_matrix.py",
        "package_transport.py --profile NUTZER",
        "verify_only",
        "verify_sha",
    ):
        if token not in workflow:
            errors.append(f"I015_WORKFLOW_GATE_FEHLT: {token}")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "repository_files": len(files),
        "schema_version": 4,
        "physical_restore_core": contract.get("physical_restore_core"),
        "acceptance_criteria": len(criteria) if current == 15 else 11,
    }


def main() -> int:
    result = validate()
    print(f"I015-VALIDATOR: {result['status']}")
    print(f"Restorekern: {result['physical_restore_core']} | Schema: {result['schema_version']}")
    for error in result["errors"]:
        print(f"FEHLER: {error}")
    print("MASCHINENLESBAR:", json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
