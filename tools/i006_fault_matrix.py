#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.factory import open_planner_services
from todo_core.errors import InjectedTodoFault


def _count(path: Path, table: str) -> int:
    connection = sqlite3.connect(path)
    try:
        return int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    finally:
        connection.close()


def _with_fault(name: str):
    class FaultContext:
        def __enter__(self):
            self.previous = os.environ.get("PROVOWARE_FAULT_MODE")
            os.environ["PROVOWARE_FAULT_MODE"] = name

        def __exit__(self, exc_type, exc, tb):
            if self.previous is None:
                os.environ.pop("PROVOWARE_FAULT_MODE", None)
            else:
                os.environ["PROVOWARE_FAULT_MODE"] = self.previous
    return FaultContext()


def run_matrix() -> dict:
    results: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="provoware-i006-fault-") as temp:
        path = Path(temp) / "planer.sqlite3"
        services = open_planner_services(path)
        try:
            with _with_fault("TODO_AFTER_INSERT_BEFORE_COMMIT"):
                services.todos.create_todo(title="Rollback-Insert")
        except InjectedTodoFault:
            pass
        results.append({"scenario":"todo_insert_exception_before_commit","pass":_count(path,"todos")==0})

        zone = ZoneInfo("Europe/Berlin")
        start = datetime(2026, 8, 14, 9, 0, tzinfo=zone)
        event = services.calendar.create_event(
            title="Fault-Termin", start_at=start, end_at=start + timedelta(hours=1), timezone_name="Europe/Berlin"
        )
        todo = services.todos.create_todo(title="Fault-Todo")
        try:
            with _with_fault("LINK_AFTER_INSERT_BEFORE_COMMIT"):
                services.links.create_link(todo.todo_id, event.event_id)
        except InjectedTodoFault:
            pass
        results.append({"scenario":"link_insert_exception_before_commit","pass":_count(path,"todo_calendar_links")==0})

        try:
            with _with_fault("TODO_AFTER_SOFT_DELETE_BEFORE_COMMIT"):
                services.todos.delete_todo(todo.todo_id, expected_version=todo.version)
        except InjectedTodoFault:
            pass
        results.append({
            "scenario":"todo_soft_delete_exception_before_commit",
            "pass":services.todos.get_todo(todo.todo_id).deleted_at is None,
        })

        before = _count(path, "todos")
        child_code = """
import os, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from storage.database import Database
path=Path(sys.argv[2])
db=Database(path)
connection=db.connect()
connection.execute('BEGIN IMMEDIATE')
connection.execute("INSERT INTO todos(todo_id,title,description,status,priority,progress,start_at,due_at,parent_id,version,created_at,updated_at,deleted_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", ('crash-row','Crash-Zeile','','OPEN','NORMAL',0,None,None,None,1,'2026-08-14T02:00:00+00:00','2026-08-14T02:00:00+00:00',None))
os._exit(91)
"""
        proc = subprocess.run([sys.executable, "-c", child_code, str(ROOT), str(path)], cwd=ROOT, check=False)
        reopened = open_planner_services(path)
        after = _count(path, "todos")
        reopened.database.quick_check()
        results.append({
            "scenario":"process_exit_before_commit",
            "pass":proc.returncode == 91 and before == after,
            "returncode":proc.returncode,
        })

    return {"status":"PASS" if all(item["pass"] for item in results) else "FAIL", "scenarios":results}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_matrix()
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
