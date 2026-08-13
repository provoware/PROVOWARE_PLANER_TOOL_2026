#!/usr/bin/env python3
"""Kanonischer Einstieg für automatisierte Foundation-Prüfungen."""

from __future__ import annotations

import argparse
from pathlib import Path

from standard_validator import print_result, validate_repository


def main() -> int:
    parser = argparse.ArgumentParser(description="PROVOWARE Entwicklungs- und Prüfautopilot")
    parser.add_argument("command", choices=["pruefen", "qualifizieren"])
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    result = validate_repository(root)
    print_result(result)
    if not result["ok"]:
        return 1

    if args.command == "qualifizieren":
        print("QUALIFIKATION: PASS - Foundation-Verträge, Standards, Dokumentation und Repository-Inventar sind konsistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
