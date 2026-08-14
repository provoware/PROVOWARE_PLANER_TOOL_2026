from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Mapping

from sync_core.canonical import canonical_json, payload_hash
from sync_core.model import FieldChangeState, PlanFieldAction, SyncPlan, SyncPlanField
from todo_core.model import LinkDirection


class JournalIntegrityState(StrEnum):
    VERIFIED = "VERIFIED"
    LEGACY_NO_SNAPSHOT = "LEGACY_NO_SNAPSHOT"
    TAMPERED = "TAMPERED"


class JournalPlanKind(StrEnum):
    SYNC = "SYNC"
    RESOLUTION = "RESOLUTION"
    RECOVERY = "RECOVERY"


class RecoveryMode(StrEnum):
    REAPPLY_AFTER = "NACHHER_ERNEUT_ANWENDEN"
    RESTORE_BEFORE = "VORHER_WIEDERHERSTELLEN"


class RecoveryPlanState(StrEnum):
    READY = "READY"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class JournalRecord:
    receipt_id: str
    link_id: str
    plan_id: str
    precondition_sha256: str
    receipt_sha256: str
    payload_json: str
    created_at: str
    todo_version_before: int
    todo_version_after: int
    event_version_before: int
    event_version_after: int
    link_version_before: int
    link_version_after: int
    plan_kind: JournalPlanKind
    integrity: JournalIntegrityState
    integrity_reason: str
    snapshot_sha256: str | None
    before_todo_values: Mapping[str, object] | None
    before_calendar_values: Mapping[str, object] | None
    after_todo_values: Mapping[str, object] | None
    after_calendar_values: Mapping[str, object] | None

    @property
    def recovery_available(self) -> bool:
        return (
            self.integrity is JournalIntegrityState.VERIFIED
            and self.snapshot_sha256 is not None
            and self.before_todo_values is not None
            and self.before_calendar_values is not None
            and self.after_todo_values is not None
            and self.after_calendar_values is not None
        )


@dataclass(frozen=True, slots=True)
class RecoveryPlanField:
    field_id: str
    todo_field: str
    calendar_field: str
    baseline_sha256: str | None
    todo_sha256: str
    calendar_sha256: str
    original_state: FieldChangeState
    target_sha256: str
    target_value: object
    resolved_action: PlanFieldAction
    todo_value: object
    calendar_value: object
    reason: str


@dataclass(frozen=True, slots=True)
class RecoveryPlan:
    recovery_plan_id: str
    source_receipt_id: str
    source_receipt_sha256: str
    source_snapshot_sha256: str | None
    source_plan_id: str
    current_sync_plan_id: str
    current_sync_plan_sha256: str
    current_precondition_sha256: str
    link_id: str
    direction: LinkDirection
    mode: RecoveryMode
    state: RecoveryPlanState
    expected_todo_version: int
    expected_event_version: int
    expected_link_version: int
    fields: tuple[RecoveryPlanField, ...]
    recovery_sha256: str
    write_permitted: bool
    blocking_reason: str = ""


def _decode_canonical(encoded: str) -> object:
    item = json.loads(encoded)
    kind = item.get("type")
    value = item.get("value")
    if kind == "datetime":
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("SYNC-HISTORY-001: gespeicherter Zeitpunkt besitzt keine Zeitzone")
        return parsed
    if kind == "null":
        return None
    if kind == "bool":
        return bool(value)
    if kind == "int":
        return int(value)
    if kind == "float":
        return float(value)
    if kind == "str":
        return str(value)
    raise ValueError(f"SYNC-HISTORY-001: unbekannter kanonischer Typ {kind!r}")


def decode_snapshot(encoded: str) -> tuple[dict[str, object], dict[str, object], dict[str, str | None]]:
    data = json.loads(encoded)
    if data.get("schema_version") != 1:
        raise ValueError("SYNC-HISTORY-001: Snapshot-Schema wird nicht unterstützt")
    todo = data.get("todo_fields")
    calendar = data.get("calendar_fields")
    baselines = data.get("baseline_hashes")
    if not isinstance(todo, dict) or not isinstance(calendar, dict) or not isinstance(baselines, dict):
        raise ValueError("SYNC-HISTORY-001: Snapshot-Felder fehlen")
    return (
        {field_id: _decode_canonical(value_json) for field_id, value_json in todo.items()},
        {field_id: _decode_canonical(value_json) for field_id, value_json in calendar.items()},
        {str(field_id): (None if value is None else str(value)) for field_id, value in baselines.items()},
    )


