from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping

from storage.sync_repository import SyncRepository
from sync_core.canonical import payload_hash
from sync_core.errors import SyncPlanBlockedError, SyncStalePlanError
from sync_core.model import FieldChangeState, PlanFieldAction, SyncAuditReceipt, SyncPlan, SyncPlanState
from sync_core.resolution import (
    ResolutionChoice,
    ResolutionPlan,
    ResolutionPlanField,
    ResolutionPlanState,
    resolution_payload,
    sync_plan_hash,
    to_execution_plan,
)
from todo_core.model import LinkDirection

from services.sync_service import SynchronizationService


def list_active_link_ids(sync_service: SynchronizationService) -> tuple[str, ...]:
    """Read-only Serviceprojektion für aktive Todo-Kalender-Verknüpfungen."""
    with sync_service.repository.database.session() as connection:
        rows = connection.execute(
            "SELECT link_id FROM todo_calendar_links WHERE deleted_at IS NULL ORDER BY created_at, link_id"
        ).fetchall()
    return tuple(row["link_id"] for row in rows)


class ResolutionService:
    """I010: erzeugt und commitet ausschließlich explizit entschiedene, hashgebundene Konfliktpläne."""

    def __init__(self, sync_service: SynchronizationService, repository: SyncRepository) -> None:
        self.sync_service = sync_service
        self.repository = repository

    @staticmethod
    def _direction_allows(direction: LinkDirection, action: PlanFieldAction) -> bool:
        if action is PlanFieldAction.TODO_TO_CALENDAR:
            return direction in {LinkDirection.TODO_TO_CALENDAR, LinkDirection.BIDIRECTIONAL}
        if action is PlanFieldAction.CALENDAR_TO_TODO:
            return direction in {LinkDirection.CALENDAR_TO_TODO, LinkDirection.BIDIRECTIONAL}
        return True

    def build(
        self,
        source_plan: SyncPlan,
        decisions: Mapping[str, ResolutionChoice],
    ) -> ResolutionPlan:
        if source_plan.state is not SyncPlanState.BLOCKED_CONFLICT:
            raise SyncPlanBlockedError(
                "RESOLUTION-SOURCE-001: Ein ResolutionPlan darf nur aus einem aktuellen BOTH_DIFFERENT-SyncPlan entstehen"
            )

        resolved_fields: list[ResolutionPlanField] = []
        blockers: list[str] = []
        for field in source_plan.fields:
            choice: ResolutionChoice | None = None
            action = field.action
            reason = field.reason

            if field.state is FieldChangeState.BOTH_DIFFERENT:
                choice = decisions.get(field.field_id, ResolutionChoice.KEEP_BLOCKED)
                if choice is ResolutionChoice.TODO_VALUE:
                    action = PlanFieldAction.TODO_TO_CALENDAR
                    reason = "Explizite Entscheidung: Der Todo-Wert wird als gemeinsamer Endwert übernommen."
                elif choice is ResolutionChoice.CALENDAR_VALUE:
                    action = PlanFieldAction.CALENDAR_TO_TODO
                    reason = "Explizite Entscheidung: Der Kalender-Wert wird als gemeinsamer Endwert übernommen."
                else:
                    action = PlanFieldAction.BLOCKED
                    reason = "Konflikt bleibt ausdrücklich blockiert; es wird nichts geschrieben."

                if action is not PlanFieldAction.BLOCKED and not self._direction_allows(source_plan.direction, action):
                    action = PlanFieldAction.BLOCKED
                    reason = "Die explizite Wahl widerspricht der verbindlichen Link-Richtung."
                    blockers.append(f"{field.field_id}: Richtung blockiert")
                elif action is PlanFieldAction.BLOCKED:
                    blockers.append(f"{field.field_id}: keine Schreibfreigabe")

            elif field.action in {PlanFieldAction.BLOCKED, PlanFieldAction.REVIEW_REQUIRED}:
                blockers.append(f"{field.field_id}: bestehende I009-Prüfung bleibt offen")

            resolved_fields.append(
                ResolutionPlanField(
                    field_id=field.field_id,
                    todo_field=field.todo_field,
                    calendar_field=field.calendar_field,
                    baseline_sha256=field.baseline_sha256,
                    todo_sha256=field.todo_sha256,
                    calendar_sha256=field.calendar_sha256,
                    original_state=field.state,
                    original_action=field.action,
                    choice=choice,
                    resolved_action=action,
                    todo_value=field.todo_value,
                    calendar_value=field.calendar_value,
                    reason=reason,
                )
            )

        fields = tuple(resolved_fields)

        projected: dict[str, object] = {}
        for field in fields:
            if field.resolved_action is PlanFieldAction.TODO_TO_CALENDAR:
                projected[field.field_id] = field.todo_value
            elif field.resolved_action is PlanFieldAction.CALENDAR_TO_TODO:
                projected[field.field_id] = field.calendar_value
            elif field.resolved_action in {PlanFieldAction.NONE, PlanFieldAction.PROMOTE_BASELINE}:
                projected[field.field_id] = field.todo_value

        from sync_core.fields import SYNC_FIELD_SPECS
        specs = {spec.field_id: spec for spec in SYNC_FIELD_SPECS}
        for field in fields:
            spec = specs[field.field_id]
            if (
                field.resolved_action is PlanFieldAction.TODO_TO_CALENDAR
                and spec.calendar_target_requires_value
                and field.todo_value is None
            ):
                blockers.append(f"{field.field_id}: Kalender-Pflichtwert darf nicht leer werden")

        start_value = projected.get("START_AT")
        end_value = projected.get("DUE_END")
        if start_value is not None and end_value is not None and start_value > end_value:
            blockers.append("Zeitfolge: Start läge nach Fälligkeit/Terminende")

        payload = resolution_payload(source_plan, fields)
        digest = payload_hash(payload)
        state = ResolutionPlanState.READY if not blockers else ResolutionPlanState.BLOCKED
        blocking_reason = (
            "Alle echten Feldkonflikte wurden explizit entschieden und bleiben an den ursprünglichen SyncPlan gebunden."
            if state is ResolutionPlanState.READY
            else "; ".join(blockers)
        )
        return ResolutionPlan(
            resolution_plan_id=f"RESOLUTIONPLAN-{digest[:32]}",
            source_plan_id=source_plan.plan_id,
            source_plan_sha256=sync_plan_hash(source_plan),
            source_precondition_sha256=source_plan.precondition_sha256,
            link_id=source_plan.link_id,
            direction=source_plan.direction,
            state=state,
            expected_todo_version=source_plan.expected_todo_version,
            expected_event_version=source_plan.expected_event_version,
            expected_link_version=source_plan.expected_link_version,
            fields=fields,
            resolution_sha256=digest,
            write_permitted=state is ResolutionPlanState.READY,
            blocking_reason=blocking_reason,
        )

    def commit(self, plan: ResolutionPlan) -> SyncAuditReceipt:
        authoritative_source = self.sync_service.plan(plan.link_id)
        if sync_plan_hash(authoritative_source) != plan.source_plan_sha256:
            raise SyncStalePlanError(
                "RESOLUTION-STALE-002: Der zugrunde liegende SyncPlan hat sich seit der Konfliktentscheidung verändert"
            )
        if authoritative_source.plan_id != plan.source_plan_id:
            raise SyncStalePlanError("RESOLUTION-STALE-003: Source-Plan-ID stimmt nicht mehr")
        decisions = {
            field.field_id: field.choice
            for field in plan.fields
            if field.choice is not None
        }
        expected = self.build(authoritative_source, decisions)
        if expected != plan:
            raise SyncStalePlanError(
                "RESOLUTION-TAMPER-004: Der ResolutionPlan wurde verändert oder entspricht nicht der autoritativen Entscheidung"
            )
        if not plan.write_permitted:
            raise SyncPlanBlockedError(f"RESOLUTION-BLOCKED-005: {plan.blocking_reason}")

        receipt = self.repository.commit(to_execution_plan(plan), now=datetime.now(timezone.utc))
        self.repository.database.quick_check()
        return receipt
