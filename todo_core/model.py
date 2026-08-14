from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .errors import TodoValidationError


class TodoStatus(StrEnum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING = "WAITING"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


class TodoPriority(StrEnum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class LinkDirection(StrEnum):
    TODO_TO_CALENDAR = "TODO_TO_CALENDAR"
    CALENDAR_TO_TODO = "CALENDAR_TO_TODO"
    BIDIRECTIONAL = "BIDIRECTIONAL"
    MANUAL = "MANUAL"


class LinkConflictStatus(StrEnum):
    CLEAN = "CLEAN"
    TODO_CHANGED = "TODO_CHANGED"
    CALENDAR_CHANGED = "CALENDAR_CHANGED"
    BOTH_CHANGED = "BOTH_CHANGED"
    DETACHED = "DETACHED"


def _aware(value: datetime | None, code: str) -> None:
    if value is not None and (value.tzinfo is None or value.utcoffset() is None):
        raise TodoValidationError(f"{code}: Zeitpunkt benötigt eine Zeitzone")


@dataclass(frozen=True, slots=True)
class TodoItem:
    todo_id: str
    title: str
    description: str = ""
    status: TodoStatus = TodoStatus.OPEN
    priority: TodoPriority = TodoPriority.NORMAL
    progress: int = 0
    start_at: datetime | None = None
    due_at: datetime | None = None
    parent_id: str | None = None
    version: int = 1
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.todo_id.strip():
            raise TodoValidationError("TODO-DOMAIN-001: todo_id darf nicht leer sein")
        title = self.title.strip()
        if not title or len(title) > 200:
            raise TodoValidationError("TODO-DOMAIN-002: Titel muss 1 bis 200 Zeichen lang sein")
        if not 0 <= self.progress <= 100:
            raise TodoValidationError("TODO-DOMAIN-003: Fortschritt muss zwischen 0 und 100 liegen")
        for value in (self.start_at, self.due_at, self.created_at, self.updated_at, self.deleted_at):
            _aware(value, "TODO-DOMAIN-004")
        if self.start_at is not None and self.due_at is not None and self.due_at < self.start_at:
            raise TodoValidationError("TODO-DOMAIN-005: Fälligkeit darf nicht vor dem Start liegen")
        if self.parent_id is not None and self.parent_id == self.todo_id:
            raise TodoValidationError("TODO-DOMAIN-006: Aufgabe darf nicht ihr eigenes Elternobjekt sein")
        if self.version < 1:
            raise TodoValidationError("TODO-DOMAIN-007: version muss mindestens 1 sein")
        if self.status is TodoStatus.DONE and self.progress != 100:
            raise TodoValidationError("TODO-DOMAIN-008: Erledigte Aufgabe benötigt 100 Prozent Fortschritt")

    def with_version(self, version: int, updated_at: datetime) -> "TodoItem":
        return TodoItem(
            todo_id=self.todo_id,
            title=self.title,
            description=self.description,
            status=self.status,
            priority=self.priority,
            progress=self.progress,
            start_at=self.start_at,
            due_at=self.due_at,
            parent_id=self.parent_id,
            version=version,
            created_at=self.created_at,
            updated_at=updated_at,
            deleted_at=self.deleted_at,
        )


@dataclass(frozen=True, slots=True)
class TodoCalendarLink:
    link_id: str
    todo_id: str
    event_id: str
    direction: LinkDirection
    conflict_status: LinkConflictStatus = LinkConflictStatus.CLEAN
    last_synced_at: datetime | None = None
    todo_version_at_sync: int = 1
    event_version_at_sync: int = 1
    version: int = 1
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.link_id.strip() or not self.todo_id.strip() or not self.event_id.strip():
            raise TodoValidationError("TODO-LINK-DOMAIN-001: Link-, Todo- und Termin-ID müssen gesetzt sein")
        if min(self.todo_version_at_sync, self.event_version_at_sync, self.version) < 1:
            raise TodoValidationError("TODO-LINK-DOMAIN-002: Link-Versionen müssen mindestens 1 sein")
        for value in (self.last_synced_at, self.created_at, self.updated_at, self.deleted_at):
            _aware(value, "TODO-LINK-DOMAIN-003")

    def with_version(self, version: int, updated_at: datetime) -> "TodoCalendarLink":
        return TodoCalendarLink(
            link_id=self.link_id,
            todo_id=self.todo_id,
            event_id=self.event_id,
            direction=self.direction,
            conflict_status=self.conflict_status,
            last_synced_at=self.last_synced_at,
            todo_version_at_sync=self.todo_version_at_sync,
            event_version_at_sync=self.event_version_at_sync,
            version=version,
            created_at=self.created_at,
            updated_at=updated_at,
            deleted_at=self.deleted_at,
        )
