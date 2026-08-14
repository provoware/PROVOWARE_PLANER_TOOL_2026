from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

from backup_core.execution import RestoreIntent, RestoreIntentState
from backup_core.model import RestorePlan
from calendar_core.errors import RestoreRejectedError
from services.restore_service import (
    EXPECTED_SCHEMA_VERSION,
    RestoreService,
    _database_state_sha256,
    _readonly_sqlite_probe,
    _sha256,
)
from storage.backup import restore_backup
from storage.restore_guard import (
    acquire_restore_lease,
    lease_owner_alive,
    read_intent,
    read_lease,
    release_restore_lease,
    snapshot_path,
    write_intent,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _encoded_value(value: object) -> str:
    if value is None:
        return "N:"
    if isinstance(value, bytes):
        return "B:" + value.hex()
    if isinstance(value, float):
        return "F:" + value.hex()
    if isinstance(value, int):
        return "I:" + str(value)
    return "T:" + str(value)


def logical_database_sha256(path: Path) -> str:
    """Deterministischer Hash des fachlichen SQLite-Inhalts einschließlich WAL."""
    path = Path(path)
    if not path.is_file():
        return "ABSENT"
    resolved = path.resolve(strict=True)
    uri = f"file:{quote(str(resolved), safe='/')}?mode=ro"
    digest = hashlib.sha256()
    try:
        connection = sqlite3.connect(uri, uri=True, timeout=1.5)
        try:
            connection.execute("PRAGMA query_only=ON")
            quick = connection.execute("PRAGMA quick_check").fetchone()
            if not quick or quick[0] != "ok":
                raise sqlite3.DatabaseError(f"quick_check={quick}")
            schema_rows = connection.execute(
                "SELECT type,name,tbl_name,COALESCE(sql,'') FROM sqlite_master "
                "WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name,tbl_name,sql"
            ).fetchall()
            for row in schema_rows:
                digest.update((json.dumps(list(row), ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8"))
            tables = [row[1] for row in schema_rows if row[0] == "table"]
            for table in sorted(tables):
                quoted = '"' + str(table).replace('"', '""') + '"'
                columns = connection.execute(f"PRAGMA table_info({quoted})").fetchall()
                names = [str(row[1]) for row in columns]
                if not names:
                    continue
                select_cols = ",".join('"' + name.replace('"', '""') + '"' for name in names)
                rows = connection.execute(f"SELECT {select_cols} FROM {quoted}").fetchall()
                encoded_rows = ["\u001f".join(_encoded_value(value) for value in row) for row in rows]
                digest.update(("TABLE:" + str(table) + "\n").encode("utf-8"))
                for encoded in sorted(encoded_rows):
                    digest.update((encoded + "\n").encode("utf-8"))
        finally:
            connection.close()
    except sqlite3.DatabaseError as exc:
        raise RestoreRejectedError("RESTORE-EXECUTION-INTEGRITY-001: Datenbankzustand kann nicht sicher gehasht werden") from exc
    return digest.hexdigest()


def _create_sqlite_snapshot(source_path: Path, destination: Path) -> str:
    source_path = Path(source_path)
    destination = Path(destination)
    if not source_path.is_file():
        raise RestoreRejectedError("RESTORE-SNAPSHOT-001: Crashsicherer Restore benötigt eine vorhandene Zieldatenbank")
    destination.parent.mkdir(parents=True, exist_ok=True)
    candidate = destination.with_suffix(destination.suffix + ".tmp")
    candidate.unlink(missing_ok=True)
    destination.unlink(missing_ok=True)
    source = sqlite3.connect(source_path, timeout=1.5)
    try:
        target = sqlite3.connect(candidate)
        try:
            source.backup(target)
            target.commit()
        finally:
            target.close()
    finally:
        source.close()
    quick, schema = _readonly_sqlite_probe(candidate)
    if quick != "ok" or schema != EXPECTED_SCHEMA_VERSION:
        candidate.unlink(missing_ok=True)
        raise RestoreRejectedError("RESTORE-SNAPSHOT-002: Vorzustand konnte nicht valide gesichert werden")
    with candidate.open("rb") as handle:
        os.fsync(handle.fileno())
    os.replace(candidate, destination)
    return _sha256(destination)


def _prove_no_writer(database_path: Path) -> None:
    try:
        connection = sqlite3.connect(database_path, timeout=1.5)
        try:
            connection.execute("PRAGMA busy_timeout=1500")
            connection.execute("BEGIN IMMEDIATE")
            connection.rollback()
        finally:
            connection.close()
    except sqlite3.OperationalError as exc:
        raise RestoreRejectedError("RESTORE-LEASE-BUSY-001: Ein Datenbankschreiber ist noch aktiv") from exc


class RestoreExecutionService:
    """I016-Sicherheitsmantel um den unveränderten I015-RestoreService."""

    def __init__(self, restore_service: RestoreService) -> None:
        self.restore_service = restore_service
        self.target_database = restore_service.target_database

    def inspect_pending(self) -> dict:
        intent = read_intent(self.target_database)
        lease = read_lease(self.target_database)
        if intent is None:
            return {
                "status": "CLEAR" if lease is None else ("ACTIVE" if lease_owner_alive(self.target_database) else "STALE_LEASE"),
                "intent": None,
                "lease": lease,
            }
        return {
            "status": "CLOSED" if intent.state is RestoreIntentState.CLOSED else "PENDING",
            "intent": intent,
            "lease": lease,
        }

    def _persist(self, intent: RestoreIntent) -> RestoreIntent:
        write_intent(self.target_database, intent)
        return intent

    def _validate_restored_target(self, intent: RestoreIntent) -> None:
        if _sha256(self.target_database) != intent.backup_sha256:
            raise RestoreRejectedError("RESTORE-EXECUTION-POST-001: Ziel entspricht nicht der geplanten Sicherung")
        if logical_database_sha256(self.target_database) != intent.expected_restored_logical_sha256:
            raise RestoreRejectedError("RESTORE-EXECUTION-POST-002: Fachlicher Zielzustand stimmt nicht mit der Sicherung überein")
        quick, schema = _readonly_sqlite_probe(self.target_database)
        if quick != "ok" or schema != self.restore_service.expected_schema_version:
            raise RestoreRejectedError("RESTORE-EXECUTION-POST-003: Ziel besteht Integritäts-/Schemaprüfung nicht")

    def _rollback_snapshot(self, intent: RestoreIntent) -> None:
        snapshot = Path(intent.snapshot_path)
        if not snapshot.is_file() or _sha256(snapshot) != intent.snapshot_sha256:
            raise RestoreRejectedError("RESTORE-SNAPSHOT-HASH-001: Crashsicherer Vorzustand fehlt oder wurde verändert")
        restore_backup(snapshot, self.target_database, expected_sha256=intent.snapshot_sha256)
        if logical_database_sha256(self.target_database) != intent.target_logical_sha256_before:
            raise RestoreRejectedError("RESTORE-RECOVERY-VERIFY-001: Wiederhergestellter Vorzustand stimmt fachlich nicht")

    def execute(self, plan: RestorePlan) -> dict:
        if not isinstance(plan, RestorePlan) or not plan.verify_hash():
            raise RestoreRejectedError("RESTORE-PLAN-HASH-001: RestorePlan ist verändert oder ungültig")
        if not plan.target_existed:
            raise RestoreRejectedError("RESTORE-SNAPSHOT-001: I016-Ausführung benötigt einen vorhandenen, sicher rücksetzbaren Vorzustand")
        if read_intent(self.target_database) is not None and read_intent(self.target_database).state is not RestoreIntentState.CLOSED:
            raise RestoreRejectedError("RESTORE-INTENT-PENDING-001: Offener Restore-Intent muss zuerst recovered werden")

        self.restore_service._verify_plan(plan)
        lease = acquire_restore_lease(self.target_database, plan_sha256=plan.plan_sha256)
        lease_id = str(lease["lease_id"])
        intent: RestoreIntent | None = None
        closed = False
        try:
            _prove_no_writer(self.target_database)
            self.restore_service._verify_plan(plan)
            before_logical = logical_database_sha256(self.target_database)
            expected_logical = logical_database_sha256(Path(plan.backup_path))
            snapshot = snapshot_path(self.target_database)
            snapshot_sha = _create_sqlite_snapshot(self.target_database, snapshot)
            if logical_database_sha256(snapshot) != before_logical:
                raise RestoreRejectedError("RESTORE-SNAPSHOT-VERIFY-001: Vorzustand-Snapshot stimmt fachlich nicht mit dem Ziel überein")
            intent = self._persist(RestoreIntent.create(
                intent_id=str(uuid4()),
                plan_sha256=plan.plan_sha256,
                backup_path=plan.backup_path,
                backup_sha256=plan.backup_sha256,
                target_path=plan.target_path,
                target_existed_before=plan.target_existed,
                target_state_sha256_before=_database_state_sha256(self.target_database),
                target_logical_sha256_before=before_logical,
                expected_restored_logical_sha256=expected_logical,
                snapshot_path=str(snapshot),
                snapshot_sha256=snapshot_sha,
                lease_id=lease_id,
                timestamp=_utc_now(),
            ))
            intent = self._persist(intent.transition(RestoreIntentState.COMMITTING, timestamp=_utc_now()))
            core_result = self.restore_service.commit_restore(plan)
            self._validate_restored_target(intent)
            intent = self._persist(intent.transition(RestoreIntentState.VERIFIED, timestamp=_utc_now(), outcome="RESTORE_VERIFIED"))
            intent = self._persist(intent.transition(RestoreIntentState.CLOSED, timestamp=_utc_now(), outcome="RESTORE_OK"))
            closed = True
            Path(intent.snapshot_path).unlink(missing_ok=True)
            release_restore_lease(self.target_database, lease_id)
            return {
                **core_result,
                "execution_status": "CLOSED",
                "intent_id": intent.intent_id,
                "intent_sha256": intent.intent_sha256,
                "lease": "RELEASED",
            }
        except BaseException:
            if intent is not None:
                try:
                    current_logical = logical_database_sha256(self.target_database)
                    if current_logical != intent.target_logical_sha256_before:
                        self._rollback_snapshot(intent)
                    intent = self._persist(intent.transition(RestoreIntentState.CLOSED, timestamp=_utc_now(), outcome="ROLLBACK_OK"))
                    closed = True
                    Path(intent.snapshot_path).unlink(missing_ok=True)
                    release_restore_lease(self.target_database, lease_id)
                except Exception:
                    pass
            elif not closed:
                try:
                    release_restore_lease(self.target_database, lease_id)
                except Exception:
                    pass
            raise

    def recover_pending(self) -> dict:
        intent = read_intent(self.target_database)
        lease = read_lease(self.target_database)
        if intent is None:
            if lease is None:
                return {"status": "CLEAR"}
            if lease_owner_alive(self.target_database):
                raise RestoreRejectedError("RESTORE-LEASE-001: Restore-Ausführung ist noch aktiv")
            release_restore_lease(self.target_database, str(lease["lease_id"]))
            return {"status": "STALE_LEASE_CLEARED"}
        if intent.state is RestoreIntentState.CLOSED:
            if lease is not None:
                if lease_owner_alive(self.target_database):
                    raise RestoreRejectedError("RESTORE-LEASE-001: Restore-Lease ist noch aktiv")
                release_restore_lease(self.target_database, str(lease["lease_id"]))
            Path(intent.snapshot_path).unlink(missing_ok=True)
            return {"status": "CLOSED", "outcome": intent.outcome}
        if lease is not None and lease_owner_alive(self.target_database):
            raise RestoreRejectedError("RESTORE-LEASE-001: Restore-Ausführung ist noch aktiv")

        recovery_lease = acquire_restore_lease(
            self.target_database,
            plan_sha256=intent.plan_sha256,
            reclaim_stale=True,
        )
        lease_id = str(recovery_lease["lease_id"])
        try:
            _prove_no_writer(self.target_database)
            current_logical = logical_database_sha256(self.target_database)
            if intent.state is RestoreIntentState.VERIFIED:
                if current_logical != intent.expected_restored_logical_sha256:
                    raise RestoreRejectedError("RESTORE-RECOVERY-AMBIGUOUS-001: Nach VERIFIED wurde der Zielzustand verändert")
                self._validate_restored_target(intent)
                intent = self._persist(intent.transition(RestoreIntentState.CLOSED, timestamp=_utc_now(), outcome="RECOVERED_CLOSE"))
            elif current_logical == intent.expected_restored_logical_sha256:
                self._validate_restored_target(intent)
                if intent.state is RestoreIntentState.PREPARED:
                    raise RestoreRejectedError("RESTORE-RECOVERY-AMBIGUOUS-002: Ziel ist neu, obwohl Intent noch PREPARED ist")
                intent = self._persist(intent.transition(RestoreIntentState.VERIFIED, timestamp=_utc_now(), outcome="RECOVERED_COMMIT"))
                intent = self._persist(intent.transition(RestoreIntentState.CLOSED, timestamp=_utc_now(), outcome="RECOVERED_COMMIT"))
            elif current_logical == intent.target_logical_sha256_before:
                intent = self._persist(intent.transition(RestoreIntentState.CLOSED, timestamp=_utc_now(), outcome="RECOVERED_NO_CHANGE"))
            else:
                self._rollback_snapshot(intent)
                intent = self._persist(intent.transition(RestoreIntentState.CLOSED, timestamp=_utc_now(), outcome="RECOVERED_ROLLBACK"))
            Path(intent.snapshot_path).unlink(missing_ok=True)
            release_restore_lease(self.target_database, lease_id)
            return {"status": "RECOVERED", "outcome": intent.outcome, "intent_sha256": intent.intent_sha256}
        except Exception:
            raise
