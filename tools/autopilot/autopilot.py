#!/usr/bin/env python3
"""Kanonischer Einstieg für automatisierte Projektprüfungen."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Callable

from i002_validator import validate as validate_i002
from i003_validator import validate as validate_i003
from i004_validator import validate as validate_i004
from i005_validator import validate as validate_i005
from i006_validator import validate as validate_i006
from i007_validator import validate as validate_i007
from i008_validator import validate as validate_i008
from i009_validator import validate as validate_i009
from i010_validator import validate as validate_i010
from i011_validator import validate as validate_i011
from i012_validator import validate as validate_i012
from i013_validator import validate as validate_i013
from i014_validator import validate as validate_i014
from i015_validator import validate as validate_i015
from i016_validator import validate as validate_i016
from standard_validator import print_result, validate_repository


def _iteration(root: Path) -> int:
    data = json.loads((root / "VERSION.json").read_text(encoding="utf-8"))
    value = str(data.get("iteration", "I000"))
    try:
        return int(value.removeprefix("I"))
    except ValueError:
        return 0


def _run_gate(name: str, validator: Callable[[], dict]) -> tuple[bool, dict]:
    started = time.perf_counter()
    result = validator()
    duration_ms = round((time.perf_counter() - started) * 1000, 3)
    status = result.get("status", "FAIL")
    print(f"{name}: {status} | {duration_ms:.3f} ms")
    for warning in result.get("warnings", []):
        print(f"WARNUNG: {warning}")
    for error in result.get("errors", []):
        print(f"FEHLER: {error}")
    return status == "PASS", {"gate": name, "status": status, "duration_ms": duration_ms}


def main() -> int:
    parser = argparse.ArgumentParser(description="PROVOWARE Entwicklungs- und Prüfautopilot")
    parser.add_argument("command", choices=["pruefen", "qualifizieren"])
    parser.add_argument("--timing-output", type=Path, default=None)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]

    started = time.perf_counter()
    standard = validate_repository(root)
    standard_ms = round((time.perf_counter() - started) * 1000, 3)
    print_result(standard)
    print(f"STANDARD-LAUFZEIT: {standard_ms:.3f} ms")
    timings: list[dict] = [{"gate": "STANDARD", "status": standard["status"], "duration_ms": standard_ms}]
    if not standard["ok"]:
        return 1

    current = _iteration(root)
    validators: list[tuple[int, str, Callable[[], dict]]] = [
        (2, "I002-EVIDENCE-GATE", validate_i002),
        (3, "I003-START-GATE", validate_i003),
        (4, "I004-KALENDER-DATEN-GATE", validate_i004),
        (5, "I005-KALENDER-GUI-GATE", validate_i005),
        (6, "I006-TODO-DOMAIN-LINK-GATE", validate_i006),
        (7, "I007-TODO-GUI-VIEWMODEL-GATE", validate_i007),
        (8, "I008-SYNC-KONFLIKT-GATE", validate_i008),
        (9, "I009-FELD-BASELINE-TRANSAKTIONS-GATE", validate_i009),
        (10, "I010-SYNC-CONTROL-RESOLUTION-GATE", validate_i010),
        (11, "I011-SYNC-JOURNAL-RECOVERY-GATE", validate_i011),
        (12, "I012-DIAGNOSE-DASHBOARD-GATE", validate_i012),
        (13, "I013-ENTWICKLUNGSAUTOPILOT-V2-GATE", validate_i013),
        (14, "I014-TRANSPORTPROFILE-TRENNUNG-GATE", validate_i014),
        (15, "I015-BACKUP-RESTOREPLAN-GATE", validate_i015),
        (16, "I016-RESTORE-EXECUTION-SAFETY-GATE", validate_i016),
    ]
    for minimum, name, validator in validators:
        if current < minimum:
            continue
        passed, timing = _run_gate(name, validator)
        timings.append(timing)
        if not passed:
            if args.timing_output:
                args.timing_output.parent.mkdir(parents=True, exist_ok=True)
                args.timing_output.write_text(json.dumps({"status": "FAIL", "timings": timings}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return 1

    if args.timing_output:
        args.timing_output.parent.mkdir(parents=True, exist_ok=True)
        args.timing_output.write_text(json.dumps({"status": "PASS", "timings": timings}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.command == "qualifizieren":
        print("QUALIFIKATION: PASS - globale Standards, Repository-Inventar und alle historischen Pflichtgates bis zur aktuellen Iteration sind konsistent; jedes Gate wurde in diesem Pass genau einmal ausgeführt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
