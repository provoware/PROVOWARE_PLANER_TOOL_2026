from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class DiagnosisState(str, Enum):
    READY = "BEREIT"
    LIMITED = "EINGESCHRAENKT"
    BLOCKED = "BLOCKIERT"

    @property
    def symbol(self) -> str:
        return {
            DiagnosisState.READY: "●",
            DiagnosisState.LIMITED: "▲",
            DiagnosisState.BLOCKED: "●",
        }[self]

    @property
    def user_text(self) -> str:
        return f"{self.symbol} {self.value}"


@dataclass(frozen=True, slots=True)
class DiagnosisItem:
    item_id: str
    title: str
    state: DiagnosisState
    summary: str
    details: str = ""
    count: int | None = None


@dataclass(frozen=True, slots=True)
class DiagnosisSnapshot:
    generated_at: datetime
    items: tuple[DiagnosisItem, ...]

    @property
    def overall_state(self) -> DiagnosisState:
        states = {item.state for item in self.items}
        if DiagnosisState.BLOCKED in states:
            return DiagnosisState.BLOCKED
        if DiagnosisState.LIMITED in states:
            return DiagnosisState.LIMITED
        return DiagnosisState.READY

    def item(self, item_id: str) -> DiagnosisItem:
        return next(item for item in self.items if item.item_id == item_id)
