from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.parse import quote

from backup_core.model import BackupCandidate, CandidateState, RestorePlan
from calendar_core.errors import RestoreRejectedError
from storage.backup import ABSENT_SHA256, restore_backup


EXPECTED_SCHEMA_VERSION = 4
FaultHook = Callable[[str], None]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _database_state_sha256(path: Path) -> str:
    """Bindet den aktiven SQLite-Zustand einschließlich WAL rein lesend.

    SHM wird bewusst nicht gebunden, weil es Lock-/Shared-Memory-Zustand und keine
    kanonischen Nutzdaten enthält. So werden WAL-Änderungen erkannt, ohne reine
    Leseraktivität als fachliche Datenänderung zu behandeln.
    """
    path = Path(path)
    if not path.is_file():
        return ABSENT_SHA256
    digest = hashlib.sha256()
    for role, item in (("MAIN", path), ("WAL", Path(str(path) + "-wal"))):
        digest.update(role.encode("ascii") + b"\0")
        if not item.is_file():
            digest.update(b"ABSENT\0")
            continue
        digest.update(str(item.stat().st_size).encode("ascii") + b"\0")
        with item.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def _database_state_size(path: Path) -> int:
    if not Path(path).is_file():
        return 0
    total = Path(path).stat().st_size
    wal = Path(str(path) + "-wal")
    if wal.is_file():
        total += wal.stat().st_size
    return total


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _manifest_path(backup: Path) -> Path:
    return backup.with_suffix(backup.suffix + ".json")


def _readonly_sqlite_probe(path: Path) -> tuple[str, int]:
    """Prüft Integrität und die bereits kanonische Migrationsversion read-only.

    Die Anwendung verwendet seit I004 `schema_migrations` als autoritative
    Schemahistorie; `Database.schema_version()` liefert ebenfalls MAX(version) daraus.
    I015 führt daher bewusst kein paralleles `PRAGMA user_version`-Signal ein.
    """
    resolved = path.resolve(strict=True)
    uri = f"file:{quote(str(resolved), safe='/')}?mode=ro&immutable=1"
    try:
        connection = sqlite3.connect(uri, uri=True)
        try:
            connection.execute("PRAGMA query_only=ON")
            quick_check = str(connection.execute("PRAGMA quick_check").fetchone()[0])
            schema_row = connection.execute(
                "SELECT COALESCE(MAX(version), 0) FROM schema_migrations"
            ).fetchone()
            schema_version = int(schema_row[0])
        finally:
            connection.close()
    except (OSError, sqlite3.DatabaseError) as exc:
        raise RestoreRejectedError(
            "RESTORE-CANDIDATE-004: Sicherung ist nicht lesbar, keine gültige Planner-Datenbank oder besitzt keine gültige Migrationshistorie"
        ) from exc
    return quick_check, schema_version


