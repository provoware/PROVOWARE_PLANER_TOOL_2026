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
    "contracts/SYNC_JOURNAL_RECOVERY_CONTRACT.json",
    "errors/SYNC_HISTORY_FEHLERKATALOG.json",
    "migrations/0004_sync_journal_snapshots.sql",
    "sync_core/history.py",
    "storage/history_repository.py",
    "services/history_service.py",
    "viewmodel/sync_history_query.py",
    "viewmodel/sync_history_viewmodel.py",
    "ui/sync_history_window.py",
    "tests/test_i011_history_repository.py",
    "tests/test_i011_recovery_plan.py",
    "tests/test_i011_sync_history_gui.py",
    "tests/test_i011_fault_matrix.py",
    "tools/i011_history_fault_matrix.py",
    "tools/i011_sync_history_gui_matrix.py",
    "docs/I011_SYNC_JOURNAL_RECOVERY.md",
    ".github/workflows/i011-qualifikation.yml",
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
        errors.append(f"I011_DATEI_FEHLT: {path}")

    version = load("VERSION.json")
    status = load("PROJEKTSTATUS.json")
    project = load("PROJECT_CONTRACT.json")
    contract = load("contracts/SYNC_JOURNAL_RECOVERY_CONTRACT.json")
    current = _iteration(version.get("iteration"))

    if current < 11:
        errors.append("I011_VERSION_UNTER_MINDESTSTAND")
    if current == 11 and version.get("version") != "0.11.0-dev.1":
        errors.append("I011_VERSION_FALSCH")
    if _iteration(status.get("iteration")) < 11:
        errors.append("I011_STATUS_UNTER_MINDESTSTAND")
    if _iteration(project.get("foundation", {}).get("current_iteration")) < 11:
        errors.append("I011_PROJEKTVERTRAG_UNTER_MINDESTSTAND")
    if contract.get("status") != "VERBINDLICH" or contract.get("mode") != "IMMUTABLE_JOURNAL_HASH_BOUND_RECOVERY":
        errors.append("I011_VERTRAG_ODER_MODUS_FALSCH")

    architecture = contract.get("architecture", {})
    for key in (
        "journal_query_read_only",
        "receipt_hash_revalidation_required",
        "snapshot_hash_revalidation_required",
        "legacy_receipts_remain_valid",
        "legacy_values_must_not_be_invented",
        "before_after_snapshot_required_for_new_commits",
        "snapshot_same_transaction_as_receipt",
        "recovery_plan_new_object_required",
        "source_receipt_hash_required",
        "source_snapshot_hash_required",
        "current_syncplan_hash_required",
        "recovery_plan_deterministic",
        "same_i009_transaction_core_required",
        "precheck_required",
        "postcheck_required",
        "new_receipt_after_recovery_required",
        "fault_crash_matrix_required",
        "gui_matrix_required",
    ):
        if architecture.get(key) is not True:
            errors.append(f"I011_ARCHITEKTURREGEL_FEHLT: {key}")
    if architecture.get("schema_version") != 4:
        errors.append("I011_SCHEMA_VERTRAG_FALSCH")

    safety = contract.get("safety", {})
    for key in (
        "no_historical_auto_replay",
        "no_free_historical_value_write",
        "target_must_exist_on_current_endpoint",
        "direction_contract_still_applies",
        "due_end_semantic_review_still_applies",
        "divergent_historical_state_not_auto_reconstructed",
        "stale_current_state_hard_block",
        "tampered_receipt_hard_block",
        "tampered_snapshot_hard_block",
        "tampered_recovery_plan_hard_block",
        "no_partial_commit",
        "no_silent_legacy_backfill",
    ):
        if safety.get(key) is not True:
            errors.append(f"I011_SICHERHEITSREGEL_FEHLT: {key}")

    migration = (ROOT / "migrations/0004_sync_journal_snapshots.sql").read_text(encoding="utf-8")
    for token in ("sync_history_snapshots", "snapshot_sha256", "before_json", "after_json", "ON DELETE RESTRICT"):
        if token not in migration:
            errors.append(f"I011_MIGRATION_BESTANDTEIL_FEHLT: {token}")
    if "ON DELETE CASCADE" in migration:
        errors.append("I011_KASKADIERENDES_LOESCHEN_VERBOTEN")

    repository_source = (ROOT / "storage/sync_repository.py").read_text(encoding="utf-8")
    for token in (
        "snapshot_payload(",
        "snapshot_hash(",
        "SYNC_AFTER_HISTORY_SNAPSHOT",
        "SYNC-HISTORY-POSTCHECK-001",
        "INSERT INTO sync_history_snapshots",
    ):
        if token not in repository_source:
            errors.append(f"I011_ATOMARER_SNAPSHOT_FEHLT: {token}")

    service_source = (ROOT / "services/history_service.py").read_text(encoding="utf-8")
    for token in (
        "source.receipt_sha256 != plan.source_receipt_sha256",
        "source.snapshot_sha256 != plan.source_snapshot_sha256",
        "sync_plan_hash(current) != plan.current_sync_plan_sha256",
        "expected != plan",
        "to_execution_plan(plan)",
    ):
        if token not in service_source:
            errors.append(f"I011_RECOVERY_HAERTUNG_FEHLT: {token}")

    query_source = (ROOT / "viewmodel/sync_history_query.py").read_text(encoding="utf-8")
    for forbidden in ("INSERT ", "UPDATE ", "DELETE "):
        if forbidden in query_source.upper():
            errors.append(f"I011_QUERY_SCHREIBT_UNERLAUBT: {forbidden.strip()}")

    runtime = "NOT_RUN"
    schema = 0
    try:
        from services.factory import open_planner_services
        from sync_core.history import JournalIntegrityState, RecoveryMode, RecoveryPlanState
        from todo_core.model import LinkDirection

        with tempfile.TemporaryDirectory(prefix="provoware-i011-validator-") as temp:
            services = open_planner_services(Path(temp) / "planer.sqlite3")
            schema = services.database.schema_version()
            zone = ZoneInfo("Europe/Berlin")
            start = datetime(2026, 8, 14, 17, 0, tzinfo=zone)
            end = start + timedelta(hours=1)
            todo = services.todos.create_todo(title="Basis", description="Text", start_at=start, due_at=end)
            event = services.calendar.create_event(
                title="Basis", description="Text", start_at=start, end_at=end, timezone_name="Europe/Berlin"
            )
            link = services.links.create_link(todo.todo_id, event.event_id, direction=LinkDirection.BIDIRECTIONAL)
            services.sync.initialize_baseline(link.link_id)
            services.todos.update_todo(replace(todo, title="Nachher"), expected_version=todo.version)
            first = services.sync.commit(services.sync.plan(link.link_id))
            record = services.journal.get_record(first.receipt_id)
            if record.integrity is not JournalIntegrityState.VERIFIED or not record.recovery_available:
                errors.append("I011_RUNTIME_JOURNAL_NICHT_VERIFIZIERT")
            if services.journal.history_repository.snapshot_count(link.link_id) != 1:
                errors.append("I011_RUNTIME_SNAPSHOT_FEHLT")

            current_event = services.calendar.get_event(event.event_id)
            services.calendar.update_event(
                replace(current_event, title="Abweichung"),
                expected_version=current_event.version,
            )
            recovery = services.journal.build_recovery(first.receipt_id, RecoveryMode.REAPPLY_AFTER)
            if recovery.state is not RecoveryPlanState.READY:
                errors.append(f"I011_RUNTIME_RECOVERY_NICHT_READY: {recovery.blocking_reason}")
            second = services.journal.commit_recovery(recovery)
            if not second.plan_id.startswith("RECOVERYPLAN-"):
                errors.append("I011_RUNTIME_RECOVERY_RECEIPT_PLAN_FEHLT")
            if second.precondition_sha256 != recovery.recovery_sha256:
                errors.append("I011_RUNTIME_RECOVERY_HASH_BINDUNG_FEHLT")
            if services.calendar.get_event(event.event_id).title != "Nachher":
                errors.append("I011_RUNTIME_RECOVERY_ZIEL_FEHLT")
            if services.journal.history_repository.snapshot_count(link.link_id) != 2:
                errors.append("I011_RUNTIME_ZWEITER_SNAPSHOT_FEHLT")
            services.database.quick_check()
            runtime = "PASS"
    except Exception as exc:
        errors.append(f"I011_RUNTIME_FEHLER: {type(exc).__name__}: {exc}")
        runtime = "FAIL"

    if schema != 4:
        errors.append(f"I011_SCHEMA_VERSION_FALSCH: {schema}")

    expected_chain = ["I002", "I003", "I004", "I005", "I006", "I007", "I008", "I009", "I010", "I011"]
    if contract.get("qualification", {}).get("historical_gate_chain") != expected_chain:
        errors.append("I011_HISTORISCHE_KETTE_FALSCH")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "repository_files": len(files),
        "schema_version": schema,
        "runtime": runtime,
    }


def main() -> int:
    result = validate()
    print(f"I011-VALIDATOR: {result['status']}")
    print(f"Schema: {result['schema_version']}")
    print(f"Runtime: {result['runtime']}")
    for error in result["errors"]:
        print(f"FEHLER: {error}")
    print("MASCHINENLESBAR:", json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
