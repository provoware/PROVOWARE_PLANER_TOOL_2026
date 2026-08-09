#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "ui"
TAURI = ROOT / "src-tauri"
EXPECTED_VERSION = "0.4.0-dev.1"


class RefParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.refs: list[str] = []
        self.scripts = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "script":
            self.scripts += 1
        for key in ("href", "src"):
            value = values.get(key)
            if value:
                self.refs.append(value)


def fail(message: str) -> None:
    raise AssertionError(message)


def main() -> int:
    config = json.loads((TAURI / "tauri.conf.json").read_text(encoding="utf-8"))
    if config["version"] != EXPECTED_VERSION:
        fail("Tauri-Konfigurationsversion stimmt nicht.")
    if config["build"]["frontendDist"] != "../ui":
        fail("frontendDist muss ausschließlich auf lokale UI-Assets zeigen.")

    csp = config["app"]["security"]["csp"]
    for forbidden in ("http:", "https:", "*", "'unsafe-eval'", "'unsafe-inline'"):
        if forbidden in csp:
            fail(f"CSP enthält unerlaubte Lockerung: {forbidden}")
    if "connect-src 'none'" not in csp:
        fail("TODO 1.2 erwartet connect-src 'none'.")

    html_path = UI / "index.html"
    parser = RefParser()
    parser.feed(html_path.read_text(encoding="utf-8"))
    if parser.scripts:
        fail("Walking Skeleton benötigt noch kein JavaScript.")
    for ref in parser.refs:
        if ref.startswith(("http://", "https://", "//")):
            fail(f"Remote-Asset gefunden: {ref}")
        target = UI / ref
        if not target.is_file():
            fail(f"Lokales Asset fehlt: {ref}")

    for path in UI.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            if re.search(r"https?://|//[A-Za-z0-9]", text):
                fail(f"Remote-Referenz in UI-Asset: {path.relative_to(ROOT)}")

    cargo = (TAURI / "Cargo.toml").read_text(encoding="utf-8")
    if f'version = "{EXPECTED_VERSION}"' not in cargo:
        fail("Cargo-Paketversion stimmt nicht.")
    if 'tauri = { version = "=2.11.2"' not in cargo:
        fail("Tauri Runtime ist nicht exakt auf 2.11.2 gepinnt.")
    if 'tauri-build = { version = "=2.6.2"' not in cargo:
        fail("tauri-build ist nicht exakt auf 2.6.2 gepinnt.")

    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix in {".rs", ".html", ".css", ".py"}:
            lines = path.read_text(encoding="utf-8").count("\n") + 1
            if lines > 1000:
                fail(f"Datei überschreitet 1000 Zeilen: {path.relative_to(ROOT)} ({lines})")

    registry = json.loads((ROOT / "manifests/traceability/TODO_1_2.registry.json").read_text(encoding="utf-8"))
    if registry["todo_id"] != "TODO-1.2":
        fail("Falsche Registry für den aktiven TODO.")
    for test in registry["tests"]:
        if test["status"] not in {"geplant", "bereit", "bestanden"}:
            fail(f"Unzulässiger Teststatus: {test['id']}")

    print("TODO 1.2 statische Vorprüfung: BESTANDEN")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"TODO 1.2 statische Vorprüfung: FEHLER – {exc}", file=sys.stderr)
        raise SystemExit(1)
