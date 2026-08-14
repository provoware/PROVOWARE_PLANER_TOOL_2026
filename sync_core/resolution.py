from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from sync_core.canonical import payload_hash
from sync_core.model import FieldChangeState, PlanFieldAction, SyncPlan, SyncPlanField
from todo_core.model import LinkDirection


class ResolutionChoice(StrEnum):
    TODO_VALUE = "TODO_WERT"
    CALENDAR_VALUE = "KALENDER_WERT"
    KEEP_BLOCKED = "BLOCKIERT_LASSEN"


class ResolutionPlanState(StrEnum):
    READY = "READY"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class ResolutionPlanField:
    field_id: str
    todo_field: str
    calendar_field: str
    baseline_sha256: str | None
    todo_sha256: str
    calendar_sha256: str
    original_state: FieldChangeState
    original_action: PlanFieldAction
    choice: ResolutionChoice | None
    resolved_action: PlanFieldAction
    todo_value: object
    calendar_value: object
    reason: str


@dataclass(frozen=True, slots=True)
class ResolutionPlan:
    resolution_plan_id: str
    source_plan_id: str
    source_plan_sha256: str
    source_precondition_sha256: str
    link_id: str
    direction: LinkDirection
    state: ResolutionPlanState
    expected_todo_version: int
    expected_event_version: int
    expected_link_version: int
    fields: tuple[ResolutionPlanField, ...]
    resolution_sha256: str
    write_permitted: bool
    blocking_reason: str = ""

    @property
    def explicit_decision_count(self) -> int:
        return sum(field.choice in {ResolutionChoice.TODO_VALUE, ResolutionChoice.CALENDAR_VALUE} for field in self.fields)


def sync_plan_payload(plan: SyncPlan) -> dict:
    return {
        "plan_id": plan.plan_id,
        "link_id": plan.link_id,
        "direction": plan.direction.value,
        "state": plan.state.value,
        "expected_todo_version": plan.expected_todo_version,
        "expected_event_version": plan.expected_event_version,
        "expected_link_version": plan.expected_link_version,
        "precondition_sha256": plan.precondition_sha256,
        "write_permitted": plan.write_permitted,
        "fields": [
            {
                "field_id": field.field_id,
                "baseline_sha256": field.baseline_sha256,
                "todo_sha256": field.todo_sha256,
                "calendar_sha256": field.calendar_sha256,
                "state": field.state.value,
                "action": field.action.value,
            }
            for field in plan.fields
        ],
    }


def sync_plan_hash(plan: SyncPlan) -> str:
    return payload_hash(sync_plan_payload(plan))


def resolution_payload(
    source_plan: SyncPlan,
    fields: tuple[ResolutionPlanField, ...],
) -> dict:
    return {
        "source_plan_id": source_plan.plan_id,
        "source_plan_sha256": sync_plan_hash(source_plan),
        "source_precondition_sha256": source_plan.precondition_sha256,
        "link_id": source_plan.link_id,
        "direction": source_plan.direction.value,
        "expected_todo_version": source_plan.expected_todo_version,
        "expected_event_version": source_plan.expected_event_version,
        "expected_link_version": source_plan.expected_link_version,
        "fields": [
            {
                "field_id": field.field_id,
                "baseline_sha256": field.baseline_sha256,
                "todo_sha256": field.todo_sha256,
                "calendar_sha256": field.calendar_sha256,
                "original_state": field.original_state.value,
                "original_action": field.original_action.value,
                "choice": field.choice.value if field.choice is not None else None,
                "resolved_action": field.resolved_action.value,
            }
            for field in fields
        ],
    }


def to_execution_plan(plan: ResolutionPlan) -> SyncPlan:
    fields = tuple(
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
    )
    from sync_core.model import SyncPlanState

    return SyncPlan(
        plan_id=plan.resolution_plan_id,
        link_id=plan.link_id,
        direction=plan.direction,
        state=SyncPlanState.READY,
        expected_todo_version=plan.expected_todo_version,
        expected_event_version=plan.expected_event_version,
        expected_link_version=plan.expected_link_version,
        fields=fields,
        precondition_sha256=plan.resolution_sha256,
        write_permitted=plan.write_permitted,
        blocking_reason=plan.blocking_reason,
    )
