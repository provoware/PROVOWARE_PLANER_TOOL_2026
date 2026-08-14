#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.factory import open_planner_services
from todo_core.model import LinkDirection
from ui.sync_history_window import SyncHistoryWindow

SIZES = ((1024, 768), (1366, 768), (1600, 900), (1920, 1080), (2560, 1440))
SCALES = (90, 100, 110, 125, 150, 175, 200)


def _seed(services) -> None:
    zone = ZoneInfo("Europe/Berlin")
    start = datetime(2026, 8, 14, 16, 0, tzinfo=zone)
    end = start + timedelta(hours=1)
    todo = services.todos.create_todo(title="Basis", description="Basis", start_at=start, due_at=end)
    event = services.calendar.create_event(
        title="Basis", description="Basis", start_at=start, end_at=end, timezone_name="Europe/Berlin"
    )
    link = services.links.create_link(todo.todo_id, event.event_id, direction=LinkDirection.BIDIRECTIONAL)
    services.sync.initialize_baseline(link.link_id)
    services.todos.update_todo(replace(todo, title="Nachher"), expected_version=todo.version)
    services.sync.commit(services.sync.plan(link.link_id))


def run(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    results: list[dict] = []
    failures: list[str] = []

    with tempfile.TemporaryDirectory(prefix="provoware-i011-history-gui-matrix-") as temp:
        services = open_planner_services(Path(temp) / "planer.sqlite3")
        _seed(services)
        window = SyncHistoryWindow(services.journal, repo_root=ROOT)
        window.show()
        app.processEvents()
        window.history_table.selectRow(0)
        window.select_current()
        app.processEvents()
        try:
            for width, height in SIZES:
                for scale in SCALES:
                    window.design.apply_font_scale(scale)
                    window.resize(width, height)
                    app.processEvents()
                    key = f"{width}x{height}-{scale}"
                    problems: list[str] = []
                    if window.width() > width or window.height() > height:
                        problems.append(
                            f"Fenster überschreitet Zielgröße: {window.width()}x{window.height()} statt maximal {width}x{height}"
                        )
                    if window.history_table.height() < 140:
                        problems.append("Journaltabelle zu niedrig")
                    if window.detail_table.height() < 100:
                        problems.append("Vorher-/Nachher-Tabelle zu niedrig")
                    if window.history_table.rowCount() < 1:
                        problems.append("Journalnachweis fehlt")
                    if window.detail_table.rowCount() != 4:
                        problems.append("Detailtabelle zeigt nicht exakt vier Vertragsfelder")
                    if not window.status_label.text().strip():
                        problems.append("Status fehlt")
                    for button in window.findChildren(QPushButton):
                        if not button.isVisible():
                            continue
                        needed = button.fontMetrics().horizontalAdvance(button.text()) + 24
                        if button.width() < needed:
                            problems.append(f"Buttontext abgeschnitten: {button.text()}")
                    status = "PASS" if not problems else "FAIL"
                    results.append(
                        {
                            "configuration": key,
                            "width": width,
                            "height": height,
                            "actual_width": window.width(),
                            "actual_height": window.height(),
                            "font_scale_percent": scale,
                            "status": status,
                            "problems": problems,
                        }
                    )
                    if problems:
                        failures.append(f"{key}: {problems}")
                    if (width, height) == (1366, 768) and scale in {100, 200}:
                        window.grab().save(str(output_dir / f"sync_history_{scale}.png"))
        finally:
            window.close()
            app.processEvents()

    report = {
        "schema_version": 1,
        "status": "PASS" if not failures else "FAIL",
        "configurations": len(results),
        "window_sizes": [f"{w}x{h}" for w, h in SIZES],
        "font_scales_percent": list(SCALES),
        "results": results,
        "failures": failures,
    }
    (output_dir / "I011_SYNC_HISTORY_GUI_MATRIX.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.output)
    print(f"I011_SYNC_HISTORY_GUI_MATRIX={report['status']} Konfigurationen={report['configurations']}")
    for failure in report["failures"]:
        print("FEHLER:", failure)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
