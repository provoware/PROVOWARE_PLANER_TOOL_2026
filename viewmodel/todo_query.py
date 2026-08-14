from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from enum import StrEnum
from zoneinfo import ZoneInfo

from services.todo_service import TodoCalendarLinkService, TodoService
from todo_core.model import LinkConflictStatus, LinkDirection, TodoItem, TodoPriority, TodoStatus


class TodoListMode(StrEnum):
    TODAY = "HEUTE"
    THIS_WEEK = "DIESE_WOCHE"
    OVERDUE = "UEBERFAELLIG"
    WITHOUT_DATE = "OHNE_DATUM"
    DONE = "ERLEDIGT"


STATUS_TEXT = {
    TodoStatus.OPEN: "Offen",
    TodoStatus.IN_PROGRESS: "In Arbeit",
    TodoStatus.WAITING: "Wartet",
    TodoStatus.DONE: "Erledigt",
    TodoStatus.CANCELLED: "Abgebrochen",
}

PRIORITY_TEXT = {
    TodoPriority.LOW: "Niedrig",
    TodoPriority.NORMAL: "Normal",
    TodoPriority.HIGH: "Hoch",
    TodoPriority.URGENT: "Dringend",
}

DIRECTION_TEXT = {
    LinkDirection.TODO_TO_CALENDAR: "Aufgabe → Kalender",
    LinkDirection.CALENDAR_TO_TODO: "Kalender → Aufgabe",
    LinkDirection.BIDIRECTIONAL: "Beidseitig – nur vorgemerkt",
    LinkDirection.MANUAL: "Manuell",
}

CONFLICT_TEXT = {
    LinkConflictStatus.CLEAN: "Keine Abweichung erkannt.",
    LinkConflictStatus.TODO_CHANGED: "Die Aufgabe wurde seit der letzten Kopplung geändert. Es wird nichts automatisch übertragen.",
    LinkConflictStatus.CALENDAR_CHANGED: "Der Termin wurde seit der letzten Kopplung geändert. Es wird nichts automatisch übertragen.",
    LinkConflictStatus.BOTH_CHANGED: "Aufgabe und Termin wurden geändert. Manuelle Prüfung ist erforderlich; I007 löst den Konflikt nicht automatisch.",
    LinkConflictStatus.DETACHED: "Mindestens ein gekoppeltes Objekt wurde weich gelöscht. Die Verknüpfung bleibt als Nachweis bestehen.",
}


@dataclass(frozen=True, slots=True)
class TodoLinkView:
    link_id: str
    event_id: str
    direction: LinkDirection
    conflict_status: LinkConflictStatus
    version: int

    @property
    def conflict_text(self) -> str:
        return CONFLICT_TEXT[self.conflict_status]

    @property
    def display_text(self) -> str:
        symbol = "●" if self.conflict_status is LinkConflictStatus.CLEAN else "▲"
        state = "SAUBER" if self.conflict_status is LinkConflictStatus.CLEAN else "PRÜFEN"
        return f"{symbol} {state} | {DIRECTION_TEXT[self.direction]} | Termin {self.event_id} | {self.conflict_text}"


@dataclass(frozen=True, slots=True)
class TodoView:
    todo_id: str
    title: str
    description: str
    status: TodoStatus
    priority: TodoPriority
    progress: int
    start_local: datetime | None
    due_local: datetime | None
    parent_id: str | None
    version: int
    links: tuple[TodoLinkView, ...]

    @property
    def status_text(self) -> str:
        return STATUS_TEXT[self.status]

    @property
    def priority_text(self) -> str:
        return PRIORITY_TEXT[self.priority]

    @property
    def due_text(self) -> str:
        if self.due_local is None:
            return "Ohne Fälligkeit"
        return self.due_local.strftime("%d.%m.%Y %H:%M")

    @property
    def start_text(self) -> str:
        if self.start_local is None:
            return "Ohne Startdatum"
        return self.start_local.strftime("%d.%m.%Y %H:%M")

    @property
    def conflict_count(self) -> int:
        return sum(link.conflict_status is not LinkConflictStatus.CLEAN for link in self.links)

    @property
    def display_text(self) -> str:
        conflict = f" | ▲ {self.conflict_count} Kopplung(en) prüfen" if self.conflict_count else ""
        return f"{self.priority_text} | {self.status_text} | {self.progress}% | {self.due_text} | {self.title}{conflict}"


