from __future__ import annotations

import json
from pathlib import Path

from runtime.checks import CHECKS
from runtime.faults import FAULTS
from runtime.model import Phase, RuntimeState

ROOT = Path(__file__).resolve().parents[2]
REQUIRED_FILES = {
    "runtime/__init__.py",
    "runtime/model.py",
    "runtime/faults.py",
    "runtime/checks.py",
    "runtime/orchestrator.py",
    "tools/start_orchestrator.py",
    "tests/test_i003_state_machine.py",
    "docs/I003_KLICK_START_ORCHESTRATOR.md",
}
REQUIRED_FAULTS = {
    "workspace_missing",
    "config_corrupt",
    "manifest_tampered",
    "missing_permissions",
    "sqlite_locked",
    "sqlite_corrupt",
    "disk_full",
}
REQUIRED_STEPS = [
    "system",
    "runtime",
    "manifest",
    "workspace",
    "configuration",
    "database",
    "recovery",
    "modules",
    "logging",
    "event_bus",
    "gui",
    "post_start",
]
REQUIRED_ERROR_CODES = {
    "START-SYS-001",
    "START-RUNTIME-001",
    "START-MANIFEST-001",
    "START-WORKSPACE-PERM-001",
    "START-WORKSPACE-DISK-001",
    "START-CONFIG-001",
    "START-DB-LOCK-001",
    "START-DB-CORRUPT-001",
    "START-MODULE-001",
    "START-LOG-001",
    "START-EVENT-001",
    "START-GUI-001",
    "START-POST-001",
    "START-FAULT-SAFETY-001",
}


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def validate() -> dict:
    errors: list[str] = []
    files = {str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts}
    for path in sorted(REQUIRED_FILES - files):
        errors.append(f"I003_DATEI_FEHLT: {path}")

    version = load("VERSION.json")
    contract = load("PROJECT_CONTRACT.json")
    status = load("PROJEKTSTATUS.json")
    start_standard = load("standards/START_STANDARD.json")
    catalog = load("errors/FEHLERKATALOG.json")

    if version.get("iteration") != "I003" or version.get("version") != "0.3.0-dev.1":
        errors.append("I003_VERSION_NICHT_PROMOVIERT")
    if contract.get("foundation", {}).get("current_iteration") != "I003":
        errors.append("I003_VERTRAG_NICHT_PROMOVIERT")
    if status.get("iteration") != "I003":
        errors.append("I003_STATUS_NICHT_PROMOVIERT")

    development = contract.get("development", {})
    for field in ("deterministic_start_state_machine_required", "fault_injection_required", "safe_recovery_required"):
        if development.get(field) is not True:
            errors.append(f"I003_VERTRAG_FELD_FEHLT: {field}")

    if start_standard.get("state_machine") != [state.value for state in RuntimeState]:
        errors.append("I003_STARTSTANDARD_ZUSTAENDE_FALSCH")
    if start_standard.get("step_sequence") != [phase.value for phase in Phase]:
        errors.append("I003_STARTSTANDARD_PHASEN_FALSCH")

    step_ids = [check.__name__.removesuffix("_check") for check in CHECKS]
    aliases = {"config": "configuration", "event_bus": "event_bus", "post_start": "post_start"}
    step_ids = [aliases.get(item, item) for item in step_ids]
    if step_ids != REQUIRED_STEPS:
        errors.append(f"I003_SCHRITTREIHENFOLGE_FALSCH: {step_ids}")
    if not REQUIRED_FAULTS.issubset(FAULTS):
        errors.append("I003_FAULT_MATRIX_UNVOLLSTAENDIG")

    codes = {item.get("code") for item in catalog.get("errors", [])}
    for code in sorted(REQUIRED_ERROR_CODES - codes):
        errors.append(f"I003_FEHLERCODE_FEHLT: {code}")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "repository_files": len(files),
        "runtime_steps": len(REQUIRED_STEPS),
        "fault_scenarios": len(REQUIRED_FAULTS),
    }


def main() -> int:
    result = validate()
    print(f"I003-VALIDATOR: {result['status']}")
    print(f"Runtime-Schritte: {result['runtime_steps']}")
    print(f"Pflicht-Faults: {result['fault_scenarios']}")
    for error in result["errors"]:
        print(f"FEHLER: {error}")
    print("MASCHINENLESBAR:", json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
