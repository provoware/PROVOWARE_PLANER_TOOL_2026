from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = {
    "backup_core/execution.py",
    "storage/restore_guard.py",
    "services/restore_execution_service.py",
    "runtime/restore_recovery.py",
    "contracts/RESTORE_EXECUTION_SAFETY_CONTRACT.json",
    "standards/RESTORE_EXECUTION_STANDARD.json",
    "errors/RESTORE_EXECUTION_FEHLERKATALOG.json",
    "tests/test_i016_restore_execution.py",
    "tests/test_i016_restore_crash_recovery.py",
    "tools/i016_restore_crash_matrix.py",
    "docs/I016_RESTORE_EXECUTION_SAFETY.md",
    ".github/workflows/i016-qualifikation.yml",
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
        if path.is_file() and ".git" not in path.parts and "__pycache__" not in path.parts
        and ".pytest_cache" not in path.parts and "dist_transport" not in path.parts
    }
    for path in sorted(REQUIRED_FILES - files):
        errors.append(f"I016_DATEI_FEHLT: {path}")

    version = load("VERSION.json")
    status = load("PROJEKTSTATUS.json")
    project = load("PROJECT_CONTRACT.json")
    contract = load("contracts/RESTORE_EXECUTION_SAFETY_CONTRACT.json")
    standard = load("standards/RESTORE_EXECUTION_STANDARD.json")
    transport = load("contracts/TRANSPORT_PROFILE_CONTRACT.json")
    plan = load("ITERATION_PLAN.json")
    current = _iteration(version.get("iteration"))

    if current < 16:
        errors.append("I016_VERSION_UNTER_MINDESTSTAND")
    if current == 16 and version.get("version") != "0.16.0-dev.1":
        errors.append("I016_VERSION_FALSCH")
    if _iteration(status.get("iteration")) < 16:
        errors.append("I016_STATUS_UNTER_MINDESTSTAND")
    if _iteration(project.get("foundation", {}).get("current_iteration")) < 16:
        errors.append("I016_PROJEKTVERTRAG_UNTER_MINDESTSTAND")

    if contract.get("contract_id") != "PROVOWARE-RESTORE-EXECUTION-SAFETY":
        errors.append("I016_VERTRAG_FALSCH")
    if contract.get("physical_restore_core") != "storage.backup.restore_backup":
        errors.append("I016_PHYSISCHER_RESTOREKERN_FALSCH")
    if contract.get("physical_restore_core_must_remain_unchanged_in_i016") is not True:
        errors.append("I016_RESTOREKERN_UNVERAENDERT_REGEL_FEHLT")
    if contract.get("execution_states") != ["PREPARED", "COMMITTING", "VERIFIED", "CLOSED"]:
        errors.append("I016_INTENT_ZUSTAENDE_FALSCH")
    if standard.get("standard_id") != "PROVOWARE-RESTORE-EXECUTION" or standard.get("version") != "1.0.0":
        errors.append("I016_STANDARD_FALSCH")

    delta = plan.get("repository_delta", {})
    if "storage/backup.py" in set(delta.get("modify", [])):
        errors.append("I016_PHYSISCHER_RESTOREKERN_DARF_NICHT_GEAENDERT_WERDEN")
    if plan.get("base", {}).get("commit") != "ce66b61444c6014ce543226e4525d5ffc2353b73":
        errors.append("I016_BASELINE_FALSCH")
    if plan.get("safety_critical") is not True or plan.get("risk_class") != "HOCH":
        errors.append("I016_RISIKOKLASSE_FALSCH")

    execution = (ROOT / "services/restore_execution_service.py").read_text(encoding="utf-8")
    for token in (
        "RestoreIntentState.COMMITTING",
        "acquire_restore_lease",
        "_prove_no_writer",
        "_create_sqlite_snapshot",
        "self.restore_service.commit_restore(plan)",
        "restore_backup(snapshot",
        "recover_pending",
        "logical_database_sha256",
    ):
        if token not in execution:
            errors.append(f"I016_EXECUTION_KERN_FEHLT: {token}")
    for forbidden in ("os.replace(candidate, target)", "shutil.copy2", "shutil.move"):
        if forbidden in execution:
            errors.append(f"I016_PARALLELER_ZIELAUSTAUSCH: {forbidden}")

    database = (ROOT / "storage/database.py").read_text(encoding="utf-8")
    if "assert_restore_write_allowed(self.path)" not in database:
        errors.append("I016_DATENBANK_LEASE_GUARD_FEHLT")
    start_gui = (ROOT / "tools/start_gui.py").read_text(encoding="utf-8")
    if start_gui.find("restore_recovery_preflight(workspace)") > start_gui.find("StartOrchestrator(ctx).run()"):
        errors.append("I016_START_RECOVERY_ZU_SPAET")

    never = transport.get("never_transport_globs", [])
    for token in ("**/.provoware_restore/**", "RESTORE_INTENT.json", "RESTORE_LEASE.json", "PRE_RESTORE_SNAPSHOT.sqlite3"):
        if token not in never:
            errors.append(f"I016_TRANSPORTSCHUTZ_FEHLT: {token}")

    if current == 16:
        criteria = {item.get("id") for item in plan.get("acceptance_criteria", [])}
        if criteria != {f"I016-A{n:02d}" for n in range(1, 13)}:
            errors.append("I016_AKZEPTANZKRITERIEN_UNVOLLSTAENDIG")

    workflow = (ROOT / ".github/workflows/i016-qualifikation.yml").read_text(encoding="utf-8") if (ROOT / ".github/workflows/i016-qualifikation.yml").exists() else ""
    for token in (
        "test_i016_restore_execution.py",
        "test_i016_restore_crash_recovery.py",
        "i016_restore_crash_matrix.py",
        "verify_only",
        "verify_sha",
        "package_transport.py --profile NUTZER",
    ):
        if token not in workflow:
            errors.append(f"I016_WORKFLOW_GATE_FEHLT: {token}")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "repository_files": len(files),
        "schema_version": 4,
        "physical_restore_core": contract.get("physical_restore_core"),
        "execution_states": contract.get("execution_states"),
        "safety_critical": plan.get("safety_critical"),
    }


def main() -> int:
    result = validate()
    print(f"I016-VALIDATOR: {result['status']}")
    print(f"Restorekern: {result['physical_restore_core']} | Schema: {result['schema_version']}")
    for error in result["errors"]:
        print(f"FEHLER: {error}")
    print("MASCHINENLESBAR:", json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
