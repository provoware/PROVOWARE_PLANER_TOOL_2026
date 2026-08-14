from __future__ import annotations

import json
import re
import sys
import tempfile
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CODE_PATTERN = re.compile(r"TODO-[A-Z0-9-]+-\d{3}")
REQUIRED_FILES = {
    "contracts/TODO_DOMAIN_LINK_CONTRACT.json", "docs/I006_TODO_DOMAIN_LINK.md", "errors/TODO_FEHLERKATALOG.json",
    "todo_core/__init__.py", "todo_core/errors.py", "todo_core/faults.py", "todo_core/model.py",
    "migrations/0002_todo_domain_links.sql", "storage/todo_repository.py", "services/todo_service.py",
    "tests/test_i006_domain.py", "tests/test_i006_persistence_links.py", "tests/test_i006_repository_constraints.py",
    "tests/test_i006_fault_matrix.py", "tools/i006_fault_matrix.py", ".github/workflows/i006-qualifikation.yml",
}


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _iteration(value: object) -> int:
    try: return int(str(value).removeprefix("I"))
    except ValueError: return 0


def repository_files() -> set[str]:
    return {str(path.relative_to(ROOT)) for path in ROOT.rglob("*") if path.is_file() and ".git" not in path.parts and "__pycache__" not in path.parts and ".pytest_cache" not in path.parts}


def catalog_codes() -> tuple[set[str], list[str]]:
    codes: list[str] = []
    for path in sorted((ROOT / "errors").glob("*FEHLERKATALOG.json")):
        codes.extend(str(item.get("code")) for item in json.loads(path.read_text(encoding="utf-8")).get("errors", []))
    return set(codes), sorted({code for code in codes if codes.count(code) > 1})


def used_todo_codes() -> set[str]:
    codes: set[str] = set()
    for path in [*(ROOT / "todo_core").rglob("*.py"), ROOT / "storage/todo_repository.py", ROOT / "services/todo_service.py", ROOT / "tools/i006_fault_matrix.py"]:
        codes.update(CODE_PATTERN.findall(path.read_text(encoding="utf-8")))
    return codes


