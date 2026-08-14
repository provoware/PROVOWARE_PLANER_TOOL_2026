from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from storage.database import Database
from sync_core.canonical import canonical_hash, canonical_json, payload_hash
from sync_core.errors import SyncBaselineError, SyncPlanBlockedError, SyncPostcheckError, SyncStalePlanError
from sync_core.faults import trigger
from sync_core.fields import SYNC_FIELD_SPECS
from sync_core.history import snapshot_hash, snapshot_payload
from sync_core.model import PlanFieldAction, SyncAuditReceipt, SyncBaseline, SyncPlan
from todo_core.model import LinkDirection


def _dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _db_value(value: object) -> object:
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise SyncPlanBlockedError("SYNC-PRECHECK-004: Zeitpunkt besitzt keine Zeitzone")
        return value.astimezone(timezone.utc).isoformat()
    return value


@dataclass(frozen=True, slots=True)
class SyncSnapshot:
    link_id: str
    todo_id: str
    event_id: str
    direction: LinkDirection
    link_version: int
    todo_version: int
    event_version: int
    detached: bool
    todo_values: dict[str, object]
    calendar_values: dict[str, object]
    baseline_hashes: dict[str, str]
    baseline_json: dict[str, str]


class SyncRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    @staticmethod
    def _value(row, column: str) -> object:
        value = row[column]
        if column in {"start_at", "due_at", "end_at"}:
            return _dt(value)
        return value

    def _snapshot(self, connection, link_id: str) -> SyncSnapshot:
        link = connection.execute("SELECT * FROM todo_calendar_links WHERE link_id=?", (link_id,)).fetchone()
        if link is None:
            raise SyncBaselineError(f"SYNC-LINK-001: Verknüpfung {link_id} wurde nicht gefunden")
        todo = connection.execute("SELECT * FROM todos WHERE todo_id=?", (link["todo_id"],)).fetchone()
        event = connection.execute("SELECT * FROM calendar_events WHERE event_id=?", (link["event_id"],)).fetchone()
        if todo is None or event is None:
            raise SyncBaselineError("SYNC-LINK-002: Ein verknüpfter Endpunkt fehlt physisch")
        baseline_rows = connection.execute(
            "SELECT field_id,baseline_sha256,baseline_json FROM sync_field_baselines WHERE link_id=?",
            (link_id,),
        ).fetchall()
        return SyncSnapshot(
            link_id=link_id,
            todo_id=link["todo_id"],
            event_id=link["event_id"],
            direction=LinkDirection(link["direction"]),
            link_version=int(link["version"]),
            todo_version=int(todo["version"]),
            event_version=int(event["version"]),
            detached=bool(link["deleted_at"] or todo["deleted_at"] or event["deleted_at"]),
            todo_values={spec.field_id: self._value(todo, spec.todo_field) for spec in SYNC_FIELD_SPECS},
            calendar_values={spec.field_id: self._value(event, spec.calendar_field) for spec in SYNC_FIELD_SPECS},
            baseline_hashes={row["field_id"]: row["baseline_sha256"] for row in baseline_rows},
            baseline_json={row["field_id"]: row["baseline_json"] for row in baseline_rows},
        )

    def snapshot(self, link_id: str) -> SyncSnapshot:
        with self.database.session() as connection:
            connection.execute("BEGIN")
            snapshot = self._snapshot(connection, link_id)
            connection.rollback()
            return snapshot

    def initialize_baselines(self, link_id: str, *, now: datetime) -> tuple[SyncBaseline, ...]:
        timestamp = now.astimezone(timezone.utc).isoformat()
        with self.database.transaction() as connection:
            snapshot = self._snapshot(connection, link_id)
            if snapshot.detached:
                raise SyncBaselineError("SYNC-BASELINE-001: Gelöschte oder getrennte Endpunkte dürfen keine Baseline erhalten")
            prepared: list[tuple[str, str, str]] = []
            for spec in SYNC_FIELD_SPECS:
                todo_value = snapshot.todo_values[spec.field_id]
                calendar_value = snapshot.calendar_values[spec.field_id]
                todo_hash = canonical_hash(todo_value)
                calendar_hash = canonical_hash(calendar_value)
                if todo_hash != calendar_hash:
                    raise SyncBaselineError(
                        f"SYNC-BASELINE-002: Feld {spec.field_id} ist nicht identisch; sichere Baseline-Bindung blockiert"
                    )
                existing = snapshot.baseline_hashes.get(spec.field_id)
                if existing is not None and existing != todo_hash:
                    raise SyncBaselineError(
                        f"SYNC-BASELINE-003: Feld {spec.field_id} besitzt bereits eine andere gebundene Baseline"
                    )
                prepared.append((spec.field_id, canonical_json(todo_value), todo_hash))
            for field_id, encoded, digest in prepared:
                connection.execute(
                    """INSERT OR IGNORE INTO sync_field_baselines(
                       link_id,field_id,baseline_json,baseline_sha256,todo_sha256_at_baseline,
                       calendar_sha256_at_baseline,version,created_at,updated_at
                       ) VALUES (?,?,?,?,?,?,1,?,?)""",
                    (link_id, field_id, encoded, digest, digest, digest, timestamp, timestamp),
                )
        return self.baselines(link_id)

    def baselines(self, link_id: str) -> tuple[SyncBaseline, ...]:
        with self.database.session() as connection:
            rows = connection.execute(
                "SELECT * FROM sync_field_baselines WHERE link_id=? ORDER BY field_id", (link_id,)
            ).fetchall()
        return tuple(
            SyncBaseline(
                link_id=row["link_id"],
                field_id=row["field_id"],
                baseline_json=row["baseline_json"],
                baseline_sha256=row["baseline_sha256"],
                version=int(row["version"]),
            )
            for row in rows
        )

    @staticmethod
    def _update_entity(
        connection,
        table: str,
        id_column: str,
        entity_id: str,
        expected_version: int,
        values: dict[str, object],
        timestamp: str,
    ) -> int:
        if not values:
            return expected_version
        assignments = [f"{column}=?" for column in values]
        assignments.extend(["version=version+1", "updated_at=?"])
        params = [_db_value(value) for value in values.values()] + [timestamp, entity_id, expected_version]
        cursor = connection.execute(
            f"UPDATE {table} SET {','.join(assignments)} WHERE {id_column}=? AND version=? AND deleted_at IS NULL",
            params,
        )
        if cursor.rowcount != 1:
            raise SyncStalePlanError(f"SYNC-STALE-002: {table} wurde während der Planung verändert")
        return expected_version + 1

    def commit(self, plan: SyncPlan, *, now: datetime) -> SyncAuditReceipt:
        if not plan.write_permitted:
            raise SyncPlanBlockedError(f"SYNC-PLAN-001: Plan ist nicht schreibbar: {plan.blocking_reason}")
        timestamp = now.astimezone(timezone.utc).isoformat()

        with self.database.transaction() as connection:
            snapshot = self._snapshot(connection, plan.link_id)
            if snapshot.detached:
                raise SyncStalePlanError("SYNC-STALE-001: Endpunkt oder Link wurde zwischen Planung und Commit getrennt")
            if snapshot.direction is not plan.direction:
                raise SyncStalePlanError("SYNC-STALE-001: Synchronisationsrichtung wurde geändert")
            if (
                snapshot.todo_version != plan.expected_todo_version
                or snapshot.event_version != plan.expected_event_version
                or snapshot.link_version != plan.expected_link_version
            ):
                raise SyncStalePlanError("SYNC-STALE-001: Objektversionen stimmen nicht mehr mit dem PRECHECK überein")

            plan_fields = {field.field_id: field for field in plan.fields}
            for spec in SYNC_FIELD_SPECS:
                field = plan_fields[spec.field_id]
                if canonical_hash(snapshot.todo_values[spec.field_id]) != field.todo_sha256:
                    raise SyncStalePlanError(f"SYNC-STALE-003: Todo-Feld {spec.field_id} änderte sich nach PRECHECK")
                if canonical_hash(snapshot.calendar_values[spec.field_id]) != field.calendar_sha256:
                    raise SyncStalePlanError(f"SYNC-STALE-003: Kalender-Feld {spec.field_id} änderte sich nach PRECHECK")
                if snapshot.baseline_hashes.get(spec.field_id) != field.baseline_sha256:
                    raise SyncStalePlanError(f"SYNC-STALE-004: Baseline {spec.field_id} änderte sich nach PRECHECK")

            todo_updates: dict[str, object] = {}
            event_updates: dict[str, object] = {}
            for spec in SYNC_FIELD_SPECS:
                field = plan_fields[spec.field_id]
                if field.action is PlanFieldAction.TODO_TO_CALENDAR:
                    event_updates[spec.calendar_field] = field.todo_value
                elif field.action is PlanFieldAction.CALENDAR_TO_TODO:
                    todo_updates[spec.todo_field] = field.calendar_value
                elif field.action in {PlanFieldAction.BLOCKED, PlanFieldAction.REVIEW_REQUIRED}:
                    raise SyncPlanBlockedError(f"SYNC-PLAN-002: Feld {spec.field_id} ist nicht commitfähig")

            todo_after = self._update_entity(
                connection,
                "todos",
                "todo_id",
                snapshot.todo_id,
                snapshot.todo_version,
                todo_updates,
                timestamp,
            )
            event_after = self._update_entity(
                connection,
                "calendar_events",
                "event_id",
                snapshot.event_id,
                snapshot.event_version,
                event_updates,
                timestamp,
            )
            trigger("SYNC_AFTER_ENTITY_WRITE")

            after = self._snapshot(connection, plan.link_id)
            after_hashes: dict[str, str] = {}
            for spec in SYNC_FIELD_SPECS:
                todo_hash = canonical_hash(after.todo_values[spec.field_id])
                calendar_hash = canonical_hash(after.calendar_values[spec.field_id])
                if todo_hash != calendar_hash:
                    raise SyncPostcheckError(
                        f"SYNC-POSTCHECK-001: Feld {spec.field_id} ist nach der Transaktion nicht identisch"
                    )
                after_hashes[spec.field_id] = todo_hash
                encoded = canonical_json(after.todo_values[spec.field_id])
                cursor = connection.execute(
                    """UPDATE sync_field_baselines SET baseline_json=?,baseline_sha256=?,
                       todo_sha256_at_baseline=?,calendar_sha256_at_baseline=?,version=version+1,updated_at=?
                       WHERE link_id=? AND field_id=?""",
                    (encoded, todo_hash, todo_hash, todo_hash, timestamp, plan.link_id, spec.field_id),
                )
                if cursor.rowcount != 1:
                    raise SyncPostcheckError(f"SYNC-POSTCHECK-002: Baseline {spec.field_id} fehlt beim Commit")
            trigger("SYNC_AFTER_BASELINE_WRITE")

            cursor = connection.execute(
                """UPDATE todo_calendar_links SET conflict_status='CLEAN',last_synced_at=?,
                   todo_version_at_sync=?,event_version_at_sync=?,version=version+1,updated_at=?
                   WHERE link_id=? AND version=? AND deleted_at IS NULL""",
                (timestamp, todo_after, event_after, timestamp, plan.link_id, snapshot.link_version),
            )
            if cursor.rowcount != 1:
                raise SyncStalePlanError("SYNC-STALE-005: Link konnte nicht atomar fortgeschrieben werden")
            link_after = snapshot.link_version + 1

            fields_payload = [
                {
                    "field_id": field.field_id,
                    "state": field.state.value,
                    "action": field.action.value,
                    "baseline_before": field.baseline_sha256,
                    "todo_before": field.todo_sha256,
                    "calendar_before": field.calendar_sha256,
                    "baseline_after": after_hashes[field.field_id],
                }
                for field in plan.fields
            ]
            receipt_payload = {
                "schema_version": 1,
                "result": "COMMITTED",
                "link_id": plan.link_id,
                "plan_id": plan.plan_id,
                "precondition_sha256": plan.precondition_sha256,
                "todo_version_before": snapshot.todo_version,
                "todo_version_after": todo_after,
                "event_version_before": snapshot.event_version,
                "event_version_after": event_after,
                "link_version_before": snapshot.link_version,
                "link_version_after": link_after,
                "fields": fields_payload,
                "created_at": timestamp,
            }
            encoded_payload = json.dumps(
                receipt_payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            receipt_digest = payload_hash(receipt_payload)
            receipt_id = str(uuid4())
            trigger("SYNC_BEFORE_RECEIPT")
            connection.execute(
                """INSERT INTO sync_audit_receipts(
                   receipt_id,link_id,plan_id,precondition_sha256,receipt_sha256,result,
                   todo_version_before,todo_version_after,event_version_before,event_version_after,
                   link_version_before,link_version_after,payload_json,created_at
                   ) VALUES (?,?,?,?,?,'COMMITTED',?,?,?,?,?,?,?,?)""",
                (
                    receipt_id,
                    plan.link_id,
                    plan.plan_id,
                    plan.precondition_sha256,
                    receipt_digest,
                    snapshot.todo_version,
                    todo_after,
                    snapshot.event_version,
                    event_after,
                    snapshot.link_version,
                    link_after,
                    encoded_payload,
                    timestamp,
                ),
            )

            verify = self._snapshot(connection, plan.link_id)
            if (
                verify.todo_version != todo_after
                or verify.event_version != event_after
                or verify.link_version != link_after
            ):
                raise SyncPostcheckError("SYNC-POSTCHECK-003: Versions-POSTCHECK fehlgeschlagen")
            for spec in SYNC_FIELD_SPECS:
                digest = canonical_hash(verify.todo_values[spec.field_id])
                if digest != canonical_hash(verify.calendar_values[spec.field_id]):
                    raise SyncPostcheckError(f"SYNC-POSTCHECK-004: Endwerte {spec.field_id} divergieren")
                if verify.baseline_hashes.get(spec.field_id) != digest:
                    raise SyncPostcheckError(
                        f"SYNC-POSTCHECK-005: Baseline {spec.field_id} entspricht nicht dem Endwert"
                    )
            receipt_row = connection.execute(
                "SELECT receipt_sha256 FROM sync_audit_receipts WHERE receipt_id=?",
                (receipt_id,),
            ).fetchone()
            if receipt_row is None or receipt_row["receipt_sha256"] != receipt_digest:
                raise SyncPostcheckError("SYNC-POSTCHECK-006: Audit-Receipt fehlt oder ist inkonsistent")

            before_json = json.dumps(
                snapshot_payload(
                    receipt_id=receipt_id,
                    receipt_sha256=receipt_digest,
                    link_id=plan.link_id,
                    todo_values=snapshot.todo_values,
                    calendar_values=snapshot.calendar_values,
                    baseline_hashes=snapshot.baseline_hashes,
                    todo_version=snapshot.todo_version,
                    event_version=snapshot.event_version,
                    link_version=snapshot.link_version,
                ),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            after_json = json.dumps(
                snapshot_payload(
                    receipt_id=receipt_id,
                    receipt_sha256=receipt_digest,
                    link_id=plan.link_id,
                    todo_values=verify.todo_values,
                    calendar_values=verify.calendar_values,
                    baseline_hashes=verify.baseline_hashes,
                    todo_version=verify.todo_version,
                    event_version=verify.event_version,
                    link_version=verify.link_version,
                ),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            history_digest = snapshot_hash(before_json, after_json, receipt_digest)
            connection.execute(
                """INSERT INTO sync_history_snapshots(
                   receipt_id,link_id,snapshot_sha256,before_json,after_json,created_at
                   ) VALUES (?,?,?,?,?,?)""",
                (receipt_id, plan.link_id, history_digest, before_json, after_json, timestamp),
            )
            history_row = connection.execute(
                "SELECT snapshot_sha256 FROM sync_history_snapshots WHERE receipt_id=?",
                (receipt_id,),
            ).fetchone()
            if history_row is None or history_row["snapshot_sha256"] != history_digest:
                raise SyncPostcheckError("SYNC-HISTORY-POSTCHECK-001: Journal-Snapshot fehlt oder ist inkonsistent")
            trigger("SYNC_AFTER_HISTORY_SNAPSHOT")
            trigger("SYNC_AFTER_RECEIPT_BEFORE_COMMIT")

        return SyncAuditReceipt(
            receipt_id=receipt_id,
            link_id=plan.link_id,
            plan_id=plan.plan_id,
            precondition_sha256=plan.precondition_sha256,
            receipt_sha256=receipt_digest,
            todo_version_before=snapshot.todo_version,
            todo_version_after=todo_after,
            event_version_before=snapshot.event_version,
            event_version_after=event_after,
            link_version_before=snapshot.link_version,
            link_version_after=link_after,
            payload_json=encoded_payload,
            created_at=timestamp,
        )

    def receipt_count(self, link_id: str) -> int:
        with self.database.session() as connection:
            return int(
                connection.execute(
                    "SELECT COUNT(*) FROM sync_audit_receipts WHERE link_id=?",
                    (link_id,),
                ).fetchone()[0]
            )

    def receipt_hashes(self, link_id: str) -> tuple[str, ...]:
        with self.database.session() as connection:
            rows = connection.execute(
                "SELECT receipt_sha256 FROM sync_audit_receipts WHERE link_id=? ORDER BY created_at,receipt_id",
                (link_id,),
            ).fetchall()
        return tuple(row["receipt_sha256"] for row in rows)
