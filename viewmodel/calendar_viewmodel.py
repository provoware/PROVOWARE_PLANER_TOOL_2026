from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum

from calendar_core.model import MarkerType
from services.calendar_service import CalendarService
from viewmodel.calendar_query import CalendarQueryService


class CalendarViewMode(StrEnum):
    DAY = "TAG"
    WEEK = "WOCHE"
    MONTH = "MONAT"
    YEAR = "JAHR"


@dataclass(slots=True)
class CalendarViewModel:
    service: CalendarService
    timezone_name: str = "Europe/Berlin"
    reference_date: date = field(default_factory=date.today)
    mode: CalendarViewMode = CalendarViewMode.MONTH
    font_scale_percent: int = 100
    query: CalendarQueryService = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.query = CalendarQueryService(self.service, timezone_name=self.timezone_name)

    def set_mode(self, mode: CalendarViewMode) -> None:
        self.mode = CalendarViewMode(mode)

    def select_date(self, value: date) -> None:
        self.reference_date = value

    def today(self) -> None:
        self.reference_date = date.today()

    def navigate(self, direction: int) -> None:
        if direction not in {-1, 1}:
            raise ValueError("direction muss -1 oder 1 sein")
        current = self.reference_date
        if self.mode == CalendarViewMode.DAY:
            from datetime import timedelta
            self.reference_date = current + timedelta(days=direction)
        elif self.mode == CalendarViewMode.WEEK:
            from datetime import timedelta
            self.reference_date = current + timedelta(days=7 * direction)
        elif self.mode == CalendarViewMode.MONTH:
            month_index = current.year * 12 + current.month - 1 + direction
            year, month_zero = divmod(month_index, 12)
            import calendar
            day = min(current.day, calendar.monthrange(year, month_zero + 1)[1])
            self.reference_date = date(year, month_zero + 1, day)
        else:
            import calendar
            year = current.year + direction
            day = min(current.day, calendar.monthrange(year, current.month)[1])
            self.reference_date = date(year, current.month, day)

    def snapshot(self):
        if self.mode == CalendarViewMode.DAY:
            return self.query.day(self.reference_date)
        if self.mode == CalendarViewMode.WEEK:
            return self.query.week(self.reference_date)
        if self.mode == CalendarViewMode.MONTH:
            return self.query.month(self.reference_date)
        return self.query.year(self.reference_date)

    def day_events(self):
        return self.query.day(self.reference_date).events

    def markers(self):
        return self.query.markers()

    def update_marker(self, marker: MarkerType) -> MarkerType:
        return self.service.update_marker(marker)
