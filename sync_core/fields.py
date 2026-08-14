from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SyncFieldSpec:
    field_id: str
    todo_field: str
    calendar_field: str
    automatic: bool
    semantic_review_required: bool = False
    calendar_target_requires_value: bool = False


SYNC_FIELD_SPECS = (
    SyncFieldSpec("TITLE", "title", "title", True),
    SyncFieldSpec("DESCRIPTION", "description", "description", True),
    SyncFieldSpec("START_AT", "start_at", "start_at", True, calendar_target_requires_value=True),
    SyncFieldSpec("DUE_END", "due_at", "end_at", False, semantic_review_required=True),
)

SYNC_FIELD_BY_ID = {item.field_id: item for item in SYNC_FIELD_SPECS}
