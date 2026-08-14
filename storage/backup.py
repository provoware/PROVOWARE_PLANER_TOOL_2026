from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from calendar_core.errors import BackupError, RestoreRejectedError
from storage.database import Database


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fsync_file(path: Path) -> None:
    with path.open("rb") as handle:
        os.fsync(handle.fileno())


def _validate_sqlite(path: Path) -> None:
    try:
        connection = sqlite3.connect(path)
        try:
            result = connection.execute("PRAGMA quick_check").fetchone()[0]
        finally:
            connection.close()
    except sqlite3.DatabaseError as exc:
        raise RestoreRejectedError("CAL-RESTORE-001: Sicherung ist keine gültige SQLite-Datenbank") from exc
    if result != "ok":
        raise RestoreRejectedError(f"CAL-RESTORE-001: Sicherungsprüfung fehlgeschlagen: {result}")


def create_backup(database: Database, target: Path) -> dict:
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    candidate = target.with_suffix(target.suffix + ".tmp")
    if candidate.exists():
        candidate.unlink()
    source = database.connect()
    try:
        destination = sqlite3.connect(candidate)
        try:
            source.backup(destination)
            destination.commit()
        finally:
            destination.close()
    except sqlite3.Error as exc:
        candidate.unlink(missing_ok=True)
        raise BackupError("CAL-BACKUP-001: Sicherung konnte nicht erstellt werden") from exc
    finally:
        source.close()

    _validate_sqlite(candidate)
    _fsync_file(candidate)
    os.replace(candidate, target)
    digest = _sha256(target)
    manifest = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "database_sha256": digest,
        "size": target.stat().st_size,
        "source": str(database.path),
    }
    manifest_path = target.with_suffix(target.suffix + ".json")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _fsync_file(manifest_path)
    return manifest


def restore_backup(backup: Path, target: Path, *, expected_sha256: str | None = None) -> None:
    backup = Path(backup)
    target = Path(target)
    if not backup.is_file():
        raise RestoreRejectedError("CAL-RESTORE-001: Sicherungsdatei fehlt")
    if expected_sha256 and _sha256(backup) != expected_sha256:
        raise RestoreRejectedError("CAL-RESTORE-HASH-001: Sicherungs-Hash stimmt nicht")
    _validate_sqlite(backup)

    target.parent.mkdir(parents=True, exist_ok=True)
    candidate = target.with_suffix(target.suffix + ".restore-candidate")
    rollback_copy = target.with_suffix(target.suffix + ".pre-restore")
    candidate.unlink(missing_ok=True)
    rollback_copy.unlink(missing_ok=True)

    source = sqlite3.connect(backup)
    try:
        destination = sqlite3.connect(candidate)
        try:
            source.backup(destination)
            destination.commit()
        finally:
            destination.close()
    except sqlite3.Error as exc:
        candidate.unlink(missing_ok=True)
        raise RestoreRejectedError("CAL-RESTORE-001: Restore-Kandidat konnte nicht erzeugt werden") from exc
    finally:
        source.close()

    _validate_sqlite(candidate)
    _fsync_file(candidate)
    if target.exists():
        shutil.copy2(target, rollback_copy)
        _fsync_file(rollback_copy)
    try:
        os.replace(candidate, target)
        _validate_sqlite(target)
    except Exception:
        if rollback_copy.exists():
            os.replace(rollback_copy, target)
        raise
    else:
        rollback_copy.unlink(missing_ok=True)
