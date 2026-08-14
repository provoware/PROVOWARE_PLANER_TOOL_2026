#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.factory import open_planner_services
from services.restore_service import RestoreService
from storage.backup import create_backup


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare(root: Path) -> tuple[Path, Path, Path]:
    workspace = root / "workspace"
    backups = workspace / "Sicherungen"
    backups.mkdir(parents=True, exist_ok=True)
    target = workspace / "planer.sqlite3"
    services = open_planner_services(target, backup_dir=backups / "migrationen")
    backup = backups / "stand.sqlite3"
    create_backup(services.database, backup)
    connection = sqlite3.connect(target)
    try:
        connection.execute("CREATE TABLE newer_state(id INTEGER PRIMARY KEY, value TEXT)")
        connection.execute("INSERT INTO newer_state(value) VALUES ('before')")
        connection.commit()
    finally:
        connection.close()
    return backups, backup, target


def crash_child(root: Path) -> int:
    backups = root / "workspace" / "Sicherungen"
    backup = backups / "stand.sqlite3"
    target = root / "workspace" / "planer.sqlite3"

    def fault(point: str) -> None:
        if point == "physical_core_precheck":
            os._exit(91)

    service = RestoreService(backup_root=backups, target_database=target, fault_hook=fault)
    service.commit_restore(service.prepare_restore(backup))
    return 99


def run_matrix() -> dict:
    scenarios: list[dict] = []

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        backups, backup, target = prepare(root)
        before = sha256(target)

        def pre_fault(point: str) -> None:
            if point == "physical_core_precheck":
                raise RuntimeError("precheck")

        service = RestoreService(backup_root=backups, target_database=target, fault_hook=pre_fault)
        plan = service.prepare_restore(backup)
        try:
            service.commit_restore(plan)
            passed = False
        except RuntimeError:
            passed = sha256(target) == before
        scenarios.append({"id": "exception_before_physical_write", "status": "PASS" if passed else "FAIL"})

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        backups, backup, target = prepare(root)
        before = sha256(target)

        def post_fault(point: str) -> None:
            if point == "after_replace_before_postcheck":
                raise RuntimeError("postcheck")

        service = RestoreService(backup_root=backups, target_database=target, fault_hook=post_fault)
        plan = service.prepare_restore(backup)
        try:
            service.commit_restore(plan)
            passed = False
        except RuntimeError:
            passed = sha256(target) == before
        scenarios.append({"id": "exception_after_replace_rolls_back", "status": "PASS" if passed else "FAIL"})

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        backups, backup, target = prepare(root)
        before = sha256(target)
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--crash-child", str(root)], check=False)
        passed = proc.returncode == 91 and sha256(target) == before
        scenarios.append({"id": "process_exit_before_physical_write", "return_code": proc.returncode, "status": "PASS" if passed else "FAIL"})

    result = {"schema_version": 1, "iteration": "I015", "scenarios": scenarios}
    result["status"] = "PASS" if all(item["status"] == "PASS" for item in scenarios) else "FAIL"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--crash-child", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.crash_child:
        return crash_child(args.crash_child)
    result = run_matrix()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
