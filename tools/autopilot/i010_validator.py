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
    "contracts/SYNC_CONTROL_RESOLUTION_CONTRACT.json",
    "errors/SYNC_CONTROL_FEHLERKATALOG.json",
    "services/resolution_service.py",
    "sync_core/resolution.py",
    "viewmodel/sync_control_query.py",
    "viewmodel/sync_control_viewmodel.py",
    "ui/sync_control_window.py",
    "tests/test_i010_resolution_plan.py",
    "tests/test_i010_sync_control_query.py",
    "tests/test_i010_sync_control_gui.py",
    "tests/test_i010_fault_matrix.py",
    "tools/i010_resolution_fault_matrix.py",
    "tools/i010_sync_gui_matrix.py",
    "docs/I010_SYNC_CONTROL_GUI_RESOLUTION.md",
    ".github/workflows/i010-qualifikation.yml",
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
        if path.is_file()
        and ".git" not in path.parts
        and "__pycache__" not in path.parts
        and ".pytest_cache" not in path.parts
    }


def validate() -> dict:
    errors: list[str] = []
    files = repository_files()
    for path in sorted(REQUIRED_FILES - files):
        errors.append(f"I010_DATEI_FEHLT: {path}")

    version = load("VERSION.json")
    status = load("PROJEKTSTATUS.json")
    project = load("PROJECT_CONTRACT.json")
    contract = load("contracts/SYNC_CONTROL_RESOLUTION_CONTRACT.json")
    current = _iteration(version.get("iteration"))
    if current < 10:
        errors.append("I010_VERSION_UNTER_MINDESTSTAND")
    if current == 10 and version.get("version") != "0.10.0-dev.1":
        errors.append("I010_VERSION_FALSCH")
    if _iteration(status.get("iteration")) < 10:
        errors.append("I010_STATUS_UNTER_MINDESTSTAND")
    if _iteration(project.get("foundation", {}).get("current_iteration")) < 10:
        errors.append("I010_PROJEKTVERTRAG_UNTER_MINDESTSTAND")
    if contract.get("status") != "VERBINDLICH" or contract.get("mode") != "EXPLICIT_HASH_BOUND_RESOLUTION":
        errors.append("I010_VERTRAG_ODER_MODUS_FALSCH")

    architecture = contract.get("architecture", {})
    for key in (
        "sync_plan_is_read_only_source",
        "sync_control_query_required",
        "sync_control_viewmodel_required",
        "field_table_required",
        "resolution_plan_new_object_required",
        "source_plan_sha256_required",
        "source_precondition_sha256_required",
        "manual_choice_only_for_both_different",
        "default_choice_keep_blocked",
        "resolution_plan_deterministic",
        "same_i009_transaction_core_required",
        "precheck_required",
        "postcheck_required",
        "audit_receipt_required",
        "fault_crash_matrix_required",
    ):
        if architecture.get(key) is not True:
            errors.append(f"I010_ARCHITEKTURREGEL_FEHLT: {key}")

    if contract.get("choices") != ["TODO_WERT", "KALENDER_WERT", "BLOCKIERT_LASSEN"]:
        errors.append("I010_ENTSCHEIDUNGEN_FALSCH")

    safety = contract.get("safety", {})
    for key in (
        "no_syncplan_mutation",
        "no_heuristic_resolution",
        "all_both_different_fields_require_explicit_choice",
        "direction_contract_still_applies",
        "stale_source_hard_block",
        "tampered_resolution_hard_block",
        "manual_review_outside_both_different_not_auto_resolved",
        "no_partial_commit",
    ):
        if safety.get(key) is not True:
            errors.append(f"I010_SICHERHEITSREGEL_FEHLT: {key}")

    service_source = (ROOT / "services/resolution_service.py").read_text(encoding="utf-8")
    for token in (
        "sync_plan_hash(authoritative_source)",
        "expected != plan",
        "ResolutionChoice.KEEP_BLOCKED",
        "to_execution_plan(plan)",
        "database.quick_check()",
    ):
        if token not in service_source:
            errors.append(f"I010_SERVICE_HAERTUNG_FEHLT: {token}")

    ui_source = (ROOT / "ui/sync_control_window.py").read_text(encoding="utf-8")
    for token in (
        "Baseline",
        "Todo",
        "Kalender",
        "Zustand",
        "Geplante Aktion",
        "Grund",
        "Versionsstatus",
        "Hashstatus",
        "Entscheidung",
        "Blockiert lassen",
        "Atomar ausführen",
    ):
        if token not in ui_source:
            errors.append(f"I010_GUI_BESTANDTEIL_FEHLT: {token}")

    runtime = "NOT_RUN"
    schema = 0
    try:
        from services.factory import open_planner_services
        from services.resolution_service import ResolutionService
        from sync_core.resolution import ResolutionChoice, ResolutionPlanState
        from todo_core.model import LinkDirection
        from viewmodel.sync_control_query import SyncControlQuery
        from viewmodel.sync_control_viewmodel import SyncControlViewModel

        with tempfile.TemporaryDirectory(prefix="provoware-i010-validator-") as temp:
            services = open_planner_services(Path(temp) / "planer.sqlite3")
            schema = services.database.schema_version()
            zone = ZoneInfo("Europe/Berlin")
            start = datetime(2026, 8, 14, 15, 0, tzinfo=zone)
            end = start + timedelta(hours=1)
            todo = services.todos.create_todo(title="Basis", description="Basis", start_at=start, due_at=end)
            event = services.calendar.create_event(
                title="Basis", description="Basis", start_at=start, end_at=end, timezone_name="Europe/Berlin"
            )
            link = services.links.create_link(todo.todo_id, event.event_id, direction=LinkDirection.BIDIRECTIONAL)
            services.sync.initialize_baseline(link.link_id)
            services.todos.update_todo(replace(todo, title="Todo"), expected_version=todo.version)
            services.calendar.update_event(replace(event, title="Kalender"), expected_version=event.version)

            resolver = ResolutionService(services.sync, services.sync.repository)
            vm = SyncControlViewModel(SyncControlQuery(services.sync), services.sync, resolver)
            snapshot = vm.load(link.link_id)
            before_id = snapshot.plan.plan_id
            vm.choose("TITLE", ResolutionChoice.TODO_VALUE)
            resolution = vm.prepare_resolution()
            if resolution.state is not ResolutionPlanState.READY:
                errors.append("I010_RUNTIME_RESOLUTION_NICHT_READY")
            receipt = vm.execute()
            if snapshot.plan.plan_id != before_id:
                errors.append("I010_RUNTIME_SOURCE_PLAN_MUTIERT")
            if services.calendar.get_event(event.event_id).title != "Todo":
                errors.append("I010_RUNTIME_ENTSCHEIDUNG_NICHT_ANGEWENDET")
            if receipt.plan_id != resolution.resolution_plan_id:
                errors.append("I010_RUNTIME_RECEIPT_PLAN_BINDUNG_FEHLT")
            if receipt.precondition_sha256 != resolution.resolution_sha256:
                errors.append("I010_RUNTIME_RECEIPT_HASH_BINDUNG_FEHLT")
            services.database.quick_check()
            runtime = "PASS"
    except Exception as exc:
        errors.append(f"I010_RUNTIME_FEHLER: {type(exc).__name__}: {exc}")
        runtime = "FAIL"

    if current == 10 and schema != 3:
        errors.append(f"I010_SCHEMA_VERSION_FALSCH: {schema}")
    elif current > 10 and schema < 3:
        errors.append(f"I010_HISTORISCHE_SCHEMA_BASIS_FEHLT: {schema}")

    expected_chain = ["I002", "I003", "I004", "I005", "I006", "I007", "I008", "I009", "I010"]
    if contract.get("qualification", {}).get("historical_gate_chain") != expected_chain:
        errors.append("I010_HISTORISCHE_KETTE_FALSCH")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "repository_files": len(files),
        "schema_version": schema,
        "runtime": runtime,
    }


def main() -> int:
    result = validate()
    print(f"I010-VALIDATOR: {result['status']}")
    print(f"Schema: {result['schema_version']}")
    print(f"Runtime: {result['runtime']}")
    for error in result["errors"]:
        print(f"FEHLER: {error}")
    print("MASCHINENLESBAR:", json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
