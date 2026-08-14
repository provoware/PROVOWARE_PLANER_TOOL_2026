from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime

from services.todo_service import TodoCalendarLinkService, TodoService
from todo_core.model import LinkDirection, TodoItem, TodoPriority, TodoStatus
from viewmodel.todo_query import TodoListMode, TodoListSnapshot, TodoQueryService, TodoView


@dataclass(slots=True)
class TodoViewModel:
    todo_service: TodoService
    link_service: TodoCalendarLinkService
    timezone_name: str = "Europe/Berlin"
    mode: TodoListMode = TodoListMode.TODAY
    selected_todo_id: str | None = None
    font_scale_percent: int = 100
    query: TodoQueryService = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.query = TodoQueryService(
            self.todo_service,
            self.link_service,
            timezone_name=self.timezone_name,
        )

    def set_mode(self, mode: TodoListMode) -> None:
        self.mode = TodoListMode(mode)
        self.selected_todo_id = None

    def select(self, todo_id: str | None) -> None:
        self.selected_todo_id = todo_id

    def snapshot(self, *, now: datetime | None = None) -> TodoListSnapshot:
        return self.query.list(self.mode, now=now)

    def selected_view(self) -> TodoView | None:
        if not self.selected_todo_id:
            return None
        return self.query.one(self.selected_todo_id)

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
        todo = self.todo_service.create_todo(
            title=title,
            description=description,
            priority=priority,
            status=status,
            progress=progress,
            start_at=start_at,
            due_at=due_at,
            parent_id=parent_id,
        )
        self.selected_todo_id = todo.todo_id
        return todo

    def update_todo(
        self,
        todo_id: str,
        *,
        title: str,
        description: str,
        priority: TodoPriority,
        status: TodoStatus,
        progress: int,
        start_at: datetime | None,
        due_at: datetime | None,
    ) -> TodoItem:
        current = self.todo_service.get_todo(todo_id)
        if status is TodoStatus.DONE:
            progress = 100
        updated = replace(
            current,
            title=title,
            description=description,
            priority=priority,
            status=status,
            progress=progress,
            start_at=start_at,
            due_at=due_at,
        )
        return self.todo_service.update_todo(updated, expected_version=current.version)

    def set_status(self, todo_id: str, status: TodoStatus) -> TodoItem:
        current = self.todo_service.get_todo(todo_id)
        return self.todo_service.set_status(todo_id, status, expected_version=current.version)

    def set_progress(self, todo_id: str, progress: int) -> TodoItem:
        current = self.todo_service.get_todo(todo_id)
        return self.todo_service.set_progress(todo_id, progress, expected_version=current.version)

    def soft_delete(self, todo_id: str) -> None:
        current = self.todo_service.get_todo(todo_id)
        self.todo_service.delete_todo(todo_id, expected_version=current.version)
        if self.selected_todo_id == todo_id:
            self.selected_todo_id = None

    def link_calendar(self, todo_id: str, event_id: str, direction: LinkDirection) -> str:
        return self.link_service.create_link(todo_id, event_id, direction=direction).link_id

    def unlink(self, link_id: str) -> None:
        link = self.link_service.get_link(link_id)
        self.link_service.unlink(link_id, expected_version=link.version)
