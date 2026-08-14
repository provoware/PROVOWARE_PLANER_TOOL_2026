from __future__ import annotations

from dataclasses import dataclass

from diagnostics_core.model import DiagnosisSnapshot
from services.diagnostics_service import DiagnosticsService


@dataclass(frozen=True, slots=True)
class DiagnosisRow:
    item_id: str
    area: str
    state_text: str
    summary: str
    details: str
    count_text: str


@dataclass(frozen=True, slots=True)
class DiagnosticsViewSnapshot:
    overall_text: str
    generated_text: str
    rows: tuple[DiagnosisRow, ...]
    source: DiagnosisSnapshot


class DiagnosticsViewModel:
    def __init__(self, service: DiagnosticsService) -> None:
        self.service = service

    def load(self) -> DiagnosticsViewSnapshot:
        snapshot = self.service.snapshot()
        rows = tuple(
            DiagnosisRow(
                item_id=item.item_id,
                area=item.title,
                state_text=item.state.user_text,
                summary=item.summary,
                details=item.details,
                count_text="—" if item.count is None else str(item.count),
            )
            for item in snapshot.items
        )
        return DiagnosticsViewSnapshot(
            overall_text=f"{snapshot.overall_state.user_text} – Diagnoseübersicht",
            generated_text=snapshot.generated_at.astimezone().strftime("%d.%m.%Y %H:%M:%S"),
            rows=rows,
            source=snapshot,
        )
