#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.faults import FAULTS, RuntimeContext
from runtime.orchestrator import StartOrchestrator


def run_once(workspace: Path, faults: set[str], allow_fault_injection: bool) -> dict:
    ctx = RuntimeContext(
        repo_root=ROOT,
        workspace=workspace,
        faults=faults,
        allow_fault_injection=allow_fault_injection,
    )
    return StartOrchestrator(ctx).run().to_dict()


def main() -> int:
    parser = argparse.ArgumentParser(description="PROVOWARE Klick-&-Start-Orchestrator I003")
    parser.add_argument("--workspace", default=os.environ.get("PROVOWARE_WORKSPACE"))
    parser.add_argument("--fault", action="append", default=[], choices=sorted(FAULTS))
    parser.add_argument("--allow-fault-injection", action="store_true")
    parser.add_argument("--json-report")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    workspace = (
        Path(args.workspace).expanduser().resolve()
        if args.workspace
        else Path.home() / ".local" / "share" / "provoware-planer-tool-2026"
    )
    report = run_once(workspace, set(args.fault), args.allow_fault_injection)

    if args.json_report:
        Path(args.json_report).write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        print("PROVOWARE KLICK-&-START I003")
        print(f"Status: {report['state']}")
        print(report["user_summary"])
        for step in report["steps"]:
            print(f"- {step['title']}: {step['final_status']}")
            for item in step["phases"]:
                print(f"  {item['phase']}: {item['status']} — {item['user_message']}")
                if item["technical_details"]:
                    print(f"    Technik: {item['technical_details']}")
                if item["automatic_action"] != "KEINE":
                    print(f"    Automatik: {item['automatic_action']}")

    return 0 if report["state"] in {"READY", "DEGRADED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