@dataclass(frozen=True, slots=True)
class TodoListSnapshot:
    mode: TodoListMode
    generated_at: datetime
    items: tuple[TodoView, ...]

    @property
    def conflict_count(self) -> int:
        return sum(item.conflict_count for item in self.items)


class TodoQueryService:
    def __init__(
        self,
        todo_service: TodoService,
        link_service: TodoCalendarLinkService,
        *,
        timezone_name: str = "Europe/Berlin",
    ) -> None:
        self.todo_service = todo_service
        self.link_service = link_service
        self.timezone_name = timezone_name
        self.zone = ZoneInfo(timezone_name)

    def list(self, mode: TodoListMode, *, now: datetime | None = None) -> TodoListSnapshot:
        current = now.astimezone(self.zone) if now is not None else datetime.now(self.zone)
        items = [item for item in self.todo_service.list_todos(include_terminal=True) if self._matches(item, mode, current)]
        views = tuple(sorted((self._view(item) for item in items), key=self._sort_key))
        return TodoListSnapshot(mode=TodoListMode(mode), generated_at=current, items=views)

    def one(self, todo_id: str) -> TodoView:
        return self._view(self.todo_service.get_todo(todo_id))

    def _matches(self, item: TodoItem, mode: TodoListMode, current: datetime) -> bool:
        mode = TodoListMode(mode)
        terminal = item.status in {TodoStatus.DONE, TodoStatus.CANCELLED}
        start = item.start_at.astimezone(self.zone) if item.start_at else None
        due = item.due_at.astimezone(self.zone) if item.due_at else None
        if mode is TodoListMode.DONE:
            return item.status is TodoStatus.DONE
        if terminal:
            return False
        if mode is TodoListMode.WITHOUT_DATE:
            return start is None and due is None
        if mode is TodoListMode.OVERDUE:
            return due is not None and due < current
        if mode is TodoListMode.TODAY:
            today = current.date()
            return (due is not None and due.date() == today) or (start is not None and start.date() == today)
        monday = current.date() - timedelta(days=current.weekday())
        sunday = monday + timedelta(days=6)
        return self._date_in_window(start, monday, sunday) or self._date_in_window(due, monday, sunday)

    @staticmethod
    def _date_in_window(value: datetime | None, start: date, end: date) -> bool:
        return value is not None and start <= value.date() <= end

    def _view(self, item: TodoItem) -> TodoView:
        links = []
        for link in self.link_service.links_for_todo(item.todo_id):
            links.append(
                TodoLinkView(
                    link_id=link.link_id,
                    event_id=link.event_id,
                    direction=link.direction,
                    conflict_status=self.link_service.preview_conflict(link.link_id),
                    version=link.version,
                )
            )
        return TodoView(
            todo_id=item.todo_id,
            title=item.title,
            description=item.description,
            status=item.status,
            priority=item.priority,
            progress=item.progress,
            start_local=item.start_at.astimezone(self.zone) if item.start_at else None,
            due_local=item.due_at.astimezone(self.zone) if item.due_at else None,
            parent_id=item.parent_id,
            version=item.version,
            links=tuple(links),
        )

    @staticmethod
    def _sort_key(item: TodoView) -> tuple:
        priority_rank = {
            TodoPriority.URGENT: 0,
            TodoPriority.HIGH: 1,
            TodoPriority.NORMAL: 2,
            TodoPriority.LOW: 3,
        }[item.priority]
        due = item.due_local or datetime.max.replace(tzinfo=ZoneInfo("UTC"))
        return (due, priority_rank, item.title.casefold(), item.todo_id)
