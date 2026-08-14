from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from todo_core.model import LinkConflictStatus, LinkDirection


class SyncFieldAction(StrEnum):
    IDENTISCH = "IDENTISCH"
    TODO_ZU_KALENDER = "TODO_ZU_KALENDER"
    KALENDER_ZU_TODO = "KALENDER_ZU_TODO"
    PRUEFUNG_ERFORDERLICH = "PRUEFUNG_ERFORDERLICH"
    BLOCKIERT = "BLOCKIERT"


class SyncPreviewState(StrEnum):
    KEINE_AENDERUNG = "KEINE_AENDERUNG"
    VORSCHLAG_BEREIT = "VORSCHLAG_BEREIT"
    MANUELLE_PRUEFUNG = "MANUELLE_PRUEFUNG"
    BLOCKIERT_BEIDSEITIG = "BLOCKIERT_BEIDSEITIG"
    BLOCKIERT_GETRENNT = "BLOCKIERT_GETRENNT"
    BLOCKIERT_RICHTUNG = "BLOCKIERT_RICHTUNG"
    BLOCKIERT_BASISABWEICHUNG = "BLOCKIERT_BASISABWEICHUNG"


@dataclass(frozen=True, slots=True)
class SyncFieldPreview:
    field_id: str
    todo_field: str
    calendar_field: str
    todo_value: object
    calendar_value: object
    action: SyncFieldAction
    reason: str
    automatic_candidate: bool = False


@dataclass(frozen=True, slots=True)
class SyncPreview:
    link_id: str
    state: SyncPreviewState
    conflict_status: LinkConflictStatus
    direction: LinkDirection
    todo_version: int
    calendar_version: int
    todo_version_at_sync: int
    calendar_version_at_sync: int
    fields: tuple[SyncFieldPreview, ...]
    write_permitted: bool = False
    blocking_reason: str = ""

    @property
    def has_differences(self) -> bool:
        return any(field.action is not SyncFieldAction.IDENTISCH for field in self.fields)

    @property
    def proposed_change_count(self) -> int:
        return sum(
            field.action in {SyncFieldAction.TODO_ZU_KALENDER, SyncFieldAction.KALENDER_ZU_TODO}
            for field in self.fields
        )


class FieldChangeState(StrEnum):
    UNCHANGED = "UNCHANGED"
    TODO_ONLY = "TODO_ONLY"
    CALENDAR_ONLY = "CALENDAR_ONLY"
    BOTH_SAME = "BOTH_SAME"
    BOTH_DIFFERENT = "BOTH_DIFFERENT"
    BASELINE_MISSING = "BASELINE_MISSING"


class PlanFieldAction(StrEnum):
    NONE = "NONE"
    TODO_TO_CALENDAR = "TODO_TO_CALENDAR"
    CALENDAR_TO_TODO = "CALENDAR_TO_TODO"
    PROMOTE_BASELINE = "PROMOTE_BASELINE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    BLOCKED = "BLOCKED"


class SyncPlanState(StrEnum):
    NO_CHANGE = "NO_CHANGE"
    READY = "READY"
    BLOCKED_CONFLICT = "BLOCKED_CONFLICT"
    BLOCKED_DIRECTION = "BLOCKED_DIRECTION"
    BLOCKED_BASELINE = "BLOCKED_BASELINE"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    BLOCKED_DETACHED = "BLOCKED_DETACHED"


@dataclass(frozen=True, slots=True)
class SyncBaseline:
    link_id: str
    field_id: str
    baseline_json: str
    baseline_sha256: str
    version: int


@dataclass(frozen=True, slots=True)
class SyncPlanField:
    field_id: str
    todo_field: str
    calendar_field: str
    baseline_sha256: str | None
    todo_sha256: str
    calendar_sha256: str
    state: FieldChangeState
    action: PlanFieldAction
    todo_value: object
    calendar_value: object
    reason: str


@dataclass(frozen=True, slots=True)
class SyncPlan:
    plan_id: str
    link_id: str
    direction: LinkDirection
    state: SyncPlanState
    expected_todo_version: int
    expected_event_version: int
    expected_link_version: int
    fields: tuple[SyncPlanField, ...]
    precondition_sha256: str
    write_permitted: bool
    blocking_reason: str = ""

    @property
    def changed_field_count(self) -> int:
        return sum(field.state is not FieldChangeState.UNCHANGED for field in self.fields)

    @property
    def entity_write_count(self) -> int:
        return sum(
            field.action in {PlanFieldAction.TODO_TO_CALENDAR, PlanFieldAction.CALENDAR_TO_TODO}
            for field in self.fields
        )


@dataclass(frozen=True, slots=True)
class SyncAuditReceipt:
    receipt_id: str
    link_id: str
    plan_id: str
    precondition_sha256: str
    receipt_sha256: str
    todo_version_before: int
    todo_version_after: int
    event_version_before: int
    event_version_after: int
    link_version_before: int
    link_version_after: int
    payload_json: str
    created_at: str
