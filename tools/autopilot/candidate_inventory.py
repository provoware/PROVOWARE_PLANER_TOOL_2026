from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
IGNORED_PARTS = {".git", "__pycache__", ".pytest_cache"}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def repository_files(root: Path = ROOT) -> set[str]:
    files: set[str] = set()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in IGNORED_PARTS for part in relative.parts):
            continue
        files.add(relative.as_posix())
    return files


def baseline_manifest(base_commit: str) -> dict[str, Any]:
    raw = _git("show", f"{base_commit}:REPOSITORY_MANIFEST.json")
    return json.loads(raw)


def compute_expected_paths(base_paths: set[str], delta: dict[str, list[str]]) -> tuple[set[str], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    additions = set(delta.get("add", []))
    modifications = set(delta.get("modify", []))
    deletions = set(delta.get("delete", []))

    if additions & modifications or additions & deletions or modifications & deletions:
        errors.append("I013-PLAN-DELTA-001: add/modify/delete müssen disjunkt sein")
    for path in sorted(additions & base_paths):
        errors.append(f"I013-PLAN-DELTA-002: als add deklariert, aber bereits in Baseline: {path}")
    for path in sorted(modifications - base_paths):
        errors.append(f"I013-PLAN-DELTA-003: modify fehlt in Baseline: {path}")
    for path in sorted(deletions - base_paths):
        errors.append(f"I013-PLAN-DELTA-004: delete fehlt in Baseline: {path}")

    expected = (base_paths | additions) - deletions
    return expected, errors, warnings


def changed_paths(base_commit: str) -> set[str]:
    output = _git("diff", "--name-only", f"{base_commit}...HEAD")
    return {line.strip() for line in output.splitlines() if line.strip()}


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    plan = _load_json(root / "ITERATION_PLAN.json")
    base_commit = str(plan.get("base", {}).get("commit", ""))
    if not base_commit:
        return {"status": "FAIL", "errors": ["I013-PLAN-BASE-001: base.commit fehlt"], "warnings": []}

    try:
        _git("cat-file", "-e", f"{base_commit}^{{commit}}")
        base = baseline_manifest(base_commit)
    except Exception as exc:
        return {
            "status": "FAIL",
            "errors": [f"I013-PLAN-BASE-002: Baseline nicht lesbar: {type(exc).__name__}: {exc}"],
            "warnings": [],
        }

    base_paths = set(base.get("files") or base.get("expected_paths") or [])
    expected, delta_errors, delta_warnings = compute_expected_paths(base_paths, plan.get("repository_delta", {}))
    errors.extend(delta_errors)
    warnings.extend(delta_warnings)

    actual = repository_files(root)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    errors.extend(f"I013-INVENTAR-FEHLT: {path}" for path in missing)
    errors.extend(f"I013-INVENTAR-UNGEPLANT: {path}" for path in unexpected)

    declared_changed = set(plan.get("repository_delta", {}).get("add", [])) | set(plan.get("repository_delta", {}).get("modify", [])) | set(plan.get("repository_delta", {}).get("delete", []))
    try:
        actual_changed = changed_paths(base_commit)
    except Exception as exc:
        errors.append(f"I013-DIFF-001: Git-Differenz nicht lesbar: {type(exc).__name__}: {exc}")
        actual_changed = set()
    for path in sorted(actual_changed - declared_changed):
        errors.append(f"I013-DIFF-UNGEPLANT: {path}")
    for path in sorted(declared_changed - actual_changed):
        warnings.append(f"I013-DIFF-NOCH-NICHT-GEAENDERT: {path}")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "base_commit": base_commit,
        "base_file_count": len(base_paths),
        "expected_file_count": len(expected),
        "actual_file_count": len(actual),
        "changed_file_count": len(actual_changed),
        "declared_change_count": len(declared_changed),
        "expected_paths": sorted(expected),
    }


def write_repository_manifest(result: dict[str, Any], root: Path = ROOT) -> None:
    if result.get("status") != "PASS":
        raise RuntimeError("Kandidateninventar ist nicht PASS")
    path = root / "REPOSITORY_MANIFEST.json"
    data = _load_json(path)
    version = _load_json(root / "VERSION.json")
    paths = list(result["expected_paths"])
    data.update(
        project_id="PROVOWARE-PLANER-2026",
        version=version["version"],
        iteration=version["iteration"],
        ignored_path_parts=sorted(IGNORED_PARTS),
        expected_file_count=len(paths),
        files=paths,
        expected_paths=paths,
        full_check_each_iteration=True,
        inventory_source="BASELINE_PLUS_DECLARED_DELTA",
        inventory_base_commit=result["base_commit"],
    )
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Planbasiertes PROVOWARE-Kandidateninventar")
    parser.add_argument("--write-manifest", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = validate()
    if args.write_manifest and result["status"] == "PASS":
        write_repository_manifest(result)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(f"KANDIDATEN-INVENTAR: {result['status']}")
        print(f"Dateien: {result.get('actual_file_count', 0)}/{result.get('expected_file_count', 0)}")
        for error in result.get("errors", []):
            print(f"FEHLER: {error}")
        for warning in result.get("warnings", []):
            print(f"WARNUNG: {warning}")
        print("MASCHINENLESBAR:", json.dumps({k: v for k, v in result.items() if k != "expected_paths"}, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
