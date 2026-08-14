from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from services.history_service import SyncJournalService
from sync_core.fields import SYNC_FIELD_SPECS
from sync_core.history import JournalRecord


def _text(value: object) -> str:
    if value is None:
        return "—"
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


@dataclass(frozen=True, slots=True)
class JournalListRow:
    receipt_id: str
    created_at: str
    link_id: str
    plan_kind: str
    integrity: str
    recovery_status: str
    versions: str
    receipt_hash: str
    plan_id: str


@dataclass(frozen=True, slots=True)
class JournalFieldRow:
    field_id: str
    before_todo: str
    before_calendar: str
    after_todo: str
    after_calendar: str


@dataclass(frozen=True, slots=True)
class JournalDetail:
    record: JournalRecord
    fields: tuple[JournalFieldRow, ...]


class SyncHistoryQuery:
    """Read-only Projektion des I011-Journals für ViewModel/GUI."""

    def __init__(self, service: SyncJournalService) -> None:
        self.service = service

    def rows(self, link_id: str | None = None) -> tuple[JournalListRow, ...]:
        result: list[JournalListRow] = []
        for record in self.service.list_records(link_id):
            result.append(
                JournalListRow(
                    receipt_id=record.receipt_id,
                    created_at=record.created_at,
                    link_id=record.link_id,
                    plan_kind=record.plan_kind.value,
                    integrity=record.integrity.value,
                    recovery_status="VERFÜGBAR" if record.recovery_available else "NICHT AUTOMATISCH",
                    versions=(
                        f"Todo {record.todo_version_before}→{record.todo_version_after} | "
                        f"Kalender {record.event_version_before}→{record.event_version_after} | "
                        f"Link {record.link_version_before}→{record.link_version_after}"
                    ),
                    receipt_hash=record.receipt_sha256,
                    plan_id=record.plan_id,
                )
            )
        return tuple(result)

    def detail(self, receipt_id: str) -> JournalDetail:
        record = self.service.get_record(receipt_id)
        rows: list[JournalFieldRow] = []
        before_todo = record.before_todo_values or {}
        before_calendar = record.before_calendar_values or {}
        after_todo = record.after_todo_values or {}
        after_calendar = record.after_calendar_values or {}
        for spec in SYNC_FIELD_SPECS:
            rows.append(
                JournalFieldRow(
                    field_id=spec.field_id,
                    before_todo=_text(before_todo.get(spec.field_id)),
                    before_calendar=_text(before_calendar.get(spec.field_id)),
                    after_todo=_text(after_todo.get(spec.field_id)),
                    after_calendar=_text(after_calendar.get(spec.field_id)),
                )
            )
        return JournalDetail(record=record, fields=tuple(rows))
