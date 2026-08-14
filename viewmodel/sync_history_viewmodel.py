from __future__ import annotations

from services.history_service import SyncJournalService
from sync_core.history import RecoveryMode, RecoveryPlan
from viewmodel.sync_history_query import JournalDetail, JournalListRow, SyncHistoryQuery


class SyncHistoryViewModel:
    def __init__(self, query: SyncHistoryQuery, service: SyncJournalService) -> None:
        self.query = query
        self.service = service
        self.selected: JournalDetail | None = None
        self.prepared: RecoveryPlan | None = None

    def rows(self, link_id: str | None = None) -> tuple[JournalListRow, ...]:
        return self.query.rows(link_id)

    def select(self, receipt_id: str) -> JournalDetail:
        self.selected = self.query.detail(receipt_id)
        self.prepared = None
        return self.selected

    def prepare_recovery(self, mode: RecoveryMode) -> RecoveryPlan:
        if self.selected is None:
            raise RuntimeError("SYNC-HISTORY-UI-001: Zuerst einen Journalnachweis auswählen")
        self.prepared = self.service.build_recovery(self.selected.record.receipt_id, mode)
        return self.prepared

    def execute_recovery(self):
        if self.prepared is None:
            raise RuntimeError(
                "SYNC-HISTORY-UI-002: RecoveryPlan zuerst ausdrücklich prüfen; es wird nichts still ausgeführt"
            )
        receipt = self.service.commit_recovery(self.prepared)
        self.prepared = None
        self.selected = self.query.detail(receipt.receipt_id)
        return receipt
