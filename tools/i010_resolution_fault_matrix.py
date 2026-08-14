#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.factory import open_planner_services
from services.resolution_service import ResolutionService
from sync_core.errors import InjectedSyncFault
from sync_core.resolution import ResolutionChoice
from todo_core.model import LinkDirection


FAULTS = (
    "SYNC_AFTER_ENTITY_WRITE",
    "SYNC_AFTER_BASELINE_WRITE",
    "SYNC_BEFORE_RECEIPT",
    "SYNC_AFTER_RECEIPT_BEFORE_COMMIT",
)


def _seed(database_path: Path) -> tuple[str, str, str]:
    services = open_planner_services(database_path)
    zone = ZoneInfo("Europe/Berlin")
    start = datetime(2026, 8, 14, 14, 0, tzinfo=zone)
    end = start + timedelta(hours=1)
    todo = services.todos.create_todo(title="Basis", description="Text", start_at=start, due_at=end)
    event = services.calendar.create_event(
        title="Basis", description="Text", start_at=start, end_at=end, timezone_name="Europe/Berlin"
    )
    link = services.links.create_link(todo.todo_id, event.event_id, direction=LinkDirection.BIDIRECTIONAL)
    services.sync.initialize_baseline(link.link_id)
    services.todos.update_todo(replace(todo, title="Todo gewinnt"), expected_version=todo.version)
    services.calendar.update_event(replace(event, title="Kalender verliert"), expected_version=event.version)
    return link.link_id, todo.todo_id, event.event_id


def _resolution(services, link_id: str):
    resolver = ResolutionService(services.sync, services.sync.repository)
    source = services.sync.plan(link_id)
    return resolver, resolver.build(source, {"TITLE": ResolutionChoice.TODO_VALUE})


def _verify_rolled_back(database_path: Path, link_id: str, todo_id: str, event_id: str) -> bool:
    services = open_planner_services(database_path)
    todo = services.todos.get_todo(todo_id)
    event = services.calendar.get_event(event_id)
    source = services.sync.plan(link_id)
    services.database.quick_check()
    return (
        todo.title == "Todo gewinnt"
        and event.title == "Kalender verliert"
        and source.state.value == "BLOCKED_CONFLICT"
        and services.sync.receipt_count(link_id) == 0
    )


def _exception_scenario(name: str) -> dict:
    with tempfile.TemporaryDirectory(prefix=f"provoware-i010-{name.lower()}-") as temp:
        database_path = Path(temp) / "planer.sqlite3"
        link_id, todo_id, event_id = _seed(database_path)
        services = open_planner_services(database_path)
        resolver, plan = _resolution(services, link_id)
        old_enabled = os.environ.get("PROVOWARE_SYNC_FAULTS")
        old_fault = os.environ.get("PROVOWARE_SYNC_FAULT_MODE")
        os.environ["PROVOWARE_SYNC_FAULTS"] = "1"
        os.environ["PROVOWARE_SYNC_FAULT_MODE"] = name
        caught = False
        try:
            resolver.commit(plan)
        except InjectedSyncFault:
            caught = True
        finally:
            if old_enabled is None:
                os.environ.pop("PROVOWARE_SYNC_FAULTS", None)
            else:
                os.environ["PROVOWARE_SYNC_FAULTS"] = old_enabled
            if old_fault is None:
                os.environ.pop("PROVOWARE_SYNC_FAULT_MODE", None)
            else:
                os.environ["PROVOWARE_SYNC_FAULT_MODE"] = old_fault
        return {
            "scenario": name,
            "pass": caught and _verify_rolled_back(database_path, link_id, todo_id, event_id),
        }


def _crash_child(database_path: Path, link_id: str) -> int:
    services = open_planner_services(database_path)
    resolver, plan = _resolution(services, link_id)
    resolver.commit(plan)
    return 0


def _crash_scenario() -> dict:
    with tempfile.TemporaryDirectory(prefix="provoware-i010-process-crash-") as temp:
        database_path = Path(temp) / "planer.sqlite3"
        link_id, todo_id, event_id = _seed(database_path)
        env = os.environ.copy()
        env["PROVOWARE_SYNC_FAULTS"] = "1"
        env["PROVOWARE_SYNC_CRASH_MODE"] = "SYNC_AFTER_ENTITY_WRITE"
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--child", str(database_path), link_id],
            env=env,
            check=False,
        )
        return {
            "scenario": "RESOLUTION_PROCESS_EXIT_AFTER_ENTITY_WRITE",
            "returncode": result.returncode,
            "pass": result.returncode == 92
            and _verify_rolled_back(database_path, link_id, todo_id, event_id),
        }


def run_matrix() -> dict:
    scenarios = [_exception_scenario(name) for name in FAULTS]
    scenarios.append(_crash_scenario())
    return {"status": "PASS" if all(item["pass"] for item in scenarios) else "FAIL", "scenarios": scenarios}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--child", nargs=2, metavar=("DATABASE", "LINK_ID"))
    args = parser.parse_args()
    if args.child:
        return _crash_child(Path(args.child[0]), args.child[1])
    result = run_matrix()
    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
