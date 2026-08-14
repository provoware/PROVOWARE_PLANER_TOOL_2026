from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REQUIRED_FILES = {
    "contracts/CALENDAR_GUI_CONTRACT.json",
    "docs/I005_KALENDER_GUI_VIEWMODEL.md",
    "errors/KALENDER_GUI_FEHLERKATALOG.json",
    "requirements-gui.lock",
    "ui/__init__.py",
    "ui/design.py",
    "ui/dialogs.py",
    "ui/calendar_views.py",
    "ui/calendar_window.py",
    "viewmodel/__init__.py",
    "viewmodel/calendar_query.py",
    "viewmodel/calendar_viewmodel.py",
    "tools/start_gui.py",
    "tools/gui_matrix.py",
    "tests/test_i005_viewmodel.py",
    "tests/test_i005_gui_offscreen.py",
    "tests/test_i005_persistence_restart.py",
}
CODE_PATTERN = re.compile(r"(?:GUI|CAL)-[A-Z0-9-]+-\d{3}")


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


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
        data = json.loads(path.read_text(encoding="utf-8"))
        codes.extend(str(item.get("code")) for item in data.get("errors", []))
    duplicates = sorted({code for code in codes if codes.count(code) > 1})
    return set(codes), duplicates


def used_gui_codes() -> set[str]:
    codes: set[str] = set()
    for directory in ("ui", "viewmodel"):
        for path in (ROOT / directory).rglob("*.py"):
            codes.update(CODE_PATTERN.findall(path.read_text(encoding="utf-8")))
    return codes


