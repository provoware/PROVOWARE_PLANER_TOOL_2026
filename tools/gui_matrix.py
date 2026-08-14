#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.factory import open_calendar_service
from ui.calendar_window import CalendarWindow
from viewmodel.calendar_viewmodel import CalendarViewMode

SIZES = ((1280, 720), (1366, 768), (1600, 900), (1920, 1080))
SCALES = (90, 100, 110, 125, 150, 175, 200)


def run(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    results: list[dict] = []
    failures: list[str] = []

    with tempfile.TemporaryDirectory(prefix="provoware-i005-matrix-") as temp:
        workspace = Path(temp)
        service = open_calendar_service(workspace / "planer.sqlite3")
        zone = ZoneInfo("Europe/Berlin")
        for hour, marker_id in ((8, 1), (10, 2), (12, 3), (14, 4), (16, 5)):
            start = datetime(2026, 8, 14, hour, 0, tzinfo=zone)
            service.create_event(
                title=f"Matrix-Termin {marker_id}",
                start_at=start,
                end_at=start + timedelta(minutes=45),
                timezone_name="Europe/Berlin",
                marker_id=marker_id,
            )
        window = CalendarWindow(service, repo_root=ROOT, workspace=workspace)
        window.view_model.select_date(date(2026, 8, 14))
        window.show()
        app.processEvents()
        try:
            for width, height in SIZES:
                for scale in SCALES:
                    scale_index = window.font_combo.findData(scale)
                    window.font_combo.setCurrentIndex(scale_index)
                    for mode in CalendarViewMode:
                        window._set_mode(mode)
                        window.resize(width, height)
                        window.refresh()
                        app.processEvents()
                        key = f"{width}x{height}-{scale}-{mode.value}"
                        problems: list[str] = []
                        if window.stack.width() < 200 or window.stack.height() < 120:
                            problems.append("Kalenderfläche zu klein")
                        if not all(label.isVisible() and label.text().strip() for label in window.marker_labels):
                            problems.append("Fünf Markierungen nicht vollständig sichtbar")
                        for button in window.findChildren(QPushButton):
                            if not button.isVisible():
                                continue
                            needed = button.fontMetrics().horizontalAdvance(button.text()) + 24
                            if button.width() < needed:
                                problems.append(f"Buttontext abgeschnitten: {button.text()}")
                        status = "PASS" if not problems else "FAIL"
                        results.append({
                            "configuration": key,
                            "width": width,
                            "height": height,
                            "font_scale_percent": scale,
                            "view": mode.value,
                            "status": status,
                            "problems": problems,
                        })
                        if problems:
                            failures.append(f"{key}: {problems}")
                        if width == 1280 and height == 720 and scale in {100, 200}:
                            window.grab().save(str(output_dir / f"{mode.value.lower()}_{scale}.png"))
        finally:
            window.close()
            app.processEvents()

    report = {
        "schema_version": 1,
        "status": "PASS" if not failures else "FAIL",
        "configurations": len(results),
        "window_sizes": [f"{w}x{h}" for w, h in SIZES],
        "font_scales_percent": list(SCALES),
        "views": [mode.value for mode in CalendarViewMode],
        "results": results,
        "failures": failures,
    }
    (output_dir / "I005_GUI_MATRIX.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.output)
    print(f"I005_GUI_MATRIX={report['status']} Konfigurationen={report['configurations']}")
    for failure in report["failures"]:
        print("FEHLER:", failure)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