class RestoreService:
    def __init__(
        self,
        *,
        backup_root: Path,
        target_database: Path,
        expected_schema_version: int = EXPECTED_SCHEMA_VERSION,
        fault_hook: FaultHook | None = None,
    ) -> None:
        self.backup_root = Path(backup_root).resolve()
        self.target_database = Path(target_database).resolve()
        self.expected_schema_version = int(expected_schema_version)
        self._fault_hook = fault_hook

    def _fault(self, point: str) -> None:
        if self._fault_hook is not None:
            self._fault_hook(point)

    def qualify_candidate(self, backup: Path) -> BackupCandidate:
        supplied = Path(backup)
        try:
            resolved = supplied.resolve(strict=True)
        except OSError:
            return BackupCandidate(
                backup_path=str(supplied), backup_sha256="", backup_size=0,
                manifest_path=str(_manifest_path(supplied)), manifest_sha256="",
                schema_version=-1, quick_check="NOT_RUN", state=CandidateState.BLOCKED,
                reason="RESTORE-CANDIDATE-001: Sicherungsdatei fehlt",
            )

        manifest = _manifest_path(resolved)
        base = dict(
            backup_path=str(resolved), backup_sha256="",
            backup_size=resolved.stat().st_size if resolved.is_file() else 0,
            manifest_path=str(manifest), manifest_sha256="", schema_version=-1,
            quick_check="NOT_RUN",
        )
        if not _inside(resolved, self.backup_root):
            return BackupCandidate(**base, state=CandidateState.BLOCKED, reason="RESTORE-BOUNDARY-001: Sicherung liegt außerhalb des Backup-Bereichs")
        if not resolved.is_file() or resolved.is_symlink():
            return BackupCandidate(**base, state=CandidateState.BLOCKED, reason="RESTORE-CANDIDATE-001: Sicherung ist keine reguläre Datei")
        if not manifest.is_file() or manifest.is_symlink():
            return BackupCandidate(**base, state=CandidateState.BLOCKED, reason="RESTORE-CANDIDATE-002: Sicherungsmanifest fehlt")

        backup_sha = _sha256(resolved)
        manifest_sha = _sha256(manifest)
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return BackupCandidate(**{**base, "backup_sha256": backup_sha, "manifest_sha256": manifest_sha}, state=CandidateState.BLOCKED, reason="RESTORE-CANDIDATE-003: Sicherungsmanifest ist ungültig")

        size = resolved.stat().st_size
        if data.get("database_sha256") != backup_sha or int(data.get("size", -1)) != size:
            return BackupCandidate(
                backup_path=str(resolved), backup_sha256=backup_sha, backup_size=size,
                manifest_path=str(manifest), manifest_sha256=manifest_sha,
                schema_version=-1, quick_check="NOT_RUN", state=CandidateState.BLOCKED,
                reason="RESTORE-CANDIDATE-HASH-001: Manifest, Größe oder Sicherungs-Hash stimmen nicht überein",
            )

        try:
            quick_check, schema_version = _readonly_sqlite_probe(resolved)
        except RestoreRejectedError as exc:
            return BackupCandidate(
                backup_path=str(resolved), backup_sha256=backup_sha, backup_size=size,
                manifest_path=str(manifest), manifest_sha256=manifest_sha,
                schema_version=-1, quick_check="FAIL", state=CandidateState.BLOCKED,
                reason=str(exc),
            )
        if quick_check != "ok":
            return BackupCandidate(
                backup_path=str(resolved), backup_sha256=backup_sha, backup_size=size,
                manifest_path=str(manifest), manifest_sha256=manifest_sha,
                schema_version=schema_version, quick_check=quick_check, state=CandidateState.BLOCKED,
                reason=f"RESTORE-CANDIDATE-004: SQLite quick_check fehlgeschlagen: {quick_check}",
            )
        if schema_version != self.expected_schema_version:
            return BackupCandidate(
                backup_path=str(resolved), backup_sha256=backup_sha, backup_size=size,
                manifest_path=str(manifest), manifest_sha256=manifest_sha,
                schema_version=schema_version, quick_check=quick_check, state=CandidateState.BLOCKED,
                reason=f"RESTORE-SCHEMA-001: Sicherungsschema {schema_version} ist nicht der erwartete Stand {self.expected_schema_version}",
            )
        return BackupCandidate(
            backup_path=str(resolved), backup_sha256=backup_sha, backup_size=size,
            manifest_path=str(manifest), manifest_sha256=manifest_sha,
            schema_version=schema_version, quick_check=quick_check,
            state=CandidateState.QUALIFIED,
            reason="RESTORE-CANDIDATE-OK: Sicherung ist qualifiziert",
        )

    def prepare_restore(self, backup: Path) -> RestorePlan:
        candidate = self.qualify_candidate(backup)
        if not candidate.qualified:
            raise RestoreRejectedError(candidate.reason)
        target_exists = self.target_database.is_file()
        return RestorePlan.create(
            backup_path=candidate.backup_path,
            backup_sha256=candidate.backup_sha256,
            backup_size=candidate.backup_size,
            manifest_path=candidate.manifest_path,
            manifest_sha256=candidate.manifest_sha256,
            backup_schema_version=candidate.schema_version,
            target_path=str(self.target_database),
            target_existed=target_exists,
            target_sha256=_database_state_sha256(self.target_database),
            target_size=_database_state_size(self.target_database),
            prepared_at=datetime.now(timezone.utc).isoformat(),
        )

    def _verify_target_state(self, plan: RestorePlan) -> None:
        current_exists = self.target_database.is_file()
        current_sha = _database_state_sha256(self.target_database)
        current_size = _database_state_size(self.target_database)
        if (current_exists, current_sha, current_size) != (plan.target_existed, plan.target_sha256, plan.target_size):
            raise RestoreRejectedError("RESTORE-STALE-001: aktive Datenbank wurde nach Planerstellung verändert")

    def _verify_plan(self, plan: RestorePlan) -> BackupCandidate:
        if not isinstance(plan, RestorePlan) or not plan.verify_hash():
            raise RestoreRejectedError("RESTORE-PLAN-HASH-001: RestorePlan ist verändert oder ungültig")
        if Path(plan.target_path).resolve() != self.target_database:
            raise RestoreRejectedError("RESTORE-PLAN-TARGET-001: RestorePlan gehört zu einer anderen Zieldatenbank")
        candidate = self.qualify_candidate(Path(plan.backup_path))
        if not candidate.qualified:
            raise RestoreRejectedError(candidate.reason)
        expected_candidate = (
            plan.backup_path, plan.backup_sha256, plan.backup_size,
            plan.manifest_path, plan.manifest_sha256, plan.backup_schema_version,
        )
        current_candidate = (
            candidate.backup_path, candidate.backup_sha256, candidate.backup_size,
            candidate.manifest_path, candidate.manifest_sha256, candidate.schema_version,
        )
        if current_candidate != expected_candidate:
            raise RestoreRejectedError("RESTORE-PLAN-STALE-001: Sicherung oder Manifest wurde nach Planerstellung verändert")
        self._verify_target_state(plan)
        return candidate

    def commit_restore(self, plan: RestorePlan) -> dict:
        self._fault("precheck_begin")
        candidate = self._verify_plan(plan)
        self._fault("precheck_pass")

        def final_precheck(_target: Path) -> None:
            self._fault("physical_core_precheck")
            self._verify_target_state(plan)

        def postcheck(path: Path) -> None:
            self._fault("after_replace_before_postcheck")
            if _sha256(path) != candidate.backup_sha256:
                raise RestoreRejectedError("RESTORE-POSTCHECK-001: wiederhergestellte Datenbank stimmt nicht mit dem geplanten Backup überein")
            quick_check, schema = _readonly_sqlite_probe(path)
            if quick_check != "ok" or schema != self.expected_schema_version:
                raise RestoreRejectedError("RESTORE-POSTCHECK-002: wiederhergestellte Datenbank besteht Integritäts-/Schemaprüfung nicht")
            self._fault("postcheck_pass")

        restore_backup(
            Path(plan.backup_path), self.target_database,
            expected_sha256=plan.backup_sha256,
            precheck=final_precheck,
            postcheck=postcheck,
        )
        return {
            "status": "PASS",
            "plan_sha256": plan.plan_sha256,
            "restored_database_sha256": _sha256(self.target_database),
            "schema_version": self.expected_schema_version,
            "precheck": "PASS", "commit": "PASS", "postcheck": "PASS",
        }
