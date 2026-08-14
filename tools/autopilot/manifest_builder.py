from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VOLATILE = {
    "SHA256_DATEI_INVENTAR.json",
    "REMOTE_TREE_RECEIPT.json",
    "QUALIFICATION_REPORT.json",
}
MANIFESTS = [
    "SOURCE_MANIFEST.json",
    "BUILD_MANIFEST.json",
    "RELEASE_MANIFEST.json",
    "EVIDENCE_MANIFEST.json",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repository_files() -> list[str]:
    return sorted(
        str(path.relative_to(ROOT))
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and "__pycache__" not in path.parts
    )


def file_info(relative_path: str) -> dict:
    path = ROOT / relative_path
    return {
        "path": relative_path,
        "sha256": sha256(path),
        "size": path.stat().st_size,
        "status": "PASS",
    }


def write_json(relative_path: str, value: dict) -> None:
    (ROOT / relative_path).write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build() -> None:
    version_data = json.loads((ROOT / "VERSION.json").read_text(encoding="utf-8"))
    version = version_data["version"]
    iteration = version_data["iteration"]
    files = repository_files()
    generated = set(MANIFESTS) | {
        "MANIFEST_INDEX.json",
        "SHA256_DATEI_INVENTAR.json",
        "REMOTE_TREE_RECEIPT.json",
        "QUALIFICATION_REPORT.json",
    }
    source = [item for item in files if item not in generated and not item.startswith(".github/")]
    build_scope = [
        item for item in files
        if item.startswith(".github/")
        or item.startswith("tools/autopilot/")
        or item.startswith("runtime/")
        or item == "tools/start_orchestrator.py"
    ]
    evidence = [
        item for item in files
        if item.startswith("tests/")
        or item.startswith("errors/")
        or item.startswith("docs/I003_")
    ]

    write_json("SOURCE_MANIFEST.json", {
        "schema_version": 1,
        "manifest_type": "SOURCE",
        "version": version,
        "iteration": iteration,
        "entries": [file_info(item) for item in source],
        "count": len(source),
    })
    write_json("BUILD_MANIFEST.json", {
        "schema_version": 1,
        "manifest_type": "BUILD",
        "version": version,
        "iteration": iteration,
        "entries": [file_info(item) for item in build_scope],
        "count": len(build_scope),
    })
    write_json("RELEASE_MANIFEST.json", {
        "schema_version": 1,
        "manifest_type": "RELEASE",
        "version": version,
        "iteration": iteration,
        "state": "NOT_BUILT",
        "reason": f"{iteration} ist noch Entwicklungsstand; ein freigegebenes Endnutzer-Releasepaket existiert nicht.",
    })
    write_json("EVIDENCE_MANIFEST.json", {
        "schema_version": 1,
        "manifest_type": "EVIDENCE",
        "version": version,
        "iteration": iteration,
        "attestation_model": "subject_commit_plus_evidence_overlay",
        "entries": [file_info(item) for item in evidence],
        "count": len(evidence),
        "remote_receipt": "REMOTE_TREE_RECEIPT.json",
        "qualification_report": "QUALIFICATION_REPORT.json",
    })
    write_json("MANIFEST_INDEX.json", {
        "schema_version": 1,
        "version": version,
        "iteration": iteration,
        "manifests": [file_info(item) for item in MANIFESTS],
    })

    inventory = []
    for item in repository_files():
        if item in VOLATILE:
            continue
        path = ROOT / item
        inventory.append({
            "path": item,
            "sha256": sha256(path),
            "size": path.stat().st_size,
            "status": "PASS",
        })
    write_json("SHA256_DATEI_INVENTAR.json", {
        "schema_version": 1,
        "algorithm": "SHA-256",
        "scope": "Repository ohne Selbstreferenz und volatile Attestierungen",
        "excluded": sorted(VOLATILE),
        "entries": inventory,
        "count": len(inventory),
    })


def check() -> list[str]:
    problems: list[str] = []
    inventory = json.loads((ROOT / "SHA256_DATEI_INVENTAR.json").read_text(encoding="utf-8"))
    if inventory.get("state") == "PENDING_GENERATION":
        return ["VAL-INVENTORY-001: SHA-256-Inventar ist noch nicht erzeugt"]
    for item in inventory.get("entries", []):
        path = ROOT / item["path"]
        if not path.exists():
            problems.append(f"VAL-INVENTORY-001: Datei fehlt: {item['path']}")
        elif sha256(path) != item["sha256"] or path.stat().st_size != item["size"]:
            problems.append(f"VAL-INVENTORY-001: Hash oder Größe falsch: {item['path']}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.write:
        build()
        print("MANIFEST_BUILDER_WRITE=PASS")
    if args.check:
        problems = check()
        if problems:
            print("\n".join(problems))
            return 1
        print("MANIFEST_BUILDER_CHECK=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
