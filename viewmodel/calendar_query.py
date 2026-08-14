from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from calendar_core.model import CalendarEvent, MarkerType
from services.calendar_service import CalendarService


@dataclass(frozen=True, slots=True)
class MarkerView:
    marker_id: int
    title: str
    short_title: str
    color: str
    symbol: str
    description: str


@dataclass(frozen=True, slots=True)
class EventView:
    event_id: str
    title: str
    description: str
    start_local: datetime
    end_local: datetime | None
    all_day: bool
    marker: MarkerView | None
    status: str
    version: int

    @property
    def marker_text(self) -> str:
        if self.marker is None:
            return "○ Ohne Markierung"
        return f"{self.marker.symbol} {self.marker.short_title} – {self.marker.title}"

    @property
    def time_text(self) -> str:
        if self.all_day:
            return "Ganztägig"
        if self.end_local is None:
            return self.start_local.strftime("%H:%M")
        return f"{self.start_local:%H:%M}–{self.end_local:%H:%M}"

    @property
    def display_text(self) -> str:
        return f"{self.time_text} | {self.marker_text} | {self.title}"


@dataclass(frozen=True, slots=True)
class DayViewData:
    day: date
    events: tuple[EventView, ...]


@dataclass(frozen=True, slots=True)
class WeekDayData:
    day: date
    events: tuple[EventView, ...]


@dataclass(frozen=True, slots=True)
class WeekViewData:
    start_day: date
    days: tuple[WeekDayData, ...]


@dataclass(frozen=True, slots=True)
class MonthCell:
    day: date
    in_month: bool
    events: tuple[EventView, ...]


@dataclass(frozen=True, slots=True)
class MonthViewData:
    year: int
    month: int
    weeks: tuple[tuple[MonthCell, ...], ...]


@dataclass(frozen=True, slots=True)
class YearMonthData:
    month: int
    event_count: int
    marker_counts: tuple[tuple[int, int], ...]


@dataclass(frozen=True, slots=True)
class YearViewData:
    year: int
    months: tuple[YearMonthData, ...]


class CalendarQueryService:
    def __init__(self, service: CalendarService, *, timezone_name: str = "Europe/Berlin") -> None:
        self.service = service
        self.timezone_name = timezone_name
        self.zone = ZoneInfo(timezone_name)

    def markers(self) -> tuple[MarkerView, ...]:
        return tuple(self._marker(marker) for marker in self.service.list_markers())

    def _marker(self, marker: MarkerType) -> MarkerView:
        return MarkerView(
            marker_id=marker.marker_id,
            title=marker.title,
            short_title=marker.short_title,
            color=marker.color,
            symbol=marker.symbol,
            description=marker.description,
        )

    def _bounds(self, day: date) -> tuple[datetime, datetime]:
        start = datetime.combine(day, time.min, tzinfo=self.zone)
        return start, start + timedelta(days=1)

    def _event(self, event: CalendarEvent, markers: dict[int, MarkerView]) -> EventView:
        return EventView(
            event_id=event.event_id,
            title=event.title,
            description=event.description,
            start_local=event.start_at.astimezone(self.zone),
            end_local=event.end_at.astimezone(self.zone) if event.end_at else None,
            all_day=event.all_day,
            marker=markers.get(event.marker_id) if event.marker_id is not None else None,
            status=event.status.value,
            version=event.version,
        )

    def _events(self, start: datetime, end: datetime) -> tuple[EventView, ...]:
        markers = {marker.marker_id: marker for marker in self.markers()}
        return tuple(self._event(event, markers) for event in self.service.list_events(start, end))

    def day(self, day: date) -> DayViewData:
        start, end = self._bounds(day)
        return DayViewData(day=day, events=self._events(start, end))

    def week(self, reference: date) -> WeekViewData:
        monday = reference - timedelta(days=reference.weekday())
        start, _ = self._bounds(monday)
        end, _ = self._bounds(monday + timedelta(days=7))
        events = self._events(start, end)
        by_day: dict[date, list[EventView]] = {monday + timedelta(days=i): [] for i in range(7)}
        for event in events:
            by_day.setdefault(event.start_local.date(), []).append(event)
        return WeekViewData(
            start_day=monday,
            days=tuple(
                WeekDayData(day=monday + timedelta(days=i), events=tuple(by_day[monday + timedelta(days=i)]))
                for i in range(7)
            ),
        )

    def month(self, reference: date) -> MonthViewData:
        cal = calendar.Calendar(firstweekday=0)
        days = list(cal.itermonthdates(reference.year, reference.month))
        start, _ = self._bounds(days[0])
        end, _ = self._bounds(days[-1] + timedelta(days=1))
        events = self._events(start, end)
        by_day: dict[date, list[EventView]] = {}
        for event in events:
            by_day.setdefault(event.start_local.date(), []).append(event)
        rows: list[tuple[MonthCell, ...]] = []
        for index in range(0, len(days), 7):
            row_days = days[index:index + 7]
            rows.append(tuple(
                MonthCell(
                    day=current,
                    in_month=current.month == reference.month,
                    events=tuple(by_day.get(current, [])),
                )
                for current in row_days
            ))
        return MonthViewData(year=reference.year, month=reference.month, weeks=tuple(rows))

    def year(self, reference: date) -> YearViewData:
        year_start = datetime(reference.year, 1, 1, tzinfo=self.zone)
        year_end = datetime(reference.year + 1, 1, 1, tzinfo=self.zone)
        events = self._events(year_start, year_end)
        months: list[YearMonthData] = []
        for month in range(1, 13):
            month_events = [event for event in events if event.start_local.month == month]
            counts: dict[int, int] = {}
            for event in month_events:
                if event.marker is not None:
                    counts[event.marker.marker_id] = counts.get(event.marker.marker_id, 0) + 1
            months.append(
                YearMonthData(
                    month=month,
                    event_count=len(month_events),
                    marker_counts=tuple(sorted(counts.items())),
                )
            )
        return YearViewData(year=reference.year, months=tuple(months))
