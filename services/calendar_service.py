from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

from calendar_core.model import CalendarEvent, EventStatus, MarkerType
from storage.repository import CalendarRepository


class CalendarService:
    def __init__(self, repository: CalendarRepository) -> None:
        self.repository = repository

    def create_event(
        self,
        *,
        title: str,
        start_at: datetime,
        end_at: datetime | None,
        timezone_name: str,
        description: str = "",
        all_day: bool = False,
        marker_id: int | None = None,
    ) -> CalendarEvent:
        now = datetime.now(timezone.utc)
        event = CalendarEvent(
            event_id=str(uuid4()),
            title=title,
            description=description,
            start_at=start_at,
            end_at=end_at,
            timezone=timezone_name,
            all_day=all_day,
            marker_id=marker_id,
            status=EventStatus.ACTIVE,
            version=1,
            created_at=now,
            updated_at=now,
        )
        return self.repository.add(event)

    def update_event(self, event: CalendarEvent, *, expected_version: int) -> CalendarEvent:
        return self.repository.update(
            event,
            expected_version=expected_version,
            updated_at=datetime.now(timezone.utc),
        )

    def cancel_event(self, event_id: str, *, expected_version: int) -> CalendarEvent:
        current = self.repository.get(event_id)
        cancelled = replace(current, status=EventStatus.CANCELLED)
        return self.update_event(cancelled, expected_version=expected_version)

    def delete_event(self, event_id: str, *, expected_version: int) -> None:
        self.repository.soft_delete(
            event_id,
            expected_version=expected_version,
            deleted_at=datetime.now(timezone.utc),
        )

    def get_event(self, event_id: str, *, include_deleted: bool = False) -> CalendarEvent:
        return self.repository.get(event_id, include_deleted=include_deleted)

    def list_events(self, start: datetime, end: datetime) -> list[CalendarEvent]:
        return self.repository.list_between(start, end)

    def list_markers(self) -> list[MarkerType]:
        return self.repository.marker_types()

    def update_markers(self, markers: tuple[MarkerType, ...] | list[MarkerType]) -> tuple[MarkerType, ...]:
        return self.repository.update_markers(markers)

    def update_marker(self, marker: MarkerType) -> MarkerType:
        return self.repository.update_marker(marker)
