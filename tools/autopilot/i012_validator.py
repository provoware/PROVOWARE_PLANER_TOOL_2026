from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REQUIRED_FILES = {
    "contracts/DIAGNOSTICS_DASHBOARD_CONTRACT.json",
    "diagnostics_core/model.py",
    "services/diagnostics_service.py",
    "viewmodel/diagnostics_viewmodel.py",
    "ui/diagnostics_window.py",
    "tests/test_i012_diagnostics_service.py",
    "tests/test_i012_diagnostics_gui.py",
    "tools/i012_diagnostics_gui_matrix.py",
    "docs/I012_DIAGNOSE_DASHBOARD.md",
    ".github/workflows/i012-qualifikation.yml",
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
    }


def validate() -> dict:
    errors: list[str] = []
    files = repository_files()
    for path in sorted(REQUIRED_FILES - files):
        errors.append(f"I012_DATEI_FEHLT: {path}")

    version = load("VERSION.json")
    status = load("PROJEKTSTATUS.json")
    project = load("PROJECT_CONTRACT.json")
    contract = load("contracts/DIAGNOSTICS_DASHBOARD_CONTRACT.json")
    current = _iteration(version.get("iteration"))
    if current < 12:
        errors.append("I012_VERSION_UNTER_MINDESTSTAND")
    if current == 12 and version.get("version") != "0.12.0-dev.1":
        errors.append("I012_VERSION_FALSCH")
    if _iteration(status.get("iteration")) < 12:
        errors.append("I012_STATUS_UNTER_MINDESTSTAND")
    if _iteration(project.get("foundation", {}).get("current_iteration")) < 12:
        errors.append("I012_PROJEKTVERTRAG_UNTER_MINDESTSTAND")
    if contract.get("status") != "VERBINDLICH" or contract.get("mode") != "READ_ONLY_DIAGNOSTIC_AGGREGATION":
        errors.append("I012_VERTRAG_ODER_MODUS_FALSCH")

    expected_areas = ["STARTZUSTAND", "SQLITE_INTEGRITAET", "JOURNAL_INTEGRITAET", "BACKUP_NACHWEISE", "RECOVERY_BLOCKADEN"]
    if contract.get("areas") != expected_areas:
        errors.append("I012_DIAGNOSEBEREICHE_FALSCH")

    safety = contract.get("safety", {})
    for key in (
        "dashboard_may_execute_sql_write",
        "dashboard_may_run_migrations",
        "dashboard_may_restore_backup",
        "dashboard_may_commit_recovery",
        "dashboard_may_commit_sync",
        "dashboard_may_repair_data",
        "dashboard_may_modify_user_data",
    ):
        if safety.get(key) is not False:
            errors.append(f"I012_WRITEVERBOT_FEHLT: {key}")
    for key in (
        "blocked_recovery_is_information_not_auto_action",
        "tampered_journal_is_hard_red",
        "missing_optional_evidence_is_yellow",
        "color_never_only_signal",
    ):
        if safety.get(key) is not True:
            errors.append(f"I012_SICHERHEITSREGEL_FEHLT: {key}")

    service_source = (ROOT / "services/diagnostics_service.py").read_text(encoding="utf-8")
    for token in ("mode=ro", "PRAGMA query_only", "quick_check", "list_records", "build_recovery"):
        if token not in service_source:
            errors.append(f"I012_READONLY_HAERTUNG_FEHLT: {token}")
    for forbidden in ("restore_backup", "commit_recovery(", "sync_service.commit(", "MigrationRunner", "BEGIN IMMEDIATE"):
        if forbidden in service_source:
            errors.append(f"I012_VERBOTENER_AKTIONSPFAD: {forbidden}")

    ui_source = (ROOT / "ui/diagnostics_window.py").read_text(encoding="utf-8")
    for token in ("Startzustand", "Datenbank", "Synchronisationsjournal", "Sicherungen", "Recovery-Pläne", "Erneut prüfen"):
        if token not in ui_source:
            errors.append(f"I012_GUI_BESTANDTEIL_FEHLT: {token}")
    for forbidden in ("restore_backup", "commit_recovery", "sqlite3", "MigrationRunner"):
        if forbidden in ui_source:
            errors.append(f"I012_GUI_GRENZE_VERLETZT: {forbidden}")

    expected_chain = ["I002", "I003", "I004", "I005", "I006", "I007", "I008", "I009", "I010", "I011", "I012"]
    if contract.get("qualification", {}).get("historical_gate_chain") != expected_chain:
        errors.append("I012_HISTORISCHE_KETTE_FALSCH")

    runtime = "NOT_RUN"
    try:
        from diagnostics_core.model import DiagnosisState
        from services.diagnostics_service import DiagnosticsService
        from services.factory import open_planner_services

        with tempfile.TemporaryDirectory(prefix="provoware-i012-validator-") as temp:
            workspace = Path(temp)
            services = open_planner_services(workspace / "planer.sqlite3")
            snapshot = DiagnosticsService(
                services.database,
                services.journal,
                workspace=workspace,
            ).snapshot()
            if {item.item_id for item in snapshot.items} != {"START", "DATABASE", "JOURNAL", "BACKUP", "RECOVERY"}:
                errors.append("I012_RUNTIME_BEREICHE_FEHLEN")
            if snapshot.item("DATABASE").state is not DiagnosisState.READY:
                errors.append("I012_RUNTIME_DATENBANK_NICHT_BEREIT")
            if snapshot.item("START").state is DiagnosisState.BLOCKED:
                errors.append("I012_RUNTIME_FEHLENDER_STARTBERICHT_FALSCH_ROT")
            if services.database.schema_version() < 4:
                errors.append("I012_RUNTIME_SCHEMA_UNTER_I011")
            runtime = "PASS"
    except Exception as exc:
        errors.append(f"I012_RUNTIME_FEHLER: {type(exc).__name__}: {exc}")
        runtime = "FAIL"

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "repository_files": len(files),
        "runtime": runtime,
        "database_schema_minimum": 4,
    }


def main() -> int:
    result = validate()
    print(f"I012-VALIDATOR: {result['status']}")
    print(f"Runtime: {result['runtime']}")
    print(f"Repository-Dateien: {result['repository_files']}")
    for error in result["errors"]:
        print(f"FEHLER: {error}")
    print("MASCHINENLESBAR:", json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