def snapshot_payload(
    *,
    receipt_id: str,
    receipt_sha256: str,
    link_id: str,
    todo_values: Mapping[str, object],
    calendar_values: Mapping[str, object],
    baseline_hashes: Mapping[str, str | None],
    todo_version: int,
    event_version: int,
    link_version: int,
) -> dict:
    keys = sorted(set(todo_values) | set(calendar_values) | set(baseline_hashes))
    return {
        "schema_version": 1,
        "receipt_id": receipt_id,
        "receipt_sha256": receipt_sha256,
        "link_id": link_id,
        "todo_version": todo_version,
        "event_version": event_version,
        "link_version": link_version,
        "todo_fields": {key: canonical_json(todo_values[key]) for key in keys},
        "calendar_fields": {key: canonical_json(calendar_values[key]) for key in keys},
        "baseline_hashes": {key: baseline_hashes.get(key) for key in keys},
    }


def snapshot_hash(before_json: str, after_json: str, receipt_sha256: str) -> str:
    return payload_hash(
        {
            "schema_version": 1,
            "receipt_sha256": receipt_sha256,
            "before_json": before_json,
            "after_json": after_json,
        }
    )


def recovery_payload(
    source: JournalRecord,
    current_plan: SyncPlan,
    mode: RecoveryMode,
    fields: tuple[RecoveryPlanField, ...],
) -> dict:
    return {
        "source_receipt_id": source.receipt_id,
        "source_receipt_sha256": source.receipt_sha256,
        "source_snapshot_sha256": source.snapshot_sha256,
        "source_plan_id": source.plan_id,
        "current_sync_plan_id": current_plan.plan_id,
        "current_sync_plan_sha256": sync_plan_hash(current_plan),
        "current_precondition_sha256": current_plan.precondition_sha256,
        "link_id": current_plan.link_id,
        "direction": current_plan.direction.value,
        "mode": mode.value,
        "expected_todo_version": current_plan.expected_todo_version,
        "expected_event_version": current_plan.expected_event_version,
        "expected_link_version": current_plan.expected_link_version,
        "fields": [
            {
                "field_id": field.field_id,
                "baseline_sha256": field.baseline_sha256,
                "todo_sha256": field.todo_sha256,
                "calendar_sha256": field.calendar_sha256,
                "original_state": field.original_state.value,
                "target_sha256": field.target_sha256,
                "resolved_action": field.resolved_action.value,
            }
            for field in fields
        ],
    }


def sync_plan_hash(plan: SyncPlan) -> str:
    from sync_core.resolution import sync_plan_hash as _hash

    return _hash(plan)


def to_execution_plan(plan: RecoveryPlan) -> SyncPlan:
    from sync_core.model import SyncPlanState

    return SyncPlan(
        plan_id=plan.recovery_plan_id,
        link_id=plan.link_id,
        direction=plan.direction,
        state=SyncPlanState.READY,
        expected_todo_version=plan.expected_todo_version,
        expected_event_version=plan.expected_event_version,
        expected_link_version=plan.expected_link_version,
        fields=tuple(
            SyncPlanField(
                field_id=field.field_id,
                todo_field=field.todo_field,
                calendar_field=field.calendar_field,
                baseline_sha256=field.baseline_sha256,
                todo_sha256=field.todo_sha256,
                calendar_sha256=field.calendar_sha256,
                state=field.original_state,
                action=field.resolved_action,
                todo_value=field.todo_value,
                calendar_value=field.calendar_value,
                reason=field.reason,
            )
            for field in plan.fields
        ),
        precondition_sha256=plan.recovery_sha256,
        write_permitted=plan.write_permitted,
        blocking_reason=plan.blocking_reason,
    )
