#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from transport_profiles import (
    ROOT,
    TransportProfileError,
    classify_path,
    load_contract,
    never_transport,
    profile_report,
    select_profile,
)

FIXED_ZIP_TIME = (2026, 1, 1, 0, 0, 0)
PACKAGE_MANIFEST = "PAKETMANIFEST.json"
PACKAGE_INVENTORY = "PAKET_INVENTAR.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_value(root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(root), *args], text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNBEKANNT"


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _package_inventory(staging: Path) -> dict:
    entries = []
    for path in sorted(p for p in staging.rglob("*") if p.is_file()):
        rel = path.relative_to(staging).as_posix()
        if rel == PACKAGE_INVENTORY:
            continue
        entries.append({
            "path": rel,
            "sha256": sha256_file(path),
            "size": path.stat().st_size,
        })
    return {
        "schema_version": 1,
        "algorithm": "SHA-256",
        "scope": "Transportpaket ohne Selbstreferenz des Paketinventars",
        "excluded": [PACKAGE_INVENTORY],
        "count": len(entries),
        "entries": entries,
    }


def _zip_staging(staging: Path, archive: Path) -> None:
    archive.parent.mkdir(parents=True, exist_ok=True)
    candidate = archive.with_suffix(archive.suffix + ".tmp")
    candidate.unlink(missing_ok=True)
    with zipfile.ZipFile(candidate, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as handle:
        for path in sorted(p for p in staging.rglob("*") if p.is_file()):
            rel = path.relative_to(staging).as_posix()
            info = zipfile.ZipInfo(rel, date_time=FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            mode = 0o755 if rel in {"tools/start_gui.py", "tools/start_orchestrator.py"} else 0o644
            info.external_attr = mode << 16
            handle.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    candidate.replace(archive)


def build_package(profile: str, output_dir: Path, root: Path = ROOT) -> Path:
    report = profile_report(root)
    if report["status"] != "PASS":
        raise TransportProfileError("TRANSPORT-KLASSIFIKATION-UNGUELTIG: " + " | ".join(report["errors"]))

    contract = load_contract(root)
    selected = select_profile(profile, root)
    version = json.loads((root / "VERSION.json").read_text(encoding="utf-8"))
    output_dir = Path(output_dir)
    archive = output_dir / f"PROVOWARE_PLANER_{profile}_{version['version']}.zip"

    with tempfile.TemporaryDirectory(prefix="provoware-transport-") as temp:
        staging = Path(temp) / "paket"
        staging.mkdir(parents=True)
        for relative in selected:
            source = root / relative
            if not source.is_file():
                raise TransportProfileError(f"TRANSPORT-QUELLDATEI-FEHLT: {relative}")
            target = staging / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)

        manifest = {
            "schema_version": 1,
            "profile": profile,
            "profile_description": contract["profiles"][profile].get("description", ""),
            "version": version["version"],
            "iteration": version["iteration"],
            "checkpoint": version["checkpoint"],
            "source_commit": _git_value(root, "rev-parse", "HEAD"),
            "source_tree": _git_value(root, "rev-parse", "HEAD^{tree}"),
            "transport_contract": contract["contract_id"],
            "transport_contract_version": contract["version"],
            "payload_file_count": len(selected),
            "payload_classes": contract["profiles"][profile].get("classes", []),
            "package_inventory": PACKAGE_INVENTORY,
            "user_data_included": False,
            "backup_data_included": False,
        }
        _write_json(staging / PACKAGE_MANIFEST, manifest)
        _write_json(staging / PACKAGE_INVENTORY, _package_inventory(staging))
        _zip_staging(staging, archive)

    validate_archive(archive, root=root)
    return archive


def validate_archive(archive: Path, root: Path = ROOT) -> dict:
    archive = Path(archive)
    contract = load_contract(root)
    errors: list[str] = []
    with zipfile.ZipFile(archive, "r") as handle:
        names = sorted(info.filename for info in handle.infolist() if not info.is_dir())
        for name in names:
            pure = PurePosixPath(name)
            if pure.is_absolute() or ".." in pure.parts:
                errors.append(f"TRANSPORT-ZIP-PFAD-UNSICHER: {name}")
            if never_transport(name, contract):
                errors.append(f"TRANSPORT-VERBOTENER-PFAD: {name}")
        if PACKAGE_MANIFEST not in names:
            errors.append("TRANSPORT-PAKETMANIFEST-FEHLT")
        if PACKAGE_INVENTORY not in names:
            errors.append("TRANSPORT-PAKETINVENTAR-FEHLT")
        if errors:
            raise TransportProfileError(" | ".join(errors))

        manifest = json.loads(handle.read(PACKAGE_MANIFEST).decode("utf-8"))
        inventory = json.loads(handle.read(PACKAGE_INVENTORY).decode("utf-8"))
        profile = str(manifest.get("profile", ""))
        if profile not in contract.get("profiles", {}):
            errors.append(f"TRANSPORT-PROFIL-UNBEKANNT: {profile}")
        else:
            allowed = set(select_profile(profile, root))
            generated = set(contract.get("generated_package_files", []))
            actual_source_names = set(names) - generated
            if actual_source_names != allowed:
                missing = sorted(allowed - actual_source_names)
                unexpected = sorted(actual_source_names - allowed)
                if missing:
                    errors.append(f"TRANSPORT-PAKETDATEI-FEHLT: {missing[:10]}")
                if unexpected:
                    errors.append(f"TRANSPORT-PAKETDATEI-UNERWARTET: {unexpected[:10]}")

        inventory_entries = {item["path"]: item for item in inventory.get("entries", [])}
        expected_inventory_names = set(names) - {PACKAGE_INVENTORY}
        if set(inventory_entries) != expected_inventory_names:
            errors.append("TRANSPORT-INVENTAR-PFADE-WIDERSPRUCH")
        for name, item in inventory_entries.items():
            payload = handle.read(name)
            if len(payload) != item.get("size") or sha256_bytes(payload) != item.get("sha256"):
                errors.append(f"TRANSPORT-INVENTAR-HASH-FALSCH: {name}")

        if manifest.get("user_data_included") is not False or manifest.get("backup_data_included") is not False:
            errors.append("TRANSPORT-PAKET-DEKLARIERT-NUTZERDATEN")

    if errors:
        raise TransportProfileError(" | ".join(errors))
    return {
        "status": "PASS",
        "profile": manifest["profile"],
        "files": len(names),
        "sha256": sha256_file(archive),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="PROVOWARE Transportpakete strikt nach Profil erzeugen")
    parser.add_argument("--profile", default="NUTZER", choices=["PROJEKTKERN", "NUTZER", "ENTWICKLER", "EVIDENCE"])
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist_transport")
    parser.add_argument("--validate", type=Path)
    args = parser.parse_args()
    try:
        if args.validate:
            result = validate_archive(args.validate)
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
            return 0
        archive = build_package(args.profile, args.output_dir)
        result = validate_archive(archive)
        print(f"TRANSPORTPAKET=PASS profile={result['profile']} files={result['files']}")
        print(f"PFAD={archive}")
        print(f"SHA256={result['sha256']}")
        return 0
    except (TransportProfileError, OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"TRANSPORTPAKET=FAIL {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
