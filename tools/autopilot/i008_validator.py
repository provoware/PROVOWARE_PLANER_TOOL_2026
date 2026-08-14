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
    "contracts/SYNC_CONFLICT_CONTRACT.json",
    "errors/SYNC_FEHLERKATALOG.json",
    "sync_core/__init__.py",
    "sync_core/model.py",
    "services/sync_preview_service.py",
    "tests/test_i008_sync_preview.py",
    "tests/test_i008_contract_guards.py",
    "docs/I008_SYNC_KONFLIKTVERTRAG.md",
    ".github/workflows/i008-qualifikation.yml",
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
        errors.append(f"I008_DATEI_FEHLT: {path}")

    version = load("VERSION.json")
    status = load("PROJEKTSTATUS.json")
    project = load("PROJECT_CONTRACT.json")
    contract = load("contracts/SYNC_CONFLICT_CONTRACT.json")
    current = _iteration(version.get("iteration"))
    if current < 8:
        errors.append("I008_VERSION_UNTER_MINDESTSTAND")
    if current == 8 and version.get("version") != "0.8.0-dev.1":
        errors.append("I008_VERSION_FALSCH")
    if _iteration(status.get("iteration")) < 8:
        errors.append("I008_STATUS_UNTER_MINDESTSTAND")
    if _iteration(project.get("foundation", {}).get("current_iteration")) < 8:
        errors.append("I008_PROJEKTVERTRAG_UNTER_MINDESTSTAND")
    if contract.get("status") != "VERBINDLICH" or contract.get("mode") != "READ_ONLY_PREVIEW":
        errors.append("I008_VERTRAG_ODER_MODUS_FALSCH")

    architecture = contract.get("architecture", {})
    if architecture.get("database_migration_required") is not False:
        errors.append("I008_UNERWARTETE_MIGRATION")
    if architecture.get("preview_must_not_write") is not True:
        errors.append("I008_VORSCHAU_SCHREIBSPERRE_FEHLT")
    if architecture.get("write_api_present_in_i008") is not False:
        errors.append("I008_SCHREIB_API_MUSS_FEHLEN")
    if architecture.get("automatic_sync_in_i008") is not False:
        errors.append("I008_AUTOSYNC_MUSS_AUS_SEIN")

    safety = contract.get("safety", {})
    for key in (
        "both_changed_hard_block",
        "detached_hard_block",
        "baseline_divergence_hard_block",
        "semantic_due_end_requires_manual_review",
        "preview_write_permitted_must_be_false",
        "optimistic_versions_visible",
        "silent_field_translation_forbidden",
    ):
        if safety.get(key) is not True:
            errors.append(f"I008_SICHERHEITSREGEL_FEHLT: {key}")

    field_rules = {item.get("field_id"): item for item in contract.get("field_rules", [])}
    if set(field_rules) != {"TITLE", "DESCRIPTION", "START_AT", "DUE_END"}:
        errors.append("I008_FELDREGELN_UNVOLLSTAENDIG")
    if field_rules.get("DUE_END", {}).get("future_automatic_candidate") is not False:
        errors.append("I008_DUE_END_DARF_NICHT_AUTOMATISCH_SEIN")
    if field_rules.get("DUE_END", {}).get("semantic_review_required") is not True:
        errors.append("I008_DUE_END_PRUEFUNG_FEHLT")

    conflict_rules = contract.get("conflict_rules", {})
    if set(conflict_rules) != {"CLEAN", "TODO_CHANGED", "CALENDAR_CHANGED", "BOTH_CHANGED", "DETACHED"}:
        errors.append("I008_KONFLIKTMATRIX_UNVOLLSTAENDIG")
    if "block" not in conflict_rules.get("BOTH_CHANGED", "").lower():
        errors.append("I008_BOTH_CHANGED_NICHT_BLOCKIERT")

    source = (ROOT / "services/sync_preview_service.py").read_text(encoding="utf-8")
    for forbidden in ("def apply(", "def synchronize(", "def execute(", "mark_synchronized(", "assess_conflict("):
        if forbidden in source:
            errors.append(f"I008_UNERLAUBTE_SCHREIBSCHNITTSTELLE: {forbidden}")

    runtime = "NOT_RUN"
    schema = 0
    try:
        from services.factory import open_planner_services
        from sync_core.model import SyncFieldAction, SyncPreviewState
        from todo_core.model import LinkDirection

        with tempfile.TemporaryDirectory(prefix="provoware-i008-validator-") as temp:
            services = open_planner_services(Path(temp) / "planer.sqlite3")
            schema = services.database.schema_version()
            zone = ZoneInfo("Europe/Berlin")
            start = datetime(2026, 8, 14, 10, 0, tzinfo=zone)
            todo = services.todos.create_todo(title="Gleich", description="Text", start_at=start, due_at=start + timedelta(hours=1))
            event = services.calendar.create_event(
                title="Gleich", description="Text", start_at=start, end_at=start + timedelta(hours=1), timezone_name="Europe/Berlin"
            )
            link = services.links.create_link(todo.todo_id, event.event_id, direction=LinkDirection.BIDIRECTIONAL)
            services.todos.update_todo(replace(todo, title="Todo geändert"), expected_version=todo.version)
            services.calendar.update_event(replace(event, title="Termin geändert"), expected_version=event.version)
            preview = services.sync_preview.preview(link.link_id)
            if preview.state is not SyncPreviewState.BLOCKIERT_BEIDSEITIG:
                errors.append("I008_RUNTIME_BOTH_CHANGED_NICHT_BLOCKIERT")
            if preview.write_permitted:
                errors.append("I008_RUNTIME_WRITE_PERMITTED_FALSCH")
            if any(field.action not in {SyncFieldAction.IDENTISCH, SyncFieldAction.BLOCKIERT} for field in preview.fields):
                errors.append("I008_RUNTIME_BOTH_CHANGED_ENTHAELT_VORSCHLAG")
            stored = services.links.get_link(link.link_id)
            if stored.version != 1:
                errors.append("I008_RUNTIME_VORSCHAU_HAT_LINK_GESCHRIEBEN")
            services.database.quick_check()
            runtime = "PASS"
    except Exception as exc:
        errors.append(f"I008_RUNTIME_FEHLER: {type(exc).__name__}: {exc}")
        runtime = "FAIL"

    if schema != 2:
        errors.append(f"I008_SCHEMA_VERSION_FALSCH: {schema}")
    qualification = contract.get("qualification", {})
    if qualification.get("historical_gate_chain") != ["I002", "I003", "I004", "I005", "I006", "I007", "I008"]:
        errors.append("I008_HISTORISCHE_KETTE_FALSCH")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "repository_files": len(files),
        "schema_version": schema,
        "runtime": runtime,
    }


def main() -> int:
    result = validate()
    print(f"I008-VALIDATOR: {result['status']}")
    print(f"Schema: {result['schema_version']}")
    print(f"Runtime: {result['runtime']}")
    for error in result["errors"]:
        print(f"FEHLER: {error}")
    print("MASCHINENLESBAR:", json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
