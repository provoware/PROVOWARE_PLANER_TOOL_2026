from __future__ import annotations

import json

from storage.database import Database
from sync_core.canonical import payload_hash
from sync_core.history import (
    JournalIntegrityState,
    JournalPlanKind,
    JournalRecord,
    decode_snapshot,
    snapshot_hash,
)


class SyncHistoryRepository:
    """Read-only Zugriff auf Audit-Receipts und I011-Snapshots."""

    def __init__(self, database: Database) -> None:
        self.database = database

    @staticmethod
    def _kind(plan_id: str) -> JournalPlanKind:
        if plan_id.startswith("RECOVERYPLAN-"):
            return JournalPlanKind.RECOVERY
        if plan_id.startswith("RESOLUTIONPLAN-"):
            return JournalPlanKind.RESOLUTION
        return JournalPlanKind.SYNC

    def _record(self, receipt, snapshot) -> JournalRecord:
        integrity = JournalIntegrityState.VERIFIED
        reasons: list[str] = []
        before_todo = before_calendar = after_todo = after_calendar = None
        snapshot_sha256 = None

        try:
            receipt_payload = json.loads(receipt["payload_json"])
            if payload_hash(receipt_payload) != receipt["receipt_sha256"]:
                integrity = JournalIntegrityState.TAMPERED
                reasons.append("Receipt-Hash stimmt nicht mit payload_json überein.")
        except Exception:
            integrity = JournalIntegrityState.TAMPERED
            reasons.append("Receipt-Payload ist nicht lesbar.")

        if snapshot is None:
            if integrity is not JournalIntegrityState.TAMPERED:
                integrity = JournalIntegrityState.LEGACY_NO_SNAPSHOT
                reasons.append(
                    "Dieser ältere Nachweis besitzt keinen I011-Wertsnapshot. "
                    "Er bleibt auditierbar, ist aber nicht automatisch wiederherstellbar."
                )
        else:
            snapshot_sha256 = snapshot["snapshot_sha256"]
            try:
                expected = snapshot_hash(
                    snapshot["before_json"],
                    snapshot["after_json"],
                    receipt["receipt_sha256"],
                )
                if expected != snapshot_sha256:
                    integrity = JournalIntegrityState.TAMPERED
                    reasons.append("Snapshot-Hash stimmt nicht.")
                before_meta = json.loads(snapshot["before_json"])
                after_meta = json.loads(snapshot["after_json"])
                for meta, label in ((before_meta, "Vorher"), (after_meta, "Nachher")):
                    if meta.get("receipt_id") != receipt["receipt_id"]:
                        integrity = JournalIntegrityState.TAMPERED
                        reasons.append(f"{label}-Snapshot referenziert eine andere Receipt-ID.")
                    if meta.get("receipt_sha256") != receipt["receipt_sha256"]:
                        integrity = JournalIntegrityState.TAMPERED
                        reasons.append(f"{label}-Snapshot referenziert einen anderen Receipt-Hash.")
                    if meta.get("link_id") != receipt["link_id"]:
                        integrity = JournalIntegrityState.TAMPERED
                        reasons.append(f"{label}-Snapshot referenziert einen anderen Link.")
                before_todo, before_calendar, _before_baselines = decode_snapshot(snapshot["before_json"])
                after_todo, after_calendar, _after_baselines = decode_snapshot(snapshot["after_json"])
            except Exception as exc:
                integrity = JournalIntegrityState.TAMPERED
                reasons.append(f"Snapshot ist nicht sicher lesbar: {type(exc).__name__}")

        return JournalRecord(
            receipt_id=receipt["receipt_id"],
            link_id=receipt["link_id"],
            plan_id=receipt["plan_id"],
            precondition_sha256=receipt["precondition_sha256"],
            receipt_sha256=receipt["receipt_sha256"],
            payload_json=receipt["payload_json"],
            created_at=receipt["created_at"],
            todo_version_before=int(receipt["todo_version_before"]),
            todo_version_after=int(receipt["todo_version_after"]),
            event_version_before=int(receipt["event_version_before"]),
            event_version_after=int(receipt["event_version_after"]),
            link_version_before=int(receipt["link_version_before"]),
            link_version_after=int(receipt["link_version_after"]),
            plan_kind=self._kind(receipt["plan_id"]),
            integrity=integrity,
            integrity_reason=" ".join(reasons) if reasons else "Receipt und Snapshot sind hashgebunden und konsistent.",
            snapshot_sha256=snapshot_sha256,
            before_todo_values=before_todo,
            before_calendar_values=before_calendar,
            after_todo_values=after_todo,
            after_calendar_values=after_calendar,
        )

    def list_records(self, link_id: str | None = None) -> tuple[JournalRecord, ...]:
        with self.database.session() as connection:
            if link_id is None:
                receipts = connection.execute(
                    "SELECT * FROM sync_audit_receipts ORDER BY created_at DESC, receipt_id DESC"
                ).fetchall()
            else:
                receipts = connection.execute(
                    "SELECT * FROM sync_audit_receipts WHERE link_id=? "
                    "ORDER BY created_at DESC, receipt_id DESC",
                    (link_id,),
                ).fetchall()
            snapshots = {
                row["receipt_id"]: row
                for row in connection.execute("SELECT * FROM sync_history_snapshots").fetchall()
            }
        return tuple(self._record(row, snapshots.get(row["receipt_id"])) for row in receipts)

    def get_record(self, receipt_id: str) -> JournalRecord:
        with self.database.session() as connection:
            receipt = connection.execute(
                "SELECT * FROM sync_audit_receipts WHERE receipt_id=?", (receipt_id,)
            ).fetchone()
            if receipt is None:
                raise KeyError(f"SYNC-HISTORY-404: Audit-Receipt {receipt_id} wurde nicht gefunden")
            snapshot = connection.execute(
                "SELECT * FROM sync_history_snapshots WHERE receipt_id=?", (receipt_id,)
            ).fetchone()
        return self._record(receipt, snapshot)

    def snapshot_count(self, link_id: str | None = None) -> int:
        with self.database.session() as connection:
            if link_id is None:
                return int(connection.execute("SELECT COUNT(*) FROM sync_history_snapshots").fetchone()[0])
            return int(
                connection.execute(
                    "SELECT COUNT(*) FROM sync_history_snapshots WHERE link_id=?", (link_id,)
                ).fetchone()[0]
            )
