from __future__ import annotations

import json
from dataclasses import dataclass

from services.sync_service import SynchronizationService
from sync_core.model import FieldChangeState, SyncPlan


@dataclass(frozen=True, slots=True)
class SyncControlRow:
    field_id: str
    baseline_text: str
    todo_text: str
    calendar_text: str
    state_text: str
    action_text: str
    reason: str
    version_status: str
    hash_status: str


@dataclass(frozen=True, slots=True)
class SyncControlSnapshot:
    link_id: str
    plan: SyncPlan
    rows: tuple[SyncControlRow, ...]
    version_status: str


def _display(value: object) -> str:
    if value is None:
        return "—"
    return str(value)


def _baseline_display(encoded: str | None) -> str:
    if not encoded:
        return "Keine Baseline"
    try:
        payload = json.loads(encoded)
    except json.JSONDecodeError:
        return "Baseline nicht lesbar"
    value = payload.get("value")
    return "—" if value is None else str(value)


class SyncControlQuery:
    """Read-only Projektion des qualifizierten Sync-Kerns für die I010-Oberfläche."""

    def __init__(self, sync_service: SynchronizationService) -> None:
        self.sync_service = sync_service

    def link_ids(self) -> tuple[str, ...]:
        # Read-only Projektion; keine Konfliktbewertung und kein Schreibzugriff.
        with self.sync_service.repository.database.session() as connection:
            rows = connection.execute(
                "SELECT link_id FROM todo_calendar_links WHERE deleted_at IS NULL ORDER BY created_at, link_id"
            ).fetchall()
        return tuple(row["link_id"] for row in rows)

    def load(self, link_id: str) -> SyncControlSnapshot:
        plan = self.sync_service.plan(link_id)
        baselines = {item.field_id: item.baseline_json for item in self.sync_service.baselines(link_id)}
        version_status = (
            f"AKTUELL – Todo v{plan.expected_todo_version}, Termin v{plan.expected_event_version}, "
            f"Link v{plan.expected_link_version}"
        )
        rows = []
        for field in plan.fields:
            if field.state is FieldChangeState.BASELINE_MISSING:
                hash_status = "BLOCKIERT – Feld-Baseline fehlt"
            elif len(field.todo_sha256) == 64 and len(field.calendar_sha256) == 64 and (
                field.baseline_sha256 is None or len(field.baseline_sha256) == 64
            ):
                hash_status = "PASS – SHA-256 vollständig"
            else:
                hash_status = "FEHLER – Hashbindung unvollständig"
            rows.append(
                SyncControlRow(
                    field_id=field.field_id,
                    baseline_text=_baseline_display(baselines.get(field.field_id)),
                    todo_text=_display(field.todo_value),
                    calendar_text=_display(field.calendar_value),
                    state_text=field.state.value,
                    action_text=field.action.value,
                    reason=field.reason,
                    version_status=version_status,
                    hash_status=hash_status,
                )
            )
        return SyncControlSnapshot(link_id=link_id, plan=plan, rows=tuple(rows), version_status=version_status)
