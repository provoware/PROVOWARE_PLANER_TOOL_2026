#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCENARIOS = [
    (
        "process_exit_after_atomic_replace",
        "test_i016_restore_crash_recovery.I016RestoreCrashRecoveryTest.test_process_exit_after_atomic_replace_is_finalized_on_restart",
    ),
    (
        "process_exit_before_physical_write",
        "test_i016_restore_crash_recovery.I016RestoreCrashRecoveryTest.test_process_exit_before_physical_write_recovers_no_change",
    ),
    (
        "exception_rollback_and_lease_guard",
        "test_i016_restore_execution.I016RestoreExecutionTest.test_exception_after_replace_returns_to_exact_logical_prestate",
    ),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="I016 Restore-Crash-Matrix")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    results = []
    for scenario, test_name in SCENARIOS:
        process = subprocess.run(
            [sys.executable, "-m", "unittest", test_name, "-v"],
            cwd=ROOT / "tests",
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        results.append({
            "scenario": scenario,
            "status": "PASS" if process.returncode == 0 else "FAIL",
            "return_code": process.returncode,
            "stderr_tail": process.stderr[-1200:] if process.returncode else "",
        })
    payload = {
        "schema_version": 1,
        "iteration": "I016",
        "status": "PASS" if all(item["status"] == "PASS" for item in results) else "FAIL",
        "scenarios": results,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    print(text, end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
