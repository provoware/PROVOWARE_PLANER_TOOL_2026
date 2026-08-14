#!/usr/bin/env python3
"""Kanonischer Einstieg für automatisierte Projektprüfungen."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from i002_validator import validate as validate_i002
from i003_validator import validate as validate_i003
from i004_validator import validate as validate_i004
from i005_validator import validate as validate_i005
from i006_validator import validate as validate_i006
from i007_validator import validate as validate_i007
from i008_validator import validate as validate_i008
from i009_validator import validate as validate_i009
from i010_validator import validate as validate_i010
from standard_validator import print_result, validate_repository


def _iteration(root: Path) -> int:
    data = json.loads((root / "VERSION.json").read_text(encoding="utf-8")); value = str(data.get("iteration", "I000"))
    try: return int(value.removeprefix("I"))
    except ValueError: return 0


def _run_gate(name: str, result: dict) -> bool:
    status = result.get("status", "FAIL"); print(f"{name}: {status}")
    for warning in result.get("warnings", []): print(f"WARNUNG: {warning}")
    for error in result.get("errors", []): print(f"FEHLER: {error}")
    return status == "PASS"


def main() -> int:
    parser = argparse.ArgumentParser(description="PROVOWARE Entwicklungs- und Prüfautopilot"); parser.add_argument("command", choices=["pruefen", "qualifizieren"]); args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]; standard = validate_repository(root); print_result(standard)
    if not standard["ok"]: return 1
    current = _iteration(root); gates: list[tuple[str, dict]] = []
    if current >= 2: gates.append(("I002-EVIDENCE-GATE", validate_i002()))
    if current >= 3: gates.append(("I003-START-GATE", validate_i003()))
    if current >= 4: gates.append(("I004-KALENDER-DATEN-GATE", validate_i004()))
    if current >= 5: gates.append(("I005-KALENDER-GUI-GATE", validate_i005()))
    if current >= 6: gates.append(("I006-TODO-DOMAIN-LINK-GATE", validate_i006()))
    if current >= 7: gates.append(("I007-TODO-GUI-VIEWMODEL-GATE", validate_i007()))
    if current >= 8: gates.append(("I008-SYNC-KONFLIKT-GATE", validate_i008()))
    if current >= 9: gates.append(("I009-FELD-BASELINE-TRANSAKTIONS-GATE", validate_i009()))
    if current >= 10: gates.append(("I010-SYNC-CONTROL-RESOLUTION-GATE", validate_i010()))
    if not all(_run_gate(name, result) for name, result in gates): return 1
    if args.command == "qualifizieren": print("QUALIFIKATION: PASS - globale Standards, Repository-Inventar und alle historischen Pflichtgates bis zur aktuellen Iteration sind konsistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
