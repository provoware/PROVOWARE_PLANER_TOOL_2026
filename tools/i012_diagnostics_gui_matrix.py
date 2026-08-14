#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication

from services.diagnostics_service import DiagnosticsService
from services.factory import open_planner_services
from ui.diagnostics_window import DiagnosticsWindow


SIZES = ((1024, 768), (1280, 720), (1366, 768), (1600, 900), (1920, 1080))
SCALES = (90, 100, 110, 125, 150, 175, 200)


def run(output: Path) -> dict:
    app = QApplication.instance() or QApplication([])
    results: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="provoware-i012-matrix-") as temp:
        workspace = Path(temp)
        services = open_planner_services(workspace / "planer.sqlite3")
        window = DiagnosticsWindow(
            DiagnosticsService(services.database, services.journal, workspace=workspace),
            repo_root=ROOT,
        )
        for width, height in SIZES:
            for scale in SCALES:
                window.design.apply_font_scale(scale)
                window.resize(width, height)
                window.show()
                app.processEvents()
                header_ok = all(window.table.columnWidth(i) > 0 for i in range(window.table.columnCount()))
                rows_ok = window.table.rowCount() == 5 and all(window.table.rowHeight(i) > 0 for i in range(5))
                controls_ok = window.refresh_button.width() > 0 and window.refresh_button.height() > 0
                passed = header_ok and rows_ok and controls_ok
                results.append(
                    {
                        "width": width,
                        "height": height,
                        "font_scale": scale,
                        "header_ok": header_ok,
                        "rows_ok": rows_ok,
                        "controls_ok": controls_ok,
                        "pass": passed,
                    }
                )
        window.close()
    payload = {
        "status": "PASS" if results and all(item["pass"] for item in results) else "FAIL",
        "configurations": len(results),
        "results": results,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "I012_DIAGNOSTICS_GUI_MATRIX.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = run(args.output)
    print(f"I012_DIAGNOSTICS_GUI_MATRIX={payload['status']} Konfigurationen={payload['configurations']}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
