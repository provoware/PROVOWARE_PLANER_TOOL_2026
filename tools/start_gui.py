#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ctypes
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.faults import RuntimeContext
from runtime.model import RuntimeState
from runtime.orchestrator import StartOrchestrator


def _check_native_gui_runtime() -> tuple[bool, str]:
    contract = json.loads((ROOT / "contracts" / "GUI_RUNTIME_CONTRACT.json").read_text(encoding="utf-8"))
    missing: list[str] = []
    for library in contract.get("native_shared_libraries", []):
        try:
            ctypes.CDLL(library)
        except OSError:
            missing.append(library)
    if missing:
        return False, "Fehlende Linux-Bibliotheken: " + ", ".join(missing)
    try:
        from PySide6 import QtCore  # noqa: F401
        from PySide6.QtWidgets import QApplication  # noqa: F401
    except Exception as exc:
        return False, f"PySide6/Qt kann nicht geladen werden: {exc!r}"
    return True, "PySide6 und native GUI-Bibliotheken sind verfügbar."


def _write_start_report(path: Path, payload: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    candidate = path.with_suffix(path.suffix + ".tmp")
    candidate.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    candidate.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="PROVOWARE PLANER GUI")
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--timezone", default="Europe/Berlin")
    parser.add_argument("--offscreen-smoke", action="store_true")
    parser.add_argument("--start-report", type=Path)
    args = parser.parse_args()

    workspace = args.workspace.expanduser().resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    report = StartOrchestrator(RuntimeContext(ROOT, workspace)).run()
    payload = report.to_dict()
    report_path = args.start_report or (workspace / "LETZTER_STARTBERICHT.json")
    _write_start_report(report_path, payload)
    print(f"STARTSTATUS={payload['state']} | {payload['user_summary']}")
    if report.state not in {RuntimeState.READY, RuntimeState.DEGRADED}:
        return 2

    gui_ok, gui_detail = _check_native_gui_runtime()
    if not gui_ok:
        print("START-GUI-RUNTIME-001: Grafische Laufzeit ist unvollständig.")
        print(f"DETAIL: {gui_detail}")
        print("AKTION: GUI sicher blockiert; qualifizierten Runtime-Reparaturpfad verwenden.")
        return 3
    print(f"GUI_RUNTIME=PASS | {gui_detail}")

    from PySide6.QtWidgets import QApplication
    from services.factory import open_planner_services
    from ui.calendar_window import CalendarWindow
    from ui.planner_integration import attach_todo_module

    app = QApplication.instance() or QApplication(sys.argv)
    services = open_planner_services(workspace / "planer.sqlite3")
    window = CalendarWindow(
        services.calendar,
        repo_root=ROOT,
        workspace=workspace,
        timezone_name=args.timezone,
    )
    attach_todo_module(
        window,
        services,
        repo_root=ROOT,
        workspace=workspace,
        timezone_name=args.timezone,
    )
    window.show()
    if args.offscreen_smoke:
        app.processEvents()
        window.close()
        return 0
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
