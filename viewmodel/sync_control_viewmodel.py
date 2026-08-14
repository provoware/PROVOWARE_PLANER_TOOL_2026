from __future__ import annotations

from services.resolution_service import ResolutionService
from services.sync_service import SynchronizationService
from sync_core.model import FieldChangeState, SyncAuditReceipt, SyncPlanState
from sync_core.resolution import ResolutionChoice, ResolutionPlan
from viewmodel.sync_control_query import SyncControlQuery, SyncControlSnapshot


class SyncControlViewModel:
    def __init__(
        self,
        query: SyncControlQuery,
        sync_service: SynchronizationService,
        resolution_service: ResolutionService,
    ) -> None:
        self.query = query
        self.sync_service = sync_service
        self.resolution_service = resolution_service
        self.snapshot: SyncControlSnapshot | None = None
        self.decisions: dict[str, ResolutionChoice] = {}
        self.prepared_resolution: ResolutionPlan | None = None

    def link_ids(self) -> tuple[str, ...]:
        return self.query.link_ids()

    def load(self, link_id: str) -> SyncControlSnapshot:
        self.snapshot = self.query.load(link_id)
        self.decisions = {
            field.field_id: ResolutionChoice.KEEP_BLOCKED
            for field in self.snapshot.plan.fields
            if field.state is FieldChangeState.BOTH_DIFFERENT
        }
        self.prepared_resolution = None
        return self.snapshot

    def choose(self, field_id: str, choice: ResolutionChoice) -> None:
        if self.snapshot is None:
            raise ValueError("SYNC-CONTROL-001: Zuerst eine Verknüpfung prüfen.")
        field = next((item for item in self.snapshot.plan.fields if item.field_id == field_id), None)
        if field is None or field.state is not FieldChangeState.BOTH_DIFFERENT:
            raise ValueError("SYNC-CONTROL-002: Entscheidungen sind ausschließlich für BOTH_DIFFERENT zulässig.")
        self.decisions[field_id] = choice
        self.prepared_resolution = None

    def resolution_plan(self) -> ResolutionPlan:
        if self.snapshot is None:
            raise ValueError("SYNC-CONTROL-001: Zuerst eine Verknüpfung prüfen.")
        return self.resolution_service.build(self.snapshot.plan, self.decisions)

    def prepare_resolution(self) -> ResolutionPlan:
        self.prepared_resolution = self.resolution_plan()
        return self.prepared_resolution

    def execute(self) -> SyncAuditReceipt:
        if self.snapshot is None:
            raise ValueError("SYNC-CONTROL-001: Zuerst eine Verknüpfung prüfen.")
        plan = self.snapshot.plan
        if plan.state is SyncPlanState.READY:
            return self.sync_service.commit(plan)
        if plan.state is SyncPlanState.BLOCKED_CONFLICT:
            if self.prepared_resolution is None:
                raise ValueError(
                    "SYNC-CONTROL-004: Entscheidungsplan zuerst prüfen. "
                    "Nach jeder geänderten Auswahl muss der ResolutionPlan neu erzeugt werden."
                )
            return self.resolution_service.commit(self.prepared_resolution)
        raise ValueError(f"SYNC-CONTROL-003: Aktueller Zustand {plan.state.value} ist nicht ausführbar.")
