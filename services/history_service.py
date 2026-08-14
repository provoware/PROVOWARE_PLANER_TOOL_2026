from __future__ import annotations

from datetime import datetime, timezone

from sync_core.canonical import canonical_hash, payload_hash
from sync_core.history import (
    JournalIntegrityState,
    JournalRecord,
    RecoveryMode,
    RecoveryPlan,
    RecoveryPlanField,
    RecoveryPlanState,
    recovery_payload,
    sync_plan_hash,
    to_execution_plan,
)
from sync_core.model import PlanFieldAction, SyncAuditReceipt, SyncPlan
from sync_core.errors import SyncPlanBlockedError, SyncStalePlanError
from storage.history_repository import SyncHistoryRepository
from storage.sync_repository import SyncRepository
from services.sync_service import SynchronizationService
from todo_core.model import LinkDirection


class SyncJournalService:
    """I011: verifiziert Journalnachweise und erzeugt stale-sichere Recovery-Pläne."""

    def __init__(
        self,
        sync_service: SynchronizationService,
        sync_repository: SyncRepository,
        history_repository: SyncHistoryRepository,
    ) -> None:
        self.sync_service = sync_service
        self.sync_repository = sync_repository
        self.history_repository = history_repository

    def list_records(self, link_id: str | None = None) -> tuple[JournalRecord, ...]:
        return self.history_repository.list_records(link_id)

    def get_record(self, receipt_id: str) -> JournalRecord:
        return self.history_repository.get_record(receipt_id)

    @staticmethod
    def _direction_allows(direction: LinkDirection, action: PlanFieldAction) -> bool:
        if action is PlanFieldAction.TODO_TO_CALENDAR:
            return direction in {LinkDirection.TODO_TO_CALENDAR, LinkDirection.BIDIRECTIONAL}
        if action is PlanFieldAction.CALENDAR_TO_TODO:
            return direction in {LinkDirection.CALENDAR_TO_TODO, LinkDirection.BIDIRECTIONAL}
        return True

    @staticmethod
    def _target_values(
        source: JournalRecord,
        mode: RecoveryMode,
    ) -> tuple[dict[str, object] | None, list[str]]:
        blockers: list[str] = []
        if source.integrity is JournalIntegrityState.TAMPERED:
            return None, ["Der ausgewählte Journalnachweis ist manipuliert oder inkonsistent."]
        if not source.recovery_available:
            return None, [
                "Dieser ältere Journalnachweis besitzt keinen I011-Wertsnapshot. "
                "Es werden keine historischen Werte erfunden."
            ]

        if mode is RecoveryMode.REAPPLY_AFTER:
            todo_values = dict(source.after_todo_values or {})
            calendar_values = dict(source.after_calendar_values or {})
        else:
            todo_values = dict(source.before_todo_values or {})
            calendar_values = dict(source.before_calendar_values or {})

        targets: dict[str, object] = {}
        for field_id in sorted(set(todo_values) | set(calendar_values)):
            if field_id not in todo_values or field_id not in calendar_values:
                blockers.append(f"{field_id}: historischer Wert ist unvollständig.")
                continue
            if canonical_hash(todo_values[field_id]) != canonical_hash(calendar_values[field_id]):
                blockers.append(
                    f"{field_id}: Todo und Kalender waren im gewählten historischen Zustand unterschiedlich. "
                    "Dieser divergente Zustand wird nicht automatisch rekonstruiert."
                )
                continue
            targets[field_id] = todo_values[field_id]
        return targets, blockers

    def build_recovery(self, receipt_id: str, mode: RecoveryMode) -> RecoveryPlan:
        source = self.history_repository.get_record(receipt_id)
        current = self.sync_service.plan(source.link_id)
        targets, blockers = self._target_values(source, mode)
        target_map = targets or {}

        fields: list[RecoveryPlanField] = []
        for field in current.fields:
            target_value = target_map.get(field.field_id, field.todo_value)
            target_sha = canonical_hash(target_value)
            action = PlanFieldAction.BLOCKED
            reason = "Historischer Zielwert ist für dieses Feld nicht sicher verfügbar."

            if field.baseline_sha256 is None:
                blockers.append(f"{field.field_id}: aktuelle Baseline fehlt.")
            elif field.field_id not in target_map:
                blockers.append(f"{field.field_id}: kein eindeutiger historischer Zielwert.")
            else:
                todo_match = field.todo_sha256 == target_sha
                calendar_match = field.calendar_sha256 == target_sha
                if todo_match and calendar_match:
                    action = PlanFieldAction.NONE
                    reason = "Beide Seiten entsprechen bereits dem historischen Zielwert."
                elif field.field_id == "DUE_END":
                    blockers.append(
                        "DUE_END: Terminende/Fälligkeit bleibt auch bei Recovery semantisch prüfpflichtig."
                    )
                    reason = "Zeitsemantik verhindert automatische Recovery-Ausführung."
                elif todo_match and self._direction_allows(current.direction, PlanFieldAction.TODO_TO_CALENDAR):
                    action = PlanFieldAction.TODO_TO_CALENDAR
                    reason = "Der aktuelle Todo-Wert entspricht beweisbar dem historischen Zielwert."
                elif calendar_match and self._direction_allows(current.direction, PlanFieldAction.CALENDAR_TO_TODO):
                    action = PlanFieldAction.CALENDAR_TO_TODO
                    reason = "Der aktuelle Kalender-Wert entspricht beweisbar dem historischen Zielwert."
                elif todo_match or calendar_match:
                    blockers.append(f"{field.field_id}: Link-Richtung erlaubt die nötige Übertragung nicht.")
                    reason = "Historischer Zielwert ist vorhanden, aber die Link-Richtung blockiert den Write."
                else:
                    blockers.append(
                        f"{field.field_id}: historischer Zielwert ist auf keiner aktuellen Seite mehr vorhanden."
                    )
                    reason = (
                        "I011 schreibt keine alten Werte frei aus dem Journal zurück; "
                        "der Zielwert muss aktuell auf Todo oder Kalender beweisbar vorhanden sein."
                    )

            fields.append(
                RecoveryPlanField(
                    field_id=field.field_id,
                    todo_field=field.todo_field,
                    calendar_field=field.calendar_field,
                    baseline_sha256=field.baseline_sha256,
                    todo_sha256=field.todo_sha256,
                    calendar_sha256=field.calendar_sha256,
                    original_state=field.state,
                    target_sha256=target_sha,
                    target_value=target_value,
                    resolved_action=action,
                    todo_value=field.todo_value,
                    calendar_value=field.calendar_value,
                    reason=reason,
                )
            )

        if current.state.value == "BLOCKED_DETACHED":
            blockers.append("Die Verknüpfung oder ein Endpunkt ist getrennt/gelöscht.")

        fields_tuple = tuple(fields)
        if source.snapshot_sha256 is None:
            blockers.append("Kein Snapshot-Hash vorhanden.")

        payload = recovery_payload(source, current, mode, fields_tuple)
        digest = payload_hash(payload)
        state = RecoveryPlanState.READY if not blockers else RecoveryPlanState.BLOCKED
        return RecoveryPlan(
            recovery_plan_id=f"RECOVERYPLAN-{digest[:32]}",
            source_receipt_id=source.receipt_id,
            source_receipt_sha256=source.receipt_sha256,
            source_snapshot_sha256=source.snapshot_sha256,
            source_plan_id=source.plan_id,
            current_sync_plan_id=current.plan_id,
            current_sync_plan_sha256=sync_plan_hash(current),
            current_precondition_sha256=current.precondition_sha256,
            link_id=current.link_id,
            direction=current.direction,
            mode=mode,
            state=state,
            expected_todo_version=current.expected_todo_version,
            expected_event_version=current.expected_event_version,
            expected_link_version=current.expected_link_version,
            fields=fields_tuple,
            recovery_sha256=digest,
            write_permitted=state is RecoveryPlanState.READY,
            blocking_reason=(
                "RecoveryPlan ist vollständig hashgebunden und kann über den bestehenden I009-Transaktionskern laufen."
                if state is RecoveryPlanState.READY
                else "; ".join(dict.fromkeys(blockers))
            ),
        )

    def commit_recovery(self, plan: RecoveryPlan) -> SyncAuditReceipt:
        source = self.history_repository.get_record(plan.source_receipt_id)
        if source.receipt_sha256 != plan.source_receipt_sha256:
            raise SyncStalePlanError("RECOVERY-STALE-001: Quell-Receipt hat sich verändert")
        if source.snapshot_sha256 != plan.source_snapshot_sha256:
            raise SyncStalePlanError("RECOVERY-STALE-002: Quell-Snapshot hat sich verändert")

        current = self.sync_service.plan(plan.link_id)
        if sync_plan_hash(current) != plan.current_sync_plan_sha256:
            raise SyncStalePlanError(
                "RECOVERY-STALE-003: Aktueller SyncPlan hat sich seit der Recovery-Vorschau verändert"
            )
        expected = self.build_recovery(plan.source_receipt_id, plan.mode)
        if expected != plan:
            raise SyncStalePlanError(
                "RECOVERY-TAMPER-004: RecoveryPlan wurde verändert oder ist nicht mehr autoritativ"
            )
        if not plan.write_permitted:
            raise SyncPlanBlockedError(f"RECOVERY-BLOCKED-005: {plan.blocking_reason}")

        receipt = self.sync_repository.commit(to_execution_plan(plan), now=datetime.now(timezone.utc))
        self.sync_repository.database.quick_check()
        return receipt
