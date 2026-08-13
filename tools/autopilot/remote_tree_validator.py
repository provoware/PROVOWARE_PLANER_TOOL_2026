from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def parse_tree(lines: list[str]) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for raw in lines:
        line = raw.rstrip("\n")
        if not line:
            continue
        meta, path = line.split("\t", 1)
        mode, kind, blob_sha, size = meta.split()
        rows[path] = {
            "path": path,
            "mode": mode,
            "type": kind,
            "blob_sha": blob_sha,
            "size": int(size),
            "status": "PASS",
        }
    return rows


def validate(rows: dict[str, dict]) -> list[str]:
    manifest = json.loads(
        (ROOT / "REPOSITORY_MANIFEST.json").read_text(encoding="utf-8")
    )
    expected = set(manifest["expected_paths"])
    actual = set(rows)
    problems: list[str] = []
    if expected != actual:
        problems.append(
            "VAL-INVENTORY-001: Repository-Pfade weichen vom Soll ab"
        )
    for path, row in rows.items():
        if row["mode"] not in {"100644", "100755"}:
            problems.append(
                f"REMOTE-TREE-001: unerlaubter Modus {row['mode']}: {path}"
            )
    return problems


def main() -> int:
    rows = parse_tree(sys.stdin.readlines())
    problems = validate(rows)
    if problems:
        print("\n".join(problems))
        return 1
    print(f"REMOTE_TREE_VALIDATOR=PASS files={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
