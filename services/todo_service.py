from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

from calendar_core.model import CalendarEvent
from storage.repository import CalendarRepository
from storage.todo_repository import TodoRepository
from todo_core.model import LinkConflictStatus, LinkDirection, TodoCalendarLink, TodoItem, TodoPriority, TodoStatus


class TodoService:
    def __init__(self, repository: TodoRepository) -> None:
        self.repository = repository

    def create_todo(
        self,
        *,
        title: str,
        description: str = "",
        priority: TodoPriority = TodoPriority.NORMAL,
        status: TodoStatus = TodoStatus.OPEN,
        progress: int = 0,
        start_at: datetime | None = None,
        due_at: datetime | None = None,
        parent_id: str | None = None,
    ) -> TodoItem:
        now = datetime.now(timezone.utc)
        if status is TodoStatus.DONE:
            progress = 100
        todo = TodoItem(
            todo_id=str(uuid4()), title=title, description=description, status=status, priority=priority,
            progress=progress, start_at=start_at, due_at=due_at, parent_id=parent_id,
            version=1, created_at=now, updated_at=now,
        )
        return self.repository.add(todo)

    def get_todo(self, todo_id: str, *, include_deleted: bool = False) -> TodoItem:
        return self.repository.get(todo_id, include_deleted=include_deleted)

    def list_todos(self, *, include_terminal: bool = True) -> list[TodoItem]:
        return self.repository.list_all(include_terminal=include_terminal)

    def update_todo(self, todo: TodoItem, *, expected_version: int) -> TodoItem:
        return self.repository.update(todo, expected_version=expected_version, updated_at=datetime.now(timezone.utc))

    def set_status(self, todo_id: str, status: TodoStatus, *, expected_version: int) -> TodoItem:
        current = self.repository.get(todo_id)
        progress = 100 if status is TodoStatus.DONE else current.progress
        return self.update_todo(replace(current, status=status, progress=progress), expected_version=expected_version)

    def set_progress(self, todo_id: str, progress: int, *, expected_version: int) -> TodoItem:
        current = self.repository.get(todo_id)
        return self.update_todo(replace(current, progress=progress), expected_version=expected_version)

    def delete_todo(self, todo_id: str, *, expected_version: int) -> None:
        self.repository.soft_delete(todo_id, expected_version=expected_version, deleted_at=datetime.now(timezone.utc))

    def list_due(self, until: datetime) -> list[TodoItem]:
        return self.repository.list_due(until)

    def list_children(self, parent_id: str) -> list[TodoItem]:
        return self.repository.list_children(parent_id)


class TodoCalendarLinkService:
    def __init__(
        self,
        todo_repository: TodoRepository,
        calendar_repository: CalendarRepository,
    ) -> None:
        self.todo_repository = todo_repository
        self.calendar_repository = calendar_repository

    def create_link(
        self,
        todo_id: str,
        event_id: str,
        *,
        direction: LinkDirection = LinkDirection.MANUAL,
    ) -> TodoCalendarLink:
        todo = self.todo_repository.get(todo_id)
        event = self.calendar_repository.get(event_id)
        now = datetime.now(timezone.utc)
        link = TodoCalendarLink(
            link_id=str(uuid4()), todo_id=todo.todo_id, event_id=event.event_id,
            direction=direction, conflict_status=LinkConflictStatus.CLEAN, last_synced_at=now,
            todo_version_at_sync=todo.version, event_version_at_sync=event.version,
            version=1, created_at=now, updated_at=now,
        )
        return self.todo_repository.add_link(link)

    def get_link(self, link_id: str, *, include_deleted: bool = False) -> TodoCalendarLink:
        return self.todo_repository.get_link(link_id, include_deleted=include_deleted)

    def unlink(self, link_id: str, *, expected_version: int) -> None:
        self.todo_repository.soft_delete_link(
            link_id, expected_version=expected_version, deleted_at=datetime.now(timezone.utc)
        )

    def set_direction(self, link_id: str, direction: LinkDirection, *, expected_version: int) -> TodoCalendarLink:
        current = self.todo_repository.get_link(link_id)
        return self.todo_repository.update_link(
            replace(current, direction=direction), expected_version=expected_version, updated_at=datetime.now(timezone.utc)
        )

    def preview_conflict(self, link_id: str) -> LinkConflictStatus:
        link = self.todo_repository.get_link(link_id)
        todo = self.todo_repository.get(link.todo_id, include_deleted=True)
        event = self.calendar_repository.get(link.event_id, include_deleted=True)
        return self._conflict_status(todo, event, link)

    def assess_conflict(self, link_id: str) -> TodoCalendarLink:
        link = self.todo_repository.get_link(link_id)
        desired = self.preview_conflict(link_id)
        if desired is link.conflict_status:
            return link
        return self.todo_repository.update_link(
            replace(link, conflict_status=desired),
            expected_version=link.version,
            updated_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _conflict_status(todo: TodoItem, event: CalendarEvent, link: TodoCalendarLink) -> LinkConflictStatus:
        if todo.deleted_at is not None or event.deleted_at is not None:
            return LinkConflictStatus.DETACHED
        todo_changed = todo.version != link.todo_version_at_sync
        event_changed = event.version != link.event_version_at_sync
        if todo_changed and event_changed:
            return LinkConflictStatus.BOTH_CHANGED
        if todo_changed:
            return LinkConflictStatus.TODO_CHANGED
        if event_changed:
            return LinkConflictStatus.CALENDAR_CHANGED
        return LinkConflictStatus.CLEAN

    def mark_synchronized(self, link_id: str, *, expected_version: int) -> TodoCalendarLink:
        link = self.todo_repository.get_link(link_id)
        todo = self.todo_repository.get(link.todo_id)
        event = self.calendar_repository.get(link.event_id)
        now = datetime.now(timezone.utc)
        synchronized = replace(
            link,
            conflict_status=LinkConflictStatus.CLEAN,
            last_synced_at=now,
            todo_version_at_sync=todo.version,
            event_version_at_sync=event.version,
        )
        return self.todo_repository.update_link(synchronized, expected_version=expected_version, updated_at=now)

    def links_for_todo(self, todo_id: str) -> list[TodoCalendarLink]:
        return self.todo_repository.links_for_todo(todo_id)

    def links_for_event(self, event_id: str) -> list[TodoCalendarLink]:
        return self.todo_repository.links_for_event(event_id)
