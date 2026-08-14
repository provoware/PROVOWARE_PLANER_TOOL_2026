from __future__ import annotations

import json
import os
import socket
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator
from uuid import uuid4

from backup_core.execution import RestoreIntent
from calendar_core.errors import RestoreRejectedError


RUNTIME_DIR_NAME = ".provoware_restore"
INTENT_NAME = "RESTORE_INTENT.json"
LEASE_NAME = "RESTORE_LEASE.json"
SNAPSHOT_NAME = "PRE_RESTORE_SNAPSHOT.sqlite3"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def runtime_dir(database_path: Path) -> Path:
    return Path(database_path).resolve().parent / RUNTIME_DIR_NAME


def intent_path(database_path: Path) -> Path:
    return runtime_dir(database_path) / INTENT_NAME


def lease_path(database_path: Path) -> Path:
    return runtime_dir(database_path) / LEASE_NAME


def snapshot_path(database_path: Path) -> Path:
    return runtime_dir(database_path) / SNAPSHOT_NAME


def _fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_write_json(path: Path, payload: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    candidate = path.with_name(path.name + ".tmp")
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    with candidate.open("w", encoding="utf-8") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(candidate, path)
    _fsync_dir(path.parent)


def _process_start_marker(pid: int) -> str:
    try:
        return Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").split()[21]
    except (OSError, IndexError):
        return "UNKNOWN"


def _lease_owner_alive(payload: dict) -> bool:
    try:
        pid = int(payload["pid"])
    except (KeyError, TypeError, ValueError):
        return False
    if payload.get("hostname") != socket.gethostname():
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    expected = str(payload.get("process_start_marker", "UNKNOWN"))
    current = _process_start_marker(pid)
    return expected == "UNKNOWN" or current == expected


def read_lease(database_path: Path) -> dict | None:
    path = lease_path(database_path)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RestoreRejectedError("RESTORE-LEASE-HASH-001: Restore-Lease ist nicht sicher lesbar") from exc
    return payload


def lease_owner_alive(database_path: Path) -> bool:
    payload = read_lease(database_path)
    return bool(payload and _lease_owner_alive(payload))


def assert_restore_write_allowed(database_path: Path, *, lease_id: str | None = None) -> None:
    payload = read_lease(database_path)
    if payload is None:
        return
    if lease_id and payload.get("lease_id") == lease_id:
        return
    raise RestoreRejectedError(
        "RESTORE-LEASE-001: Datenbank ist für eine sichere Wiederherstellung exklusiv gesperrt"
    )


def acquire_restore_lease(database_path: Path, *, plan_sha256: str, reclaim_stale: bool = False) -> dict:
    path = lease_path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = read_lease(database_path)
    if existing is not None:
        if _lease_owner_alive(existing):
            raise RestoreRejectedError("RESTORE-LEASE-001: Eine andere Restore-Ausführung ist noch aktiv")
        if not reclaim_stale:
            raise RestoreRejectedError("RESTORE-LEASE-STALE-001: Verwaiste Restore-Lease erfordert Recovery")
        path.unlink(missing_ok=True)
        _fsync_dir(path.parent)

    payload = {
        "schema_version": 1,
        "lease_id": str(uuid4()),
        "pid": os.getpid(),
        "hostname": socket.gethostname(),
        "process_start_marker": _process_start_marker(os.getpid()),
        "target_path": str(Path(database_path).resolve()),
        "plan_sha256": plan_sha256,
        "acquired_at": utc_now(),
    }
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        fd = os.open(path, flags, 0o600)
    except FileExistsError as exc:
        raise RestoreRejectedError("RESTORE-LEASE-001: Restore-Lease wurde parallel belegt") from exc
    try:
        raw = (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
        os.write(fd, raw)
        os.fsync(fd)
    finally:
        os.close(fd)
    _fsync_dir(path.parent)
    return payload


def release_restore_lease(database_path: Path, lease_id: str) -> None:
    path = lease_path(database_path)
    payload = read_lease(database_path)
    if payload is None:
        return
    if payload.get("lease_id") != lease_id:
        raise RestoreRejectedError("RESTORE-LEASE-OWNER-001: Restore-Lease gehört zu einer anderen Ausführung")
    path.unlink(missing_ok=True)
    _fsync_dir(path.parent)


def write_intent(database_path: Path, intent: RestoreIntent) -> None:
    if not intent.verify_hash():
        raise RestoreRejectedError("RESTORE-INTENT-HASH-001: Ungültiger Restore-Intent darf nicht gespeichert werden")
    atomic_write_json(intent_path(database_path), intent.to_dict())


def read_intent(database_path: Path) -> RestoreIntent | None:
    path = intent_path(database_path)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return RestoreIntent.from_dict(payload)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise RestoreRejectedError("RESTORE-INTENT-HASH-001: Restore-Intent ist verändert oder ungültig") from exc


@contextmanager
def restore_lease(database_path: Path, *, plan_sha256: str) -> Iterator[dict]:
    lease = acquire_restore_lease(database_path, plan_sha256=plan_sha256)
    try:
        yield lease
    finally:
        release_restore_lease(database_path, str(lease["lease_id"]))
