from __future__ import annotations

import json
import os
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

GUI_CODE_PATTERN = re.compile(r"GUI-TODO-[A-Z0-9-]+-\d{3}")
REQUIRED_FILES = {
    "contracts/TODO_GUI_CONTRACT.json",
    "errors/TODO_GUI_FEHLERKATALOG.json",
    "viewmodel/todo_query.py",
    "viewmodel/todo_viewmodel.py",
    "ui/todo_dialogs.py",
    "ui/todo_window.py",
    "ui/planner_integration.py",
    "tests/test_i007_query_viewmodel.py",
    "tests/test_i007_gui_offscreen.py",
    "tests/test_i007_persistence_restart.py",
    "tools/todo_gui_matrix.py",
    ".github/workflows/i007-qualifikation.yml",
    "docs/I007_TODO_GUI_VIEWMODEL.md",
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


def catalog_codes() -> tuple[set[str], list[str]]:
    codes: list[str] = []
    for path in sorted((ROOT / "errors").glob("*FEHLERKATALOG.json")):
        codes.extend(str(item.get("code")) for item in json.loads(path.read_text(encoding="utf-8")).get("errors", []))
    return set(codes), sorted({code for code in codes if codes.count(code) > 1})


def used_gui_codes() -> set[str]:
    codes: set[str] = set()
    for path in (ROOT / "ui").glob("todo_*.py"):
        codes.update(GUI_CODE_PATTERN.findall(path.read_text(encoding="utf-8")))
    return codes


def validate() -> dict:
    errors: list[str] = []
    files = repository_files()
    for path in sorted(REQUIRED_FILES - files):
        errors.append(f"I007_DATEI_FEHLT: {path}")

    version = load("VERSION.json")
    status = load("PROJEKTSTATUS.json")
    project = load("PROJECT_CONTRACT.json")
    contract = load("contracts/TODO_GUI_CONTRACT.json")
    current = _iteration(version.get("iteration"))
    if current < 7:
        errors.append("I007_VERSION_UNTER_MINDESTSTAND")
    if current == 7 and version.get("version") != "0.7.0-dev.1":
        errors.append("I007_VERSION_FALSCH")
    if _iteration(status.get("iteration")) < 7:
        errors.append("I007_STATUS_UNTER_MINDESTSTAND")
    if _iteration(project.get("foundation", {}).get("current_iteration")) < 7:
        errors.append("I007_PROJEKTVERTRAG_UNTER_MINDESTSTAND")
    if contract.get("status") != "VERBINDLICH":
        errors.append("I007_VERTRAG_NICHT_VERBINDLICH")

    architecture = contract.get("architecture", {})
    expected_chain = ["TodoService", "TodoQueryService", "TodoViewModel", "Darstellungsmodelle", "PySide6_Qt"]
    if architecture.get("required_chain") != expected_chain:
        errors.append("I007_ARCHITEKTURKETTE_FALSCH")
    for key in ("ui_may_import_repository", "ui_may_execute_sql", "viewmodel_may_import_repository"):
        if architecture.get(key) is not False:
            errors.append(f"I007_SCHICHTGRENZE_FEHLT: {key}")
    if architecture.get("query_uses_service_api_only") is not True:
        errors.append("I007_QUERY_SERVICE_GRENZE_FEHLT")

    required_views = ["HEUTE", "DIESE_WOCHE", "UEBERFAELLIG", "OHNE_DATUM", "ERLEDIGT"]
    if contract.get("required_views") != required_views:
        errors.append("I007_FUENF_ANSICHTEN_FALSCH")
    link = contract.get("calendar_link", {})
    for key in (
        "conflict_status_visible",
        "conflict_explanation_visible",
        "unlink_must_not_delete_entities",
        "todo_delete_must_not_delete_event",
        "query_conflict_preview_must_not_write",
    ):
        if link.get(key) is not True:
            errors.append(f"I007_LINKREGEL_FEHLT: {key}")
    if link.get("automatic_conflict_resolution_in_i007") is not False:
        errors.append("I007_AUTO_KONFLIKTAUFLOESUNG_MUSS_AUS_SEIN")
    if link.get("automatic_payload_sync_in_i007") is not False:
        errors.append("I007_AUTOSYNC_MUSS_AUS_SEIN")

    accessibility = contract.get("accessibility", {})
    expected_scales = [90, 100, 110, 125, 150, 175, 200]
    if accessibility.get("font_scale_percent") != expected_scales:
        errors.append("I007_SCHRIFTMATRIX_FALSCH")
    for key in ("keyboard_navigation_required", "accessible_names_required", "high_contrast_semantics_required", "status_not_color_only"):
        if accessibility.get(key) is not True:
            errors.append(f"I007_BARRIEREFREIHEIT_FEHLT: {key}")

    qualification = contract.get("qualification", {})
    if qualification.get("offscreen_matrix_min_configurations", 0) < 140:
        errors.append("I007_GUI_MATRIX_ZU_KLEIN")
    if qualification.get("historical_gate_chain") != ["I002", "I003", "I004", "I005", "I006", "I007"]:
        errors.append("I007_HISTORISCHE_KETTE_FALSCH")

    layer_files = (
        "viewmodel/todo_query.py",
        "viewmodel/todo_viewmodel.py",
        "ui/todo_dialogs.py",
        "ui/todo_window.py",
        "ui/planner_integration.py",
    )
    forbidden = ("sqlite3", "storage.", "storage import", "MigrationRunner", "SELECT ", "INSERT ", "UPDATE ", "DELETE ")
    for relative in layer_files:
        text = (ROOT / relative).read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                errors.append(f"I007_SCHICHTVERLETZUNG: {relative} enthält {token!r}")

    query_text = (ROOT / "viewmodel/todo_query.py").read_text(encoding="utf-8")
    if "preview_conflict" not in query_text:
        errors.append("I007_PURE_KONFLIKTVORSCHAU_FEHLT")
    for forbidden_call in ("assess_conflict", "mark_synchronized"):
        if forbidden_call in query_text:
            errors.append(f"I007_QUERY_DARF_NICHT_SCHREIBEN: {forbidden_call}")

    combined = "\n".join((ROOT / path).read_text(encoding="utf-8") for path in layer_files)
    for token in (
        "TodoQueryService", "TodoViewModel", "Heute", "Diese Woche", "Überfällig", "Ohne Datum", "Erledigt",
        "Ctrl+N", "Ctrl+E", "Ctrl+Shift+N", "Ctrl+L", "apply_font_scale", "accessible(",
        "automatisch", "Verknüpfung", "Unteraufgabe",
    ):
        if token not in combined:
            errors.append(f"I007_GUI_BESTANDTEIL_FEHLT: {token}")

    workflow = (ROOT / ".github/workflows/i007-qualifikation.yml").read_text(encoding="utf-8") if (ROOT / ".github/workflows/i007-qualifikation.yml").is_file() else ""
    for token in ("verify_sha", "git rev-parse HEAD", "inputs[verify_sha]", "github.actor != 'github-actions[bot]'", "todo_gui_matrix.py"):
        if token not in workflow:
            errors.append(f"I007_WORKFLOW_HAERTUNG_FEHLT: {token}")

    catalogs, duplicates = catalog_codes()
    used = used_gui_codes()
    if duplicates:
        errors.append(f"I007_FEHLERCODE_DOPPELT: {duplicates}")
    missing = sorted(used - catalogs)
    if missing:
        errors.append(f"I007_FEHLERCODE_NICHT_KATALOGISIERT: {missing}")

    runtime = "NOT_RUN"
    schema = 0
    try:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication
        from services.factory import open_planner_services
        from todo_core.model import LinkConflictStatus, LinkDirection
        from ui.todo_window import TodoWindow
        from viewmodel.todo_query import TodoListMode, TodoQueryService

        with tempfile.TemporaryDirectory(prefix="provoware-i007-validator-") as temp:
            workspace = Path(temp)
            services = open_planner_services(workspace / "planer.sqlite3")
            schema = services.database.schema_version()
            zone = ZoneInfo("Europe/Berlin")
            now = datetime.now(zone).replace(second=0, microsecond=0)
            todo = services.todos.create_todo(title="I007 Todo", due_at=now + timedelta(hours=1))
            event = services.calendar.create_event(
                title="I007 Termin",
                start_at=now + timedelta(hours=2),
                end_at=now + timedelta(hours=3),
                timezone_name="Europe/Berlin",
            )
            created_link = services.links.create_link(todo.todo_id, event.event_id, direction=LinkDirection.BIDIRECTIONAL)
            services.todos.update_todo(replace(todo, title="I007 Todo geändert"), expected_version=todo.version)
            services.calendar.update_event(replace(event, title="I007 Termin geändert"), expected_version=event.version)
            query = TodoQueryService(services.todos, services.links, timezone_name="Europe/Berlin")
            view = query.one(todo.todo_id)
            if view.links[0].conflict_status is not LinkConflictStatus.BOTH_CHANGED:
                errors.append("I007_RUNTIME_BOTH_CHANGED_NICHT_SICHTBAR")
            stored_link = services.links.get_link(created_link.link_id)
            if stored_link.conflict_status is not LinkConflictStatus.CLEAN or stored_link.version != 1:
                errors.append("I007_RUNTIME_KONFLIKTVORSCHAU_HAT_GESCHRIEBEN")
            if len(TodoListMode) != 5:
                errors.append("I007_RUNTIME_ANSICHTSANZAHL_FALSCH")
            app = QApplication.instance() or QApplication([])
            window = TodoWindow(
                services.todos,
                services.links,
                services.calendar,
                repo_root=ROOT,
                workspace=workspace,
                timezone_name="Europe/Berlin",
            )
            window.show(); app.processEvents()
            if window.mode_combo.count() != 5:
                errors.append("I007_RUNTIME_GUI_ANSICHTEN_FEHLEN")
            if not window.status_label.text().strip():
                errors.append("I007_RUNTIME_GUI_STATUS_FEHLT")
            window.close(); app.processEvents()
            services.database.quick_check()
            runtime = "PASS"
    except Exception as exc:
        errors.append(f"I007_RUNTIME_FEHLER: {type(exc).__name__}: {exc}")
        runtime = "FAIL"

    if current == 7 and schema != 2:
        errors.append(f"I007_SCHEMA_VERSION_FALSCH: {schema}")
    elif current > 7 and schema < 2:
        errors.append(f"I007_HISTORISCHE_SCHEMA_BASIS_FEHLT: {schema}")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "repository_files": len(files),
        "todo_gui_error_codes_used": len(used),
        "todo_gui_error_codes_registered": len(used & catalogs),
        "schema_version": schema,
        "runtime": runtime,
    }


def main() -> int:
    result = validate()
    print(f"I007-VALIDATOR: {result['status']}")
    print(f"Todo-GUI-Fehlercodes: {result['todo_gui_error_codes_registered']}/{result['todo_gui_error_codes_used']}")
    print(f"Schema: {result['schema_version']}")
    print(f"Runtime: {result['runtime']}")
    for error in result["errors"]:
        print(f"FEHLER: {error}")
    print("MASCHINENLESBAR:", json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
