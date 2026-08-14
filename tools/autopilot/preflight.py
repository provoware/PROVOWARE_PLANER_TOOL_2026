from __future__ import annotations

import argparse
import json
import py_compile
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.autopilot.candidate_inventory import validate as validate_candidate_inventory


def _load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"P0-DATEI-FEHLT: {path.relative_to(ROOT).as_posix()}")
    except json.JSONDecodeError as exc:
        errors.append(f"P0-JSON-001: {path.relative_to(ROOT).as_posix()} Zeile {exc.lineno}: {exc.msg}")
    return {}


def _validate_all_json(errors: list[str]) -> int:
    count = 0
    for path in sorted(ROOT.rglob("*.json")):
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        count += 1
        _load_json(path, errors)
    return count


def _validate_python_syntax(errors: list[str]) -> int:
    count = 0
    for path in sorted(ROOT.rglob("*.py")):
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        count += 1
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f"P0-PYTHON-001: {path.relative_to(ROOT).as_posix()}: {exc.msg}")
    return count


def _validate_metadata(errors: list[str]) -> None:
    version = _load_json(ROOT / "VERSION.json", errors)
    status = _load_json(ROOT / "PROJEKTSTATUS.json", errors)
    project = _load_json(ROOT / "PROJECT_CONTRACT.json", errors)
    plan = _load_json(ROOT / "ITERATION_PLAN.json", errors)
    values = {
        "version.VERSION": version.get("version"),
        "status.VERSION": status.get("version"),
        "project.VERSION": project.get("foundation", {}).get("version"),
        "plan.VERSION": plan.get("version"),
    }
    if len(set(values.values())) != 1:
        errors.append(f"P0-METADATA-001: Versionswiderspruch {values}")
    iterations = {
        "version.ITERATION": version.get("iteration"),
        "status.ITERATION": status.get("iteration"),
        "project.ITERATION": project.get("foundation", {}).get("current_iteration"),
        "plan.ITERATION": plan.get("iteration"),
    }
    if len(set(iterations.values())) != 1:
        errors.append(f"P0-METADATA-002: Iterationswiderspruch {iterations}")
    checkpoints = {
        version.get("checkpoint"),
        status.get("checkpoint"),
        project.get("foundation", {}).get("current_checkpoint"),
        plan.get("checkpoint"),
    }
    if len(checkpoints) != 1:
        errors.append(f"P0-METADATA-003: Checkpoint-Widerspruch {sorted(str(v) for v in checkpoints)}")


def _validate_standards(errors: list[str]) -> int:
    index = _load_json(ROOT / "standards" / "STANDARD_INDEX.json", errors)
    count = 0
    for entry in index.get("standards", []):
        count += 1
        relative = str(entry.get("file", ""))
        standard = _load_json(ROOT / relative, errors)
        if standard.get("standard_id") != entry.get("id"):
            errors.append(f"P0-STANDARD-001: ID-Widerspruch {relative}")
        if standard.get("version") != entry.get("version"):
            errors.append(f"P0-STANDARD-002: Versionswiderspruch {relative}")
        if standard.get("status") != "VERBINDLICH":
            errors.append(f"P0-STANDARD-003: nicht verbindlich {relative}")
    return count


def _validate_documentation(errors: list[str]) -> None:
    standard = _load_json(ROOT / "standards" / "DOKUMENTATIONS_STANDARD.json", errors)
    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
    markers = standard.get("readme_required_section_markers", [])
    if markers:
        for marker in markers:
            if marker not in readme:
                errors.append(f"P0-DOKU-001: README-Abschnittsmarker fehlt: {marker}")
    else:
        for heading in standard.get("readme_required_headings", []):
            if heading not in readme:
                errors.append(f"P0-DOKU-ALT-001: README-Abschnitt fehlt: {heading}")


def _validate_pipeline_contract(errors: list[str]) -> None:
    contract = _load_json(ROOT / "contracts" / "DEVELOPMENT_PIPELINE_CONTRACT.json", errors)
    stage_ids = [stage.get("id") for stage in contract.get("stages", [])]
    expected = ["P0_STATIC", "P1_PLAN_AND_TARGET", "P2_RUNTIME_TARGET", "P3_REGRESSION", "P4_EVIDENCE", "P5_PROMOTION"]
    if stage_ids != expected:
        errors.append(f"P0-PIPELINE-001: Stufenfolge falsch: {stage_ids}")
    if contract.get("precision_guards", {}).get("repository_expected_paths_source") != "BASELINE_PLUS_DECLARED_DELTA":
        errors.append("P0-PIPELINE-002: planbasiertes Repository-Soll fehlt")
    if contract.get("efficiency_guards", {}).get("static_preflight_before_apt_or_pip") is not True:
        errors.append("P0-PIPELINE-003: Static-first-Regel fehlt")
    if contract.get("efficiency_guards", {}).get("same_gate_once_per_pass") is not True:
        errors.append("P0-PIPELINE-004: Gate-Deduplizierung fehlt")


def _validate_workflow_guards(errors: list[str]) -> None:
    version = _load_json(ROOT / "VERSION.json", errors)
    try:
        current = int(str(version.get("iteration", "I000")).removeprefix("I"))
    except ValueError:
        current = 0
    if current < 13:
        return
    workflow = ROOT / ".github" / "workflows" / "i013-qualifikation.yml"
    if not workflow.exists():
        errors.append("P0-CI-001: I013-Workflow fehlt")
        return
    text = workflow.read_text(encoding="utf-8")
    for token in ("concurrency:", "cancel-in-progress: true", "cache: 'pip'", "candidate_inventory.py", "preflight.py"):
        if token not in text:
            errors.append(f"P0-CI-002: Workflow-Härtung fehlt: {token}")
    preflight_pos = text.find("preflight.py")
    apt_pos = text.find("apt-get")
    pip_pos = text.find("pip install")
    if preflight_pos < 0 or (apt_pos >= 0 and preflight_pos > apt_pos) or (pip_pos >= 0 and preflight_pos > pip_pos):
        errors.append("P0-CI-003: Preflight läuft nicht vor Runtime-Setup")


def validate() -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    json_count = _validate_all_json(errors)
    python_count = _validate_python_syntax(errors)
    _validate_metadata(errors)
    standard_count = _validate_standards(errors)
    _validate_documentation(errors)
    _validate_pipeline_contract(errors)
    _validate_workflow_guards(errors)

    inventory = validate_candidate_inventory()
    errors.extend(inventory.get("errors", []))
    warnings.extend(inventory.get("warnings", []))

    return {
        "status": "PASS" if not errors else "FAIL",
        "stage": "P0_STATIC",
        "errors": errors,
        "warnings": warnings,
        "json_files_checked": json_count,
        "python_files_compiled": python_count,
        "standards_checked": standard_count,
        "candidate_inventory_status": inventory.get("status"),
        "candidate_expected_files": inventory.get("expected_file_count"),
        "candidate_actual_files": inventory.get("actual_file_count"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="PROVOWARE P0 Static Preflight")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = validate()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(f"P0-STATIC-PREFLIGHT: {result['status']}")
        print(f"JSON: {result['json_files_checked']} | Python-Syntax: {result['python_files_compiled']} | Standards: {result['standards_checked']}")
        for error in result["errors"]:
            print(f"FEHLER: {error}")
        for warning in result["warnings"]:
            print(f"WARNUNG: {warning}")
        print("MASCHINENLESBAR:", json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
