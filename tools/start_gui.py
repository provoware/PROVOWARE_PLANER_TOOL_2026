#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.faults import RuntimeContext
from runtime.model import RuntimeState
from runtime.orchestrator import StartOrchestrator
from services.factory import open_calendar_service
from ui.calendar_window import CalendarWindow


def main() -> int:
    parser = argparse.ArgumentParser(description="PROVOWARE PLANER Kalender-GUI")
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--timezone", default="Europe/Berlin")
    parser.add_argument("--offscreen-smoke", action="store_true")
    parser.add_argument("--start-report", type=Path)
    args = parser.parse_args()

    workspace = args.workspace.expanduser().resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    report = StartOrchestrator(RuntimeContext(ROOT, workspace)).run()
    payload = report.to_dict()
    if args.start_report:
        args.start_report.parent.mkdir(parents=True, exist_ok=True)
        args.start_report.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(f"STARTSTATUS={payload['state']} | {payload['user_summary']}")
    if report.state not in {RuntimeState.READY, RuntimeState.DEGRADED}:
        return 2

    app = QApplication.instance() or QApplication(sys.argv)
    service = open_calendar_service(workspace / "planer.sqlite3")
    window = CalendarWindow(
        service,
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
