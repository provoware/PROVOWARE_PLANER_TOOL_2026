from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .errors import DomainValidationError


class EventStatus(StrEnum):
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class MarkerType:
    marker_id: int
    title: str
    short_title: str
    color: str
    symbol: str
    description: str = ""
    enabled: bool = True

    def __post_init__(self) -> None:
        if not 1 <= self.marker_id <= 5:
            raise DomainValidationError("CAL-DOMAIN-004: marker_id muss zwischen 1 und 5 liegen")
        if not self.title.strip():
            raise DomainValidationError("CAL-DOMAIN-005: Markierungstitel darf nicht leer sein")
        if not self.short_title.strip():
            raise DomainValidationError("CAL-DOMAIN-006: Markierungskürzel darf nicht leer sein")
        if not (self.color.startswith("#") and len(self.color) in {4, 7}):
            raise DomainValidationError("CAL-DOMAIN-007: Markierungsfarbe ist ungültig")


@dataclass(frozen=True, slots=True)
class CalendarEvent:
    event_id: str
    title: str
    description: str
    start_at: datetime
    end_at: datetime | None
    timezone: str
    all_day: bool = False
    marker_id: int | None = None
    status: EventStatus = EventStatus.ACTIVE
    version: int = 1
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

    def __post_init__(self) -> None:
        title = self.title.strip()
        if not title:
            raise DomainValidationError("CAL-DOMAIN-001: Titel darf nicht leer sein")
        if len(title) > 200:
            raise DomainValidationError("CAL-DOMAIN-002: Titel darf höchstens 200 Zeichen lang sein")
        if self.start_at.tzinfo is None or self.start_at.utcoffset() is None:
            raise DomainValidationError("CAL-DOMAIN-003: Startzeit benötigt eine Zeitzone")
        if self.end_at is not None:
            if self.end_at.tzinfo is None or self.end_at.utcoffset() is None:
                raise DomainValidationError("CAL-DOMAIN-003: Endzeit benötigt eine Zeitzone")
            if self.end_at < self.start_at:
                raise DomainValidationError("CAL-DOMAIN-008: Endzeit darf nicht vor Startzeit liegen")
        if self.marker_id is not None and not 1 <= self.marker_id <= 5:
            raise DomainValidationError("CAL-DOMAIN-004: marker_id muss zwischen 1 und 5 liegen")
        if self.version < 1:
            raise DomainValidationError("CAL-DOMAIN-009: version muss mindestens 1 sein")
        try:
            ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError as exc:
            raise DomainValidationError("CAL-DOMAIN-010: unbekannte Zeitzone") from exc

    def with_version(self, version: int, updated_at: datetime) -> "CalendarEvent":
        return CalendarEvent(
            event_id=self.event_id,
            title=self.title,
            description=self.description,
            start_at=self.start_at,
            end_at=self.end_at,
            timezone=self.timezone,
            all_day=self.all_day,
            marker_id=self.marker_id,
            status=self.status,
            version=version,
            created_at=self.created_at,
            updated_at=updated_at,
            deleted_at=self.deleted_at,
        )
