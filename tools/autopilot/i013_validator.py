from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = {
    "ITERATION_PLAN.json",
    "PROCESS_AUDIT_I012.json",
    "contracts/DEVELOPMENT_PIPELINE_CONTRACT.json",
    "standards/ENTWICKLUNGS_STANDARD.json",
    "tools/autopilot/candidate_inventory.py",
    "tools/autopilot/preflight.py",
    "tests/test_i013_candidate_inventory.py",
    "tests/test_i013_preflight.py",
    "docs/I013_ENTWICKLUNGSAUTOPILOT_V2.md",
    ".github/workflows/i013-qualifikation.yml",
}


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _iteration(value: object) -> int:
    try:
        return int(str(value).removeprefix("I"))
    except ValueError:
        return 0


def repository_files() -> set[str]:
    return {
        str(path.relative_to(ROOT))
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and "__pycache__" not in path.parts
        and ".pytest_cache" not in path.parts
        and "dist_transport" not in path.parts
    }


def validate() -> dict:
    errors: list[str] = []
    files = repository_files()
    for path in sorted(REQUIRED_FILES - files):
        errors.append(f"I013_DATEI_FEHLT: {path}")

    version = load("VERSION.json")
    status = load("PROJEKTSTATUS.json")
    project = load("PROJECT_CONTRACT.json")
    standard = load("standards/ENTWICKLUNGS_STANDARD.json")
    contract = load("contracts/DEVELOPMENT_PIPELINE_CONTRACT.json")
    plan = load("ITERATION_PLAN.json")
    audit = load("PROCESS_AUDIT_I012.json")

    current = _iteration(version.get("iteration"))
    if current < 13:
        errors.append("I013_VERSION_UNTER_MINDESTSTAND")
    if current == 13 and version.get("version") != "0.13.0-dev.1":
        errors.append("I013_VERSION_FALSCH")
    if _iteration(status.get("iteration")) < 13:
        errors.append("I013_STATUS_UNTER_MINDESTSTAND")
    if _iteration(project.get("foundation", {}).get("current_iteration")) < 13:
        errors.append("I013_PROJEKTVERTRAG_UNTER_MINDESTSTAND")

    if standard.get("standard_id") != "PROVOWARE-DEVELOPMENT" or standard.get("version") != "2.0.0":
        errors.append("I013_ENTWICKLUNGSSTANDARD_FALSCH")
    rules = standard.get("rules", {})
    for key in (
        "machine_readable_iteration_plan_required",
        "explicit_repository_delta_required",
        "static_preflight_before_runtime_dependency_install_required",
        "fail_fast_cost_order_required",
        "duplicate_gate_execution_within_same_pass_forbidden",
        "candidate_inventory_must_derive_from_baseline_plus_declared_delta",
        "exact_sha_second_pass_required_for_qualification",
        "second_pass_repository_write_forbidden",
        "fast_forward_promotion_required",
        "post_promotion_independent_check_required",
    ):
        if rules.get(key) is not True:
            errors.append(f"I013_STANDARDREGEL_FEHLT: {key}")

    if contract.get("precision_guards", {}).get("repository_expected_paths_source") != "BASELINE_PLUS_DECLARED_DELTA":
        errors.append("I013_PIPELINE_SOLLQUELLE_FALSCH")
    if contract.get("efficiency_guards", {}).get("same_gate_once_per_pass") is not True:
        errors.append("I013_PIPELINE_DEDUP_FEHLT")
    stages = [stage.get("id") for stage in contract.get("stages", [])]
    if stages != ["P0_STATIC", "P1_PLAN_AND_TARGET", "P2_RUNTIME_TARGET", "P3_REGRESSION", "P4_EVIDENCE", "P5_PROMOTION"]:
        errors.append("I013_PIPELINE_STUFEN_FALSCH")

    criteria = {item.get("id") for item in plan.get("acceptance_criteria", [])}
    if current == 13:
        if plan.get("base", {}).get("commit") != "f2e12bde3f4a6e3d8cd490018fb5e101819d281b":
            errors.append("I013_BASELINE_FALSCH")
        if plan.get("risk_class") != "HOCH":
            errors.append("I013_RISIKOKLASSE_FALSCH")
        if criteria != {f"I013-A0{number}" for number in range(1, 9)}:
            errors.append("I013_AKZEPTANZKRITERIEN_UNVOLLSTAENDIG")
    else:
        if plan.get("iteration") != version.get("iteration"):
            errors.append("I013_FOLGEPLAN_ITERATION_WIDERSPRUCH")
        if plan.get("version") != version.get("version"):
            errors.append("I013_FOLGEPLAN_VERSION_WIDERSPRUCH")
        if plan.get("risk_class") not in {"NIEDRIG", "MITTEL", "HOCH"}:
            errors.append("I013_FOLGEPLAN_RISIKOKLASSE_FEHLT")
        if not criteria:
            errors.append("I013_FOLGEPLAN_AKZEPTANZKRITERIEN_FEHLEN")
        delta = plan.get("repository_delta", {})
        if not all(key in delta for key in ("add", "modify", "delete")):
            errors.append("I013_FOLGEPLAN_REPOSITORY_DELTA_FEHLT")

    if audit.get("observed_remote_runs", {}).get("failed_before_success") != 2:
        errors.append("I013_AUDIT_FEHLERZAHL_FALSCH")
    if audit.get("target_state_i013", {}).get("unplanned_repository_paths_target") != 0:
        errors.append("I013_AUDIT_ZIEL_FALSCH")

    candidate_source = (ROOT / "tools/autopilot/candidate_inventory.py").read_text(encoding="utf-8") if (ROOT / "tools/autopilot/candidate_inventory.py").exists() else ""
    for token in ("BASELINE_PLUS_DECLARED_DELTA", "changed_paths", "write_repository_manifest", "I013-INVENTAR-UNGEPLANT"):
        if token not in candidate_source:
            errors.append(f"I013_INVENTARWERKZEUG_FEHLT: {token}")

    preflight_source = (ROOT / "tools/autopilot/preflight.py").read_text(encoding="utf-8") if (ROOT / "tools/autopilot/preflight.py").exists() else ""
    for token in ("P0_STATIC", "py_compile", "readme_required_section_markers", "validate_candidate_inventory"):
        if token not in preflight_source:
            errors.append(f"I013_PREFLIGHT_WERKZEUG_FEHLT: {token}")

    workflow = (ROOT / ".github/workflows/i013-qualifikation.yml").read_text(encoding="utf-8") if (ROOT / ".github/workflows/i013-qualifikation.yml").exists() else ""
    for token in (
        "concurrency:",
        "cancel-in-progress: true",
        "preflight.py",
        "candidate_inventory.py --write-manifest",
        "cache: 'pip'",
        "verify_only",
        "verify_sha",
    ):
        if token not in workflow:
            errors.append(f"I013_WORKFLOW_HAERTUNG_FEHLT: {token}")
    if workflow.count("unittest discover -s tests -p 'test_*.py'") != 1:
        errors.append("I013_FULL_SUITE_NICHT_GENAU_EINMAL")
    if workflow.count("autopilot.py qualifizieren") != 1:
        errors.append("I013_HISTORISCHE_KETTE_NICHT_GENAU_EINMAL")
    if workflow.find("preflight.py") > workflow.find("apt-get") >= 0:
        errors.append("I013_PREFLIGHT_ZU_SPAET")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "repository_files": len(files),
        "acceptance_criteria": len(criteria),
        "risk_class": plan.get("risk_class"),
        "gate_execution_model": "ONE_GATE_ONCE_PER_PASS",
        "forward_compatible_plan_check": current > 13,
    }


def main() -> int:
    result = validate()
    print(f"I013-VALIDATOR: {result['status']}")
    print(f"Akzeptanzkriterien: {result['acceptance_criteria']} | Risiko: {result['risk_class']}")
    print(f"Gate-Modell: {result['gate_execution_model']}")
    for error in result["errors"]:
        print(f"FEHLER: {error}")
    print("MASCHINENLESBAR:", json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
