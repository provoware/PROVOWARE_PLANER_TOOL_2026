#!/usr/bin/env python3
"""Unabhängiger Validator für PROVOWARE Foundation-Verträge und Repository-Inventar."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_FOUNDATION_FILES = (
    "PROJECT_CONTRACT.json",
    "VERSION.json",
    "PROJEKTSTATUS.json",
    "REPOSITORY_MANIFEST.json",
    "README.md",
    "TODO.md",
    "standards/STANDARD_INDEX.json",
)


def _load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"DATEI_FEHLT: {path.as_posix()}")
    except json.JSONDecodeError as exc:
        errors.append(f"JSON_UNGUELTIG: {path.as_posix()} Zeile {exc.lineno}: {exc.msg}")
    return {}


def _inventory(root: Path, ignored_parts: set[str]) -> set[str]:
    files: set[str] = set()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in ignored_parts for part in relative.parts):
            continue
        files.add(relative.as_posix())
    return files


def validate_repository(root: Path, foundation_checks: bool = True) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    warnings: list[str] = []

    manifest_path = root / "REPOSITORY_MANIFEST.json"
    manifest = _load_json(manifest_path, errors)
    expected = set(manifest.get("files", []))
    ignored = set(manifest.get("ignored_path_parts", [".git", "__pycache__", ".pytest_cache"]))
    actual = _inventory(root, ignored)

    for missing in sorted(expected - actual):
        errors.append(f"REPOSITORY_DATEI_FEHLT: {missing}")
    for unexpected in sorted(actual - expected):
        errors.append(f"REPOSITORY_DATEI_NICHT_REGISTRIERT: {unexpected}")

    declared_count = manifest.get("expected_file_count")
    if declared_count is not None and declared_count != len(expected):
        errors.append(f"MANIFEST_ANZAHL_FALSCH: erwartet deklariert {declared_count}, Liste hat {len(expected)}")
    if expected and declared_count != len(actual):
        errors.append(f"REPOSITORY_ANZAHL_FALSCH: Soll {declared_count}, Ist {len(actual)}")

    if foundation_checks:
        for relative in REQUIRED_FOUNDATION_FILES:
            if not (root / relative).is_file():
                errors.append(f"FOUNDATION_DATEI_FEHLT: {relative}")

        contract = _load_json(root / "PROJECT_CONTRACT.json", errors)
        version = _load_json(root / "VERSION.json", errors)
        status = _load_json(root / "PROJEKTSTATUS.json", errors)
        index = _load_json(root / "standards/STANDARD_INDEX.json", errors)
        documentation = _load_json(root / "standards/DOKUMENTATIONS_STANDARD.json", errors)

        identities = {
            contract.get("contract_id"),
            version.get("project_id"),
            status.get("project_id"),
            manifest.get("project_id"),
        }
        if len(identities - {None}) != 1 or None in identities:
            errors.append(f"PROJEKT_ID_WIDERSPRUCH: {sorted(str(value) for value in identities)}")

        versions = {contract.get("foundation", {}).get("version"), version.get("version"), status.get("version"), manifest.get("version")}
        if len(versions - {None}) != 1 or None in versions:
            errors.append(f"VERSION_WIDERSPRUCH: {sorted(str(value) for value in versions)}")

        iterations = {contract.get("foundation", {}).get("current_iteration"), version.get("iteration"), status.get("iteration"), manifest.get("iteration")}
        if len(iterations - {None}) != 1 or None in iterations:
            errors.append(f"ITERATION_WIDERSPRUCH: {sorted(str(value) for value in iterations)}")

        for entry in index.get("standards", []):
            standard_path = root / entry.get("file", "")
            standard = _load_json(standard_path, errors)
            if standard.get("standard_id") != entry.get("id"):
                errors.append(f"STANDARD_ID_WIDERSPRUCH: {entry.get('file')}")
            if standard.get("version") != entry.get("version"):
                errors.append(f"STANDARD_VERSION_WIDERSPRUCH: {entry.get('file')}")
            if standard.get("status") != "VERBINDLICH":
                errors.append(f"STANDARD_NICHT_VERBINDLICH: {entry.get('file')}")

        readme_path = root / "README.md"
        readme = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
        if version.get("version") and version["version"] not in readme:
            errors.append("README_VERSION_FEHLT")
        for heading in documentation.get("readme_required_headings", []):
            if heading not in readme:
                errors.append(f"README_ABSCHNITT_FEHLT: {heading}")

        todo_path = root / "TODO.md"
        todo = todo_path.read_text(encoding="utf-8") if todo_path.exists() else ""
        for marker in ("## I000 — Foundation", "## I001 — Globale Standards", "vollständige Repository-Dateiliste"):
            if marker not in todo:
                errors.append(f"TODO_INHALT_FEHLT: {marker}")

    return {
        "ok": not errors,
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "expected_files": len(expected),
        "actual_files": len(actual),
    }


def print_result(result: dict[str, Any], json_only: bool = False) -> None:
    if json_only:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return
    print(f"STANDARD-VALIDATOR: {result['status']}")
    print(f"Repository-Dateien: {result['actual_files']}/{result['expected_files']}")
    for error in result["errors"]:
        print(f"FEHLER: {error}")
    for warning in result["warnings"]:
        print(f"WARNUNG: {warning}")
    print("MASCHINENLESBAR:", json.dumps(result, ensure_ascii=False, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description="PROVOWARE Standard- und Repository-Validator")
    parser.add_argument("--root", default=None, help="Repository-Wurzel")
    parser.add_argument("--json", action="store_true", help="nur JSON ausgeben")
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[2]
    result = validate_repository(root)
    print_result(result, json_only=args.json)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