def validate() -> dict:
    errors: list[str] = []
    files = repository_files()
    for path in sorted(REQUIRED_FILES - files): errors.append(f"I006_DATEI_FEHLT: {path}")
    version = load("VERSION.json"); status = load("PROJEKTSTATUS.json"); project = load("PROJECT_CONTRACT.json"); contract = load("contracts/TODO_DOMAIN_LINK_CONTRACT.json")
    current = _iteration(version.get("iteration"))
    if current < 6 or version.get("version") != "0.6.0-dev.1": errors.append("I006_VERSION_NICHT_AKTIV")
    if _iteration(status.get("iteration")) < 6: errors.append("I006_STATUS_NICHT_AKTIV")
    if _iteration(project.get("foundation", {}).get("current_iteration")) < 6: errors.append("I006_PROJEKTVERTRAG_NICHT_AKTIV")
    if contract.get("status") != "VERBINDLICH": errors.append("I006_VERTRAG_NICHT_VERBINDLICH")
    link_contract = contract.get("calendar_link", {}); database_contract = contract.get("database", {}); qualification = contract.get("qualification", {})
    for key in ("own_identity_required","soft_link_required","todo_delete_must_not_delete_event","event_delete_must_not_delete_todo","entity_delete_must_not_delete_link","physical_endpoint_delete_restricted","unlink_must_not_delete_entities","version_snapshots_required"):
        if link_contract.get(key) is not True: errors.append(f"I006_LINKREGEL_FEHLT: {key}")
    if link_contract.get("automatic_payload_sync_in_i006") is not False: errors.append("I006_AUTOSYNC_MUSS_AUS_SEIN")
    if database_contract.get("on_delete_cascade_forbidden") is not True: errors.append("I006_CASCADE_VERBOT_FEHLT")
    if database_contract.get("migration_version") != 2: errors.append("I006_MIGRATIONSVERSION_FALSCH")
    expected_conflicts = ["CLEAN","TODO_CHANGED","CALENDAR_CHANGED","BOTH_CHANGED","DETACHED"]
    if link_contract.get("conflict_states") != expected_conflicts: errors.append("I006_KONFLIKTZUSTAENDE_FALSCH")
    if qualification.get("historical_gate_chain") != ["I002","I003","I004","I005","I006"]: errors.append("I006_HISTORISCHE_KETTE_FALSCH")
    migration = (ROOT / "migrations/0002_todo_domain_links.sql").read_text(encoding="utf-8")
    if "ON DELETE CASCADE" in migration.upper(): errors.append("I006_ON_DELETE_CASCADE_GEFUNDEN")
    for token in ("CREATE TABLE IF NOT EXISTS todos", "CREATE TABLE IF NOT EXISTS todo_calendar_links", "ON DELETE RESTRICT", "ON DELETE SET NULL", "TODO_CHANGED", "BOTH_CHANGED", "DETACHED"):
        if token not in migration: errors.append(f"I006_MIGRATION_BESTANDTEIL_FEHLT: {token}")
    for path in (ROOT / "todo_core").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "PySide6" in text or "sqlite3" in text: errors.append(f"I006_DOMAIN_SCHICHTVERLETZUNG: {path.relative_to(ROOT)}")
    workflow = (ROOT / ".github/workflows/i006-qualifikation.yml").read_text(encoding="utf-8")
    for token in ("verify_sha", "git rev-parse HEAD", "inputs[verify_sha]", "github.actor != 'github-actions[bot]'", "i006_fault_matrix.py"):
        if token not in workflow: errors.append(f"I006_WORKFLOW_HAERTUNG_FEHLT: {token}")
    catalogs, duplicates = catalog_codes(); used = used_todo_codes()
    if duplicates: errors.append(f"I006_FEHLERCODE_DOPPELT: {duplicates}")
    missing = sorted(used - catalogs)
    if missing: errors.append(f"I006_FEHLERCODE_NICHT_KATALOGISIERT: {missing}")
    runtime = "NOT_RUN"; schema = 0
    try:
        from services.factory import open_planner_services
        from todo_core.model import LinkConflictStatus, LinkDirection
        with tempfile.TemporaryDirectory(prefix="provoware-i006-validator-") as temp:
            services = open_planner_services(Path(temp) / "planer.sqlite3"); schema = services.database.schema_version()
            zone = ZoneInfo("Europe/Berlin"); start = datetime(2026,8,14,9,0,tzinfo=zone)
            event = services.calendar.create_event(title="I006 Termin", start_at=start, end_at=start+timedelta(hours=1), timezone_name="Europe/Berlin")
            todo = services.todos.create_todo(title="I006 Todo", start_at=start, due_at=start+timedelta(hours=2))
            link = services.links.create_link(todo.todo_id, event.event_id, direction=LinkDirection.BIDIRECTIONAL)
            changed = services.todos.update_todo(replace(todo, title="I006 Todo geändert"), expected_version=todo.version)
            assessed = services.links.assess_conflict(link.link_id)
            if assessed.conflict_status is not LinkConflictStatus.TODO_CHANGED: errors.append("I006_RUNTIME_TODO_KONFLIKT_FEHLT")
            services.todos.delete_todo(changed.todo_id, expected_version=changed.version)
            detached = services.links.assess_conflict(link.link_id)
            if detached.conflict_status is not LinkConflictStatus.DETACHED: errors.append("I006_RUNTIME_DETACHED_FEHLT")
            if services.calendar.get_event(event.event_id).event_id != event.event_id: errors.append("I006_RUNTIME_EVENT_VERLOREN")
            if services.links.get_link(link.link_id).link_id != link.link_id: errors.append("I006_RUNTIME_LINK_VERLOREN")
            services.database.quick_check(); runtime = "PASS"
    except Exception as exc:
        errors.append(f"I006_RUNTIME_FEHLER: {type(exc).__name__}: {exc}"); runtime = "FAIL"
    if schema != 2: errors.append(f"I006_SCHEMA_VERSION_FALSCH: {schema}")
    return {"status":"PASS" if not errors else "FAIL","errors":errors,"repository_files":len(files),"todo_error_codes_used":len(used),"todo_error_codes_registered":len(used & catalogs),"schema_version":schema,"runtime":runtime}


def main() -> int:
    result = validate(); print(f"I006-VALIDATOR: {result['status']}"); print(f"Todo-Fehlercodes: {result['todo_error_codes_registered']}/{result['todo_error_codes_used']}"); print(f"Schema: {result['schema_version']}"); print(f"Runtime: {result['runtime']}")
    for error in result["errors"]: print(f"FEHLER: {error}")
    print("MASCHINENLESBAR:", json.dumps(result, ensure_ascii=False, sort_keys=True)); return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
