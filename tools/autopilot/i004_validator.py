from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storage.database import Database
from storage.migrations import MigrationRunner
from storage.repository import CalendarRepository

REQUIRED_FILES = {
    "calendar_core/__init__.py",
    "calendar_core/errors.py",
    "calendar_core/model.py",
    "contracts/CALENDAR_DATA_CONTRACT.json",
    "errors/KALENDER_FEHLERKATALOG.json",
    "migrations/0001_calendar_core.sql",
    "services/__init__.py",
    "services/calendar_service.py",
    "storage/__init__.py",
    "storage/backup.py",
    "storage/database.py",
    "storage/migrations.py",
    "storage/repository.py",
    "tests/test_i004_calendar_core.py",
    "tests/test_i004_fault_injection.py",
    "docs/I004_KALENDER_DOMAIN_SQLITE.md",
}
SOURCE_DIRS = ("calendar_core", "storage", "services")
CODE_PATTERN = re.compile(r"CAL-[A-Z0-9-]+-\d{3}")


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def repository_files() -> set[str]:
    return {
        str(path.relative_to(ROOT))
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and "__pycache__" not in path.parts
        and ".pytest_cache" not in path.parts
    }


def catalog_codes() -> tuple[set[str], list[str]]:
    all_codes: list[str] = []
    for path in sorted((ROOT / "errors").glob("*FEHLERKATALOG.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        all_codes.extend(str(item.get("code")) for item in data.get("errors", []))
    duplicates = sorted({code for code in all_codes if all_codes.count(code) > 1})
    return set(all_codes), duplicates


def used_calendar_codes() -> set[str]:
    codes: set[str] = set()
    for directory in SOURCE_DIRS:
        for path in (ROOT / directory).rglob("*.py"):
            codes.update(CODE_PATTERN.findall(path.read_text(encoding="utf-8")))
    return codes


def validate() -> dict:
    errors: list[str] = []
    files = repository_files()
    for path in sorted(REQUIRED_FILES - files):
        errors.append(f"I004_DATEI_FEHLT: {path}")

    version = load("VERSION.json")
    status = load("PROJEKTSTATUS.json")
    project = load("PROJECT_CONTRACT.json")
    contract = load("contracts/CALENDAR_DATA_CONTRACT.json")

    if version.get("iteration") != "I004" or version.get("version") != "0.4.0-dev.1":
        errors.append("I004_VERSION_NICHT_PROMOVIERT")
    if status.get("iteration") != "I004":
        errors.append("I004_STATUS_NICHT_PROMOVIERT")
    if project.get("foundation", {}).get("current_iteration") != "I004":
        errors.append("I004_PROJEKTVERTRAG_NICHT_PROMOVIERT")
    if contract.get("status") != "VERBINDLICH":
        errors.append("I004_KALENDERVERTRAG_NICHT_VERBINDLICH")

    domain = contract.get("domain", {})
    sqlite_contract = contract.get("sqlite", {})
    migrations = contract.get("migrations", {})
    restore = contract.get("backup_restore", {})
    gui_boundary = contract.get("gui_boundary", {})
    required_true = [
        domain.get("soft_delete_required"),
        sqlite_contract.get("foreign_keys"),
        sqlite_contract.get("quick_check_required"),
        sqlite_contract.get("transactional_writes_only"),
        migrations.get("sha256_bound"),
        migrations.get("backup_before_apply"),
        migrations.get("rollback_on_failure"),
        restore.get("candidate_validation"),
        restore.get("atomic_promotion"),
        restore.get("wal_checkpoint_before_restore"),
        gui_boundary.get("gui_uses_service_api_only"),
    ]
    if not all(value is True for value in required_true):
        errors.append("I004_DATENSICHERHEITSVERTRAG_UNVOLLSTAENDIG")
    if gui_boundary.get("gui_may_execute_sql") is not False:
        errors.append("I004_GUI_SQL_GRENZE_FEHLT")

    catalogs, duplicates = catalog_codes()
    if duplicates:
        errors.append(f"I004_FEHLERCODE_DOPPELT: {duplicates}")
    missing_codes = sorted(used_calendar_codes() - catalogs)
    if missing_codes:
        errors.append(f"I004_FEHLERCODE_NICHT_KATALOGISIERT: {missing_codes}")

    for directory in SOURCE_DIRS:
        for path in (ROOT / directory).rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if "PySide6" in text or "PyQt" in text:
                errors.append(f"I004_GUI_ABHAENGIGKEIT_IM_DATENKERN: {path.relative_to(ROOT)}")
    service_text = (ROOT / "services/calendar_service.py").read_text(encoding="utf-8")
    if "sqlite3" in service_text or "SELECT " in service_text or "INSERT " in service_text:
        errors.append("I004_SERVICE_ENTHAELT_SQL")

    migration_sql = (ROOT / "migrations/0001_calendar_core.sql").read_text(encoding="utf-8")
    for token in ("marker_types", "calendar_events", "FOREIGN KEY", "deleted_at", "version"):
        if token not in migration_sql:
            errors.append(f"I004_SCHEMA_BESTANDTEIL_FEHLT: {token}")

    runtime_result = "NOT_RUN"
    try:
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            database = Database(temp_root / "planner.sqlite3")
            runner = MigrationRunner(database, ROOT / "migrations")
            applied = runner.apply_all()
            runner.verify_history()
            database.quick_check()
            markers = CalendarRepository(database).marker_types()
            backup = temp_root / "backups" / "pre_migration_v0001.sqlite3"
            if applied != [1]:
                errors.append(f"I004_MIGRATION_UNERWARTET: {applied}")
            if database.schema_version() != 1:
                errors.append("I004_SCHEMA_VERSION_FALSCH")
            if len(markers) != 5:
                errors.append("I004_MARKER_ANZAHL_FALSCH")
            if not backup.is_file() or not backup.with_suffix(backup.suffix + ".json").is_file():
                errors.append("I004_VOR_MIGRATIONS_BACKUP_FEHLT")
            runtime_result = "PASS"
    except Exception as exc:
        errors.append(f"I004_RUNTIME_VALIDIERUNG_FEHLER: {type(exc).__name__}: {exc}")
        runtime_result = "FAIL"

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "repository_files": len(files),
        "calendar_error_codes_used": len(used_calendar_codes()),
        "calendar_error_codes_registered": len(used_calendar_codes() & catalogs),
        "schema_runtime": runtime_result,
    }


def main() -> int:
    result = validate()
    print(f"I004-VALIDATOR: {result['status']}")
    print(f"Kalender-Fehlercodes: {result['calendar_error_codes_registered']}/{result['calendar_error_codes_used']}")
    print(f"Schema-Runtime: {result['schema_runtime']}")
    for error in result["errors"]:
        print(f"FEHLER: {error}")
    print("MASCHINENLESBAR:", json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