def validate() -> dict:
    errors: list[str] = []
    files = repository_files()
    for path in sorted(REQUIRED_FILES - files):
        errors.append(f"I005_DATEI_FEHLT: {path}")

    version = load("VERSION.json")
    status = load("PROJEKTSTATUS.json")
    project = load("PROJECT_CONTRACT.json")
    contract = load("contracts/CALENDAR_GUI_CONTRACT.json")
    ui_standard = load("standards/UI_STANDARD.json")
    access_standard = load("standards/ACCESSIBILITY_STANDARD.json")

    if version.get("iteration") != "I005" or version.get("version") != "0.5.0-dev.1":
        errors.append("I005_VERSION_NICHT_PROMOVIERT")
    if status.get("iteration") != "I005":
        errors.append("I005_STATUS_NICHT_PROMOVIERT")
    if project.get("foundation", {}).get("current_iteration") != "I005":
        errors.append("I005_PROJEKTVERTRAG_NICHT_PROMOVIERT")
    if contract.get("status") != "VERBINDLICH":
        errors.append("I005_GUI_VERTRAG_NICHT_VERBINDLICH")

    architecture = contract.get("architecture", {})
    if architecture.get("service_only") is not True:
        errors.append("I005_SERVICE_GRENZE_FEHLT")
    if architecture.get("sql_in_gui_forbidden") is not True:
        errors.append("I005_SQL_VERBOT_FEHLT")
    if architecture.get("four_views") != ["TAG", "WOCHE", "MONAT", "JAHR"]:
        errors.append("I005_VIER_ANSICHTEN_VERTRAG_FALSCH")

    expected_scales = [90, 100, 110, 125, 150, 175, 200]
    if ui_standard.get("font_scale_percent") != expected_scales:
        errors.append("I005_SCHRIFTSKALA_STANDARD_FALSCH")
    if contract.get("accessibility", {}).get("font_scales_percent") != expected_scales:
        errors.append("I005_SCHRIFTSKALA_VERTRAG_FALSCH")
    if ui_standard.get("color_alone_forbidden") is not True:
        errors.append("I005_FARBALLEIN_STANDARD_FEHLT")
    if access_standard.get("rules", {}).get("accessible_names_required") is not True:
        errors.append("I005_ACCESSIBLE_NAMES_STANDARD_FEHLT")

    forbidden = ("sqlite3", "storage.", "storage import", "MigrationRunner", "SELECT ", "INSERT ", "UPDATE ", "DELETE ")
    for directory in ("ui", "viewmodel"):
        for path in (ROOT / directory).rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for token in forbidden:
                if token in text:
                    errors.append(f"I005_GUI_SCHICHTVERLETZUNG: {path.relative_to(ROOT)} enthält {token!r}")

    window_text = (ROOT / "ui/calendar_window.py").read_text(encoding="utf-8")
    views_text = (ROOT / "ui/calendar_views.py").read_text(encoding="utf-8")
    design_text = (ROOT / "ui/design.py").read_text(encoding="utf-8")
    viewmodel_text = (ROOT / "viewmodel/calendar_viewmodel.py").read_text(encoding="utf-8")
    query_text = (ROOT / "viewmodel/calendar_query.py").read_text(encoding="utf-8")
    required_tokens = (
        "DayView", "WeekView", "MonthView", "YearView",
        "Heute", "Zurück", "Vor", "Markierungen",
        "Ctrl+N", "Ctrl+E", "Ctrl+T", "Alt+",
        "setAccessibleName", "apply_font_scale",
    )
    combined = "\n".join((window_text, views_text, design_text, viewmodel_text, query_text))
    for token in required_tokens:
        if token not in combined:
            errors.append(f"I005_GUI_BESTANDTEIL_FEHLT: {token}")

    if "CalendarQueryService" not in viewmodel_text or "CalendarService" not in query_text:
        errors.append("I005_VIEWMODEL_QUERY_KETTE_FEHLT")

    catalogs, duplicates = catalog_codes()
    if duplicates:
        errors.append(f"I005_FEHLERCODE_DOPPELT: {duplicates}")
    missing_codes = sorted(used_gui_codes() - catalogs)
    if missing_codes:
        errors.append(f"I005_GUI_FEHLERCODE_NICHT_KATALOGISIERT: {missing_codes}")

    runtime_result = "NOT_RUN"
    try:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication
        from services.factory import open_calendar_service
        from ui.calendar_window import CalendarWindow
        from viewmodel.calendar_viewmodel import CalendarViewMode

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory(prefix="provoware-i005-validator-") as temp:
            workspace = Path(temp)
            service = open_calendar_service(workspace / "planer.sqlite3")
            window = CalendarWindow(service, repo_root=ROOT, workspace=workspace)
            try:
                window.resize(1280, 720)
                window.show()
                app.processEvents()
                for mode in CalendarViewMode:
                    window._set_mode(mode)
                    app.processEvents()
                if len(window.marker_labels) != 5:
                    errors.append("I005_RUNTIME_MARKER_ANZAHL_FALSCH")
                if not all(label.text().strip() for label in window.marker_labels):
                    errors.append("I005_RUNTIME_MARKER_TEXT_FEHLT")
                if window.stack.count() != 4:
                    errors.append("I005_RUNTIME_VIEW_ANZAHL_FALSCH")
                runtime_result = "PASS"
            finally:
                window.close()
                app.processEvents()
    except Exception as exc:
        errors.append(f"I005_RUNTIME_VALIDIERUNG_FEHLER: {type(exc).__name__}: {exc}")
        runtime_result = "FAIL"

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "repository_files": len(files),
        "gui_error_codes_used": len(used_gui_codes()),
        "gui_error_codes_registered": len(used_gui_codes() & catalogs),
        "qt_runtime": runtime_result,
    }


def main() -> int:
    result = validate()
    print(f"I005-VALIDATOR: {result['status']}")
    print(f"GUI-Fehlercodes: {result['gui_error_codes_registered']}/{result['gui_error_codes_used']}")
    print(f"Qt-Runtime: {result['qt_runtime']}")
    for error in result["errors"]:
        print(f"FEHLER: {error}")
    print("MASCHINENLESBAR:", json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
