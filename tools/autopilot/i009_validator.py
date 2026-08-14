from __future__ import annotations

import json
import sys
import tempfile
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REQUIRED_FILES = {
    "contracts/SYNC_EXECUTION_CONTRACT.json",
    "errors/SYNC_EXECUTION_FEHLERKATALOG.json",
    "migrations/0003_sync_field_baseline.sql",
    "sync_core/canonical.py",
    "sync_core/fields.py",
    "sync_core/errors.py",
    "sync_core/faults.py",
    "storage/sync_repository.py",
    "services/sync_service.py",
    "tests/test_i009_three_way_sync.py",
    "tests/test_i009_plan_tamper.py",
    "tests/test_i009_fault_matrix.py",
    "tools/i009_fault_matrix.py",
    "docs/I009_FELD_BASELINE_TRANSAKTIONALER_SYNC.md",
    ".github/workflows/i009-qualifikation.yml",
}


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _iteration(value: object) -> int:
    try:
        return int(str(value).removeprefix("I"))
    except ValueError:
        return 0


def repository_files() -> set[str]:
    return {
        str(path.relative_to(ROOT))
        for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.parts and "__pycache__" not in path.parts and ".pytest_cache" not in path.parts
    }


def validate() -> dict:
    errors: list[str] = []
    files = repository_files()
    for path in sorted(REQUIRED_FILES - files):
        errors.append(f"I009_DATEI_FEHLT: {path}")

    version = load("VERSION.json")
    status = load("PROJEKTSTATUS.json")
    project = load("PROJECT_CONTRACT.json")
    contract = load("contracts/SYNC_EXECUTION_CONTRACT.json")
    current = _iteration(version.get("iteration"))
    if current < 9:
        errors.append("I009_VERSION_UNTER_MINDESTSTAND")
    if current == 9 and version.get("version") != "0.9.0-dev.1":
        errors.append("I009_VERSION_FALSCH")
    if _iteration(status.get("iteration")) < 9:
        errors.append("I009_STATUS_UNTER_MINDESTSTAND")
    if _iteration(project.get("foundation", {}).get("current_iteration")) < 9:
        errors.append("I009_PROJEKTVERTRAG_UNTER_MINDESTSTAND")
    if contract.get("status") != "VERBINDLICH" or contract.get("mode") != "HASH_BOUND_TRANSACTIONAL_SYNC":
        errors.append("I009_VERTRAG_ODER_MODUS_FALSCH")

    architecture = contract.get("architecture", {})
    for key in (
        "database_migration_required",
        "field_baseline_required_before_plan",
        "three_way_comparison_required",
        "deterministic_plan_required",
        "precheck_required",
        "single_atomic_transaction_required",
        "postcheck_required_before_commit",
        "audit_receipt_required",
        "fault_and_crash_matrix_required",
    ):
        if architecture.get(key) is not True:
            errors.append(f"I009_ARCHITEKTURREGEL_FEHLT: {key}")
    if architecture.get("schema_version") != 3:
        errors.append("I009_SCHEMA_VERTRAG_FALSCH")

    expected_states = {"UNCHANGED", "TODO_ONLY", "CALENDAR_ONLY", "BOTH_SAME", "BOTH_DIFFERENT", "BASELINE_MISSING"}
    if set(contract.get("field_states", [])) != expected_states:
        errors.append("I009_DREI_WEGE_ZUSTAENDE_UNVOLLSTAENDIG")
    safety = contract.get("safety", {})
    for key in (
        "both_different_hard_block", "detached_hard_block", "missing_baseline_hard_block",
        "due_end_manual_review", "no_cascade_delete", "optimistic_locking",
        "fault_injection_requires_explicit_enable", "process_crash_rollback_required",
    ):
        if safety.get(key) is not True:
            errors.append(f"I009_SICHERHEITSREGEL_FEHLT: {key}")

    migration = (ROOT / "migrations/0003_sync_field_baseline.sql").read_text(encoding="utf-8")
    for token in ("sync_field_baselines", "sync_audit_receipts", "baseline_sha256", "receipt_sha256", "ON DELETE RESTRICT"):
        if token not in migration:
            errors.append(f"I009_MIGRATION_BESTANDTEIL_FEHLT: {token}")
    if "ON DELETE CASCADE" in migration:
        errors.append("I009_KASKADIERENDES_LOESCHEN_VERBOTEN")

    repository_source = (ROOT / "storage/sync_repository.py").read_text(encoding="utf-8")
    for token in (
        "SYNC_AFTER_ENTITY_WRITE", "SYNC_AFTER_BASELINE_WRITE", "SYNC_BEFORE_RECEIPT",
        "SYNC_AFTER_RECEIPT_BEFORE_COMMIT", "receipt_sha256", "baseline_sha256",
        "expected_todo_version", "expected_event_version", "expected_link_version",
    ):
        if token not in repository_source:
            errors.append(f"I009_REPOSITORY_HAERTUNG_FEHLT: {token}")

    service_source = (ROOT / "services/sync_service.py").read_text(encoding="utf-8")
    for token in ("authoritative = self.plan", "authoritative != plan", "SYNC-STALE-006", "quick_check"):
        if token not in service_source:
            errors.append(f"I009_SERVICE_HAERTUNG_FEHLT: {token}")

    catalog = load("errors/SYNC_EXECUTION_FEHLERKATALOG.json")
    catalog_codes = {str(item.get("code")) for item in catalog.get("errors", [])}
    for code in ("SYNC-STALE-006", "SYNC-POSTCHECK-006", "SYNC-FAULT-001"):
        if code not in catalog_codes:
            errors.append(f"I009_FEHLERCODE_NICHT_KATALOGISIERT: {code}")

    runtime = "NOT_RUN"
    schema = 0
    try:
        from services.factory import open_planner_services
        from sync_core.model import FieldChangeState, SyncPlanState
        from todo_core.model import LinkDirection

        with tempfile.TemporaryDirectory(prefix="provoware-i009-validator-") as temp:
            services = open_planner_services(Path(temp) / "planer.sqlite3")
            schema = services.database.schema_version()
            zone = ZoneInfo("Europe/Berlin")
            start = datetime(2026, 8, 14, 10, 0, tzinfo=zone)
            end = start + timedelta(hours=1)
            todo = services.todos.create_todo(title="Basis", description="Basis", start_at=start, due_at=end)
            event = services.calendar.create_event(
                title="Basis", description="Basis", start_at=start, end_at=end, timezone_name="Europe/Berlin"
            )
            link = services.links.create_link(todo.todo_id, event.event_id, direction=LinkDirection.BIDIRECTIONAL)
            services.sync.initialize_baseline(link.link_id)
            todo2 = services.todos.update_todo(replace(todo, title="Todo"), expected_version=todo.version)
            event2 = services.calendar.update_event(replace(event, description="Kalender"), expected_version=event.version)
            if services.links.preview_conflict(link.link_id).value != "BOTH_CHANGED":
                errors.append("I009_RUNTIME_OBJEKTKONFLIKT_ERWARTET")
            plan = services.sync.plan(link.link_id)
            states = {field.field_id: field.state for field in plan.fields}
            if plan.state is not SyncPlanState.READY:
                errors.append(f"I009_RUNTIME_DISJUNKTER_PLAN_NICHT_READY: {plan.state.value}")
            if states.get("TITLE") is not FieldChangeState.TODO_ONLY or states.get("DESCRIPTION") is not FieldChangeState.CALENDAR_ONLY:
                errors.append("I009_RUNTIME_FELDWEISE_TRENNUNG_FEHLT")
            receipt = services.sync.commit(plan)
            if services.calendar.get_event(event.event_id).title != todo2.title:
                errors.append("I009_RUNTIME_TODO_ZU_KALENDER_FEHLT")
            if services.todos.get_todo(todo.todo_id).description != event2.description:
                errors.append("I009_RUNTIME_KALENDER_ZU_TODO_FEHLT")
            if len(receipt.receipt_sha256) != 64 or services.sync.receipt_count(link.link_id) != 1:
                errors.append("I009_RUNTIME_AUDIT_RECEIPT_FEHLT")
            services.database.quick_check()
            runtime = "PASS"
    except Exception as exc:
        errors.append(f"I009_RUNTIME_FEHLER: {type(exc).__name__}: {exc}")
        runtime = "FAIL"

    if schema != 3:
        errors.append(f"I009_SCHEMA_VERSION_FALSCH: {schema}")
    expected_chain = ["I002", "I003", "I004", "I005", "I006", "I007", "I008", "I009"]
    if contract.get("qualification", {}).get("historical_gate_chain") != expected_chain:
        errors.append("I009_HISTORISCHE_KETTE_FALSCH")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "repository_files": len(files),
        "schema_version": schema,
        "runtime": runtime,
    }


def main() -> int:
    result = validate()
    print(f"I009-VALIDATOR: {result['status']}")
    print(f"Schema: {result['schema_version']}")
    print(f"Runtime: {result['runtime']}")
    for error in result["errors"]:
        print(f"FEHLER: {error}")
    print("MASCHINENLESBAR:", json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
