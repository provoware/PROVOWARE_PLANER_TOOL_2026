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
