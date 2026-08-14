from __future__ import annotations

from datetime import datetime, timezone

from storage.sync_repository import SyncRepository, SyncSnapshot
from sync_core.canonical import canonical_hash, payload_hash
from sync_core.fields import SYNC_FIELD_SPECS, SyncFieldSpec
from sync_core.model import (
    FieldChangeState,
    PlanFieldAction,
    SyncAuditReceipt,
    SyncBaseline,
    SyncPlan,
    SyncPlanField,
    SyncPlanState,
)
from todo_core.model import LinkDirection


class SynchronizationService:
    """I009: plant und commitet ausschließlich hashgebundene, transaktional geprüfte Feldänderungen."""

    def __init__(self, repository: SyncRepository) -> None:
        self.repository = repository

    def initialize_baseline(self, link_id: str) -> tuple[SyncBaseline, ...]:
        return self.repository.initialize_baselines(link_id, now=datetime.now(timezone.utc))

    @staticmethod
    def _direction_allows(direction: LinkDirection, action: PlanFieldAction) -> bool:
        if action is PlanFieldAction.TODO_TO_CALENDAR:
            return direction in {LinkDirection.TODO_TO_CALENDAR, LinkDirection.BIDIRECTIONAL}
        if action is PlanFieldAction.CALENDAR_TO_TODO:
            return direction in {LinkDirection.CALENDAR_TO_TODO, LinkDirection.BIDIRECTIONAL}
        return True

    @staticmethod
    def _classify(spec: SyncFieldSpec, snapshot: SyncSnapshot) -> tuple[FieldChangeState, PlanFieldAction, str]:
        baseline = snapshot.baseline_hashes.get(spec.field_id)
        todo_value = snapshot.todo_values[spec.field_id]
        calendar_value = snapshot.calendar_values[spec.field_id]
        todo_hash = canonical_hash(todo_value)
        calendar_hash = canonical_hash(calendar_value)
        if baseline is None:
            return (
                FieldChangeState.BASELINE_MISSING,
                PlanFieldAction.BLOCKED,
                "Für dieses Feld wurde noch keine beweisbare gemeinsame Baseline gebunden.",
            )
        if todo_hash == baseline and calendar_hash == baseline:
            return FieldChangeState.UNCHANGED, PlanFieldAction.NONE, "Beide Seiten entsprechen der gebundenen Baseline."
        if todo_hash != baseline and calendar_hash == baseline:
            state, action = FieldChangeState.TODO_ONLY, PlanFieldAction.TODO_TO_CALENDAR
        elif todo_hash == baseline and calendar_hash != baseline:
            state, action = FieldChangeState.CALENDAR_ONLY, PlanFieldAction.CALENDAR_TO_TODO
        elif todo_hash == calendar_hash:
            return (
                FieldChangeState.BOTH_SAME,
                PlanFieldAction.PROMOTE_BASELINE,
                "Beide Seiten wurden unabhängig auf denselben kanonischen Wert geändert; nur die Baseline wird fortgeschrieben.",
            )
        else:
            return (
                FieldChangeState.BOTH_DIFFERENT,
                PlanFieldAction.BLOCKED,
                "Dasselbe Feld wurde auf beiden Seiten unterschiedlich geändert. Kein verlustfreier Automatismus ist zulässig.",
            )

        if spec.semantic_review_required:
            return (
                state,
                PlanFieldAction.REVIEW_REQUIRED,
                "Fälligkeit und Terminende bleiben semantisch verschieden und benötigen eine ausdrückliche Entscheidung.",
            )
        if not SynchronizationService._direction_allows(snapshot.direction, action):
            return state, PlanFieldAction.BLOCKED, "Die konfigurierte Link-Richtung erlaubt diese Feldübertragung nicht."
        if action is PlanFieldAction.TODO_TO_CALENDAR and spec.calendar_target_requires_value and todo_value is None:
            return state, PlanFieldAction.BLOCKED, "Ein Pflichtfeld des Kalenders darf nicht auf leer gesetzt werden."
        if spec.field_id == "START_AT" and action is PlanFieldAction.TODO_TO_CALENDAR:
            event_end = snapshot.calendar_values["DUE_END"]
            if todo_value is not None and event_end is not None and todo_value > event_end:
                return state, PlanFieldAction.BLOCKED, "Neuer Kalenderstart läge nach dem bestehenden Terminende."
        if spec.field_id == "START_AT" and action is PlanFieldAction.CALENDAR_TO_TODO:
            todo_due = snapshot.todo_values["DUE_END"]
            if todo_due is not None and calendar_value > todo_due:
                return state, PlanFieldAction.BLOCKED, "Neuer Aufgabenstart läge nach der bestehenden Fälligkeit."
        return state, action, "Änderungsseite, Baseline und Synchronisationsrichtung sind eindeutig belegt."

    def plan(self, link_id: str) -> SyncPlan:
        snapshot = self.repository.snapshot(link_id)
        fields: list[SyncPlanField] = []
        for spec in SYNC_FIELD_SPECS:
            state, action, reason = self._classify(spec, snapshot)
            fields.append(
                SyncPlanField(
                    field_id=spec.field_id,
                    todo_field=spec.todo_field,
                    calendar_field=spec.calendar_field,
                    baseline_sha256=snapshot.baseline_hashes.get(spec.field_id),
                    todo_sha256=canonical_hash(snapshot.todo_values[spec.field_id]),
                    calendar_sha256=canonical_hash(snapshot.calendar_values[spec.field_id]),
                    state=state,
                    action=action,
                    todo_value=snapshot.todo_values[spec.field_id],
                    calendar_value=snapshot.calendar_values[spec.field_id],
                    reason=reason,
                )
            )

        if snapshot.detached:
            state = SyncPlanState.BLOCKED_DETACHED
            reason = "Link, Aufgabe oder Termin ist gelöscht/getrennt; Wiederbelebung ist verboten."
        elif any(field.state is FieldChangeState.BASELINE_MISSING for field in fields):
            state = SyncPlanState.BLOCKED_BASELINE
            reason = "Mindestens eine Feld-Baseline fehlt."
        elif any(field.state is FieldChangeState.BOTH_DIFFERENT for field in fields):
            state = SyncPlanState.BLOCKED_CONFLICT
            reason = "Mindestens ein Feld enthält echte beidseitig unterschiedliche Änderungen."
        elif any(field.action is PlanFieldAction.REVIEW_REQUIRED for field in fields):
            state = SyncPlanState.MANUAL_REVIEW
            reason = "Mindestens ein Feld benötigt semantische Prüfung."
        elif any(field.action is PlanFieldAction.BLOCKED for field in fields):
            state = SyncPlanState.BLOCKED_DIRECTION
            reason = "Mindestens eine Änderung verletzt Richtung oder Zielinvarianten."
        elif all(field.state is FieldChangeState.UNCHANGED for field in fields):
            state = SyncPlanState.NO_CHANGE
            reason = "Alle Felder entsprechen der Baseline."
        else:
            state = SyncPlanState.READY
            reason = "Alle Änderungen sind feldweise beweisbar, richtungskonform und transaktional ausführbar."

        precondition_payload = {
            "link_id": snapshot.link_id,
            "direction": snapshot.direction.value,
            "todo_version": snapshot.todo_version,
            "event_version": snapshot.event_version,
            "link_version": snapshot.link_version,
            "fields": [
                {
                    "field_id": field.field_id,
                    "baseline": field.baseline_sha256,
                    "todo": field.todo_sha256,
                    "calendar": field.calendar_sha256,
                    "state": field.state.value,
                    "action": field.action.value,
                }
                for field in fields
            ],
        }
        precondition = payload_hash(precondition_payload)
        plan_payload = {**precondition_payload, "plan_state": state.value, "precondition": precondition}
        plan_id = f"SYNCPLAN-{payload_hash(plan_payload)[:32]}"
        return SyncPlan(
            plan_id=plan_id,
            link_id=snapshot.link_id,
            direction=snapshot.direction,
            state=state,
            expected_todo_version=snapshot.todo_version,
            expected_event_version=snapshot.event_version,
            expected_link_version=snapshot.link_version,
            fields=tuple(fields),
            precondition_sha256=precondition,
            write_permitted=state is SyncPlanState.READY,
            blocking_reason=reason,
        )

    def commit(self, plan: SyncPlan) -> SyncAuditReceipt:
        receipt = self.repository.commit(plan, now=datetime.now(timezone.utc))
        self.repository.database.quick_check()
        return receipt

    def baselines(self, link_id: str) -> tuple[SyncBaseline, ...]:
        return self.repository.baselines(link_id)

    def receipt_count(self, link_id: str) -> int:
        return self.repository.receipt_count(link_id)

    @staticmethod
    def feedback(plan: SyncPlan) -> tuple[str, ...]:
        header = f"SYNCPLAN {plan.plan_id}: {plan.state.value} – {plan.blocking_reason}"
        details = tuple(
            f"{field.field_id}: {field.state.value} / {field.action.value} – {field.reason}"
            for field in plan.fields
        )
        return (header, *details)
