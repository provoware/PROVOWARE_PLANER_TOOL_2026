from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from storage.database import Database
from todo_core.errors import (
    TodoConcurrentUpdateError,
    TodoLinkConflictError,
    TodoLinkNotFoundError,
    TodoNotFoundError,
)
from todo_core.faults import trigger
from todo_core.model import LinkConflictStatus, LinkDirection, TodoCalendarLink, TodoItem, TodoPriority, TodoStatus


def _iso_utc(value: datetime | None) -> str | None:
    return value.astimezone(timezone.utc).isoformat() if value else None


def _dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _todo(row) -> TodoItem:
    return TodoItem(
        todo_id=row["todo_id"], title=row["title"], description=row["description"],
        status=TodoStatus(row["status"]), priority=TodoPriority(row["priority"]),
        progress=int(row["progress"]), start_at=_dt(row["start_at"]), due_at=_dt(row["due_at"]),
        parent_id=row["parent_id"], version=int(row["version"]), created_at=_dt(row["created_at"]),
        updated_at=_dt(row["updated_at"]), deleted_at=_dt(row["deleted_at"]),
    )


def _link(row) -> TodoCalendarLink:
    return TodoCalendarLink(
        link_id=row["link_id"], todo_id=row["todo_id"], event_id=row["event_id"],
        direction=LinkDirection(row["direction"]), conflict_status=LinkConflictStatus(row["conflict_status"]),
        last_synced_at=_dt(row["last_synced_at"]), todo_version_at_sync=int(row["todo_version_at_sync"]),
        event_version_at_sync=int(row["event_version_at_sync"]), version=int(row["version"]),
        created_at=_dt(row["created_at"]), updated_at=_dt(row["updated_at"]), deleted_at=_dt(row["deleted_at"]),
    )


class TodoRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def add(self, todo: TodoItem) -> TodoItem:
        try:
            with self.database.transaction() as connection:
                connection.execute(
                    """INSERT INTO todos(todo_id,title,description,status,priority,progress,start_at,due_at,parent_id,version,created_at,updated_at,deleted_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (todo.todo_id, todo.title.strip(), todo.description, todo.status.value, todo.priority.value,
                     todo.progress, _iso_utc(todo.start_at), _iso_utc(todo.due_at), todo.parent_id, todo.version,
                     _iso_utc(todo.created_at), _iso_utc(todo.updated_at), _iso_utc(todo.deleted_at)),
                )
                trigger("TODO_AFTER_INSERT_BEFORE_COMMIT")
        except sqlite3.IntegrityError as exc:
            raise TodoLinkConflictError(f"TODO-LINK-FK-001: Todo konnte nicht gespeichert werden: {exc}") from exc
        return todo

    def get(self, todo_id: str, *, include_deleted: bool = False) -> TodoItem:
        with self.database.session() as connection:
            sql = "SELECT * FROM todos WHERE todo_id = ?"
            if not include_deleted:
                sql += " AND deleted_at IS NULL"
            row = connection.execute(sql, (todo_id,)).fetchone()
        if row is None:
            raise TodoNotFoundError(f"TODO-NOTFOUND-001: {todo_id}")
        return _todo(row)

    def update(self, todo: TodoItem, *, expected_version: int, updated_at: datetime) -> TodoItem:
        new_version = expected_version + 1
        with self.database.transaction() as connection:
            cursor = connection.execute(
                """UPDATE todos SET title=?,description=?,status=?,priority=?,progress=?,start_at=?,due_at=?,parent_id=?,version=?,updated_at=?
                WHERE todo_id=? AND version=? AND deleted_at IS NULL""",
                (todo.title.strip(), todo.description, todo.status.value, todo.priority.value, todo.progress,
                 _iso_utc(todo.start_at), _iso_utc(todo.due_at), todo.parent_id, new_version, _iso_utc(updated_at),
                 todo.todo_id, expected_version),
            )
            if cursor.rowcount != 1:
                row = connection.execute("SELECT version,deleted_at FROM todos WHERE todo_id=?", (todo.todo_id,)).fetchone()
                if row is None or row["deleted_at"] is not None:
                    raise TodoNotFoundError(f"TODO-NOTFOUND-001: {todo.todo_id}")
                raise TodoConcurrentUpdateError(
                    f"TODO-CONFLICT-001: erwartet Version {expected_version}, vorhanden {row['version']}"
                )
            trigger("TODO_AFTER_UPDATE_BEFORE_COMMIT")
        return todo.with_version(new_version, updated_at)

    def soft_delete(self, todo_id: str, *, expected_version: int, deleted_at: datetime) -> None:
        with self.database.transaction() as connection:
            cursor = connection.execute(
                """UPDATE todos SET deleted_at=?,updated_at=?,version=version+1
                WHERE todo_id=? AND version=? AND deleted_at IS NULL""",
                (_iso_utc(deleted_at), _iso_utc(deleted_at), todo_id, expected_version),
            )
            if cursor.rowcount != 1:
                row = connection.execute("SELECT version FROM todos WHERE todo_id=? AND deleted_at IS NULL", (todo_id,)).fetchone()
                if row is None:
                    raise TodoNotFoundError(f"TODO-NOTFOUND-001: {todo_id}")
                raise TodoConcurrentUpdateError(
                    f"TODO-CONFLICT-001: erwartet Version {expected_version}, vorhanden {row['version']}"
                )
            trigger("TODO_AFTER_SOFT_DELETE_BEFORE_COMMIT")

    def list_due(self, until: datetime, *, include_terminal: bool = False) -> list[TodoItem]:
        with self.database.session() as connection:
            sql = "SELECT * FROM todos WHERE deleted_at IS NULL AND due_at IS NOT NULL AND due_at <= ?"
            params: list[object] = [_iso_utc(until)]
            if not include_terminal:
                sql += " AND status NOT IN ('DONE','CANCELLED')"
            sql += " ORDER BY due_at, priority DESC, todo_id"
            rows = connection.execute(sql, params).fetchall()
        return [_todo(row) for row in rows]

    def list_children(self, parent_id: str) -> list[TodoItem]:
        with self.database.session() as connection:
            rows = connection.execute(
                "SELECT * FROM todos WHERE parent_id=? AND deleted_at IS NULL ORDER BY created_at,todo_id",
                (parent_id,),
            ).fetchall()
        return [_todo(row) for row in rows]

    def add_link(self, link: TodoCalendarLink) -> TodoCalendarLink:
        try:
            with self.database.transaction() as connection:
                connection.execute(
                    """INSERT INTO todo_calendar_links(link_id,todo_id,event_id,direction,conflict_status,last_synced_at,todo_version_at_sync,event_version_at_sync,version,created_at,updated_at,deleted_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (link.link_id, link.todo_id, link.event_id, link.direction.value, link.conflict_status.value,
                     _iso_utc(link.last_synced_at), link.todo_version_at_sync, link.event_version_at_sync, link.version,
                     _iso_utc(link.created_at), _iso_utc(link.updated_at), _iso_utc(link.deleted_at)),
                )
                trigger("LINK_AFTER_INSERT_BEFORE_COMMIT")
        except sqlite3.IntegrityError as exc:
            message = str(exc).lower()
            code = "TODO-LINK-DUP-001" if "unique" in message else "TODO-LINK-FK-001"
            raise TodoLinkConflictError(f"{code}: Link konnte nicht gespeichert werden: {exc}") from exc
        return link

    def get_link(self, link_id: str, *, include_deleted: bool = False) -> TodoCalendarLink:
        with self.database.session() as connection:
            sql = "SELECT * FROM todo_calendar_links WHERE link_id=?"
            if not include_deleted:
                sql += " AND deleted_at IS NULL"
            row = connection.execute(sql, (link_id,)).fetchone()
        if row is None:
            raise TodoLinkNotFoundError(f"TODO-LINK-NOTFOUND-001: {link_id}")
        return _link(row)

    def update_link(self, link: TodoCalendarLink, *, expected_version: int, updated_at: datetime) -> TodoCalendarLink:
        new_version = expected_version + 1
        with self.database.transaction() as connection:
            cursor = connection.execute(
                """UPDATE todo_calendar_links SET direction=?,conflict_status=?,last_synced_at=?,todo_version_at_sync=?,event_version_at_sync=?,version=?,updated_at=?
                WHERE link_id=? AND version=? AND deleted_at IS NULL""",
                (link.direction.value, link.conflict_status.value, _iso_utc(link.last_synced_at), link.todo_version_at_sync,
                 link.event_version_at_sync, new_version, _iso_utc(updated_at), link.link_id, expected_version),
            )
            if cursor.rowcount != 1:
                row = connection.execute("SELECT version FROM todo_calendar_links WHERE link_id=? AND deleted_at IS NULL", (link.link_id,)).fetchone()
                if row is None:
                    raise TodoLinkNotFoundError(f"TODO-LINK-NOTFOUND-001: {link.link_id}")
                raise TodoConcurrentUpdateError(
                    f"TODO-CONFLICT-001: Link erwartet Version {expected_version}, vorhanden {row['version']}"
                )
            trigger("LINK_AFTER_UPDATE_BEFORE_COMMIT")
        return link.with_version(new_version, updated_at)

    def soft_delete_link(self, link_id: str, *, expected_version: int, deleted_at: datetime) -> None:
        with self.database.transaction() as connection:
            cursor = connection.execute(
                """UPDATE todo_calendar_links SET deleted_at=?,updated_at=?,version=version+1
                WHERE link_id=? AND version=? AND deleted_at IS NULL""",
                (_iso_utc(deleted_at), _iso_utc(deleted_at), link_id, expected_version),
            )
            if cursor.rowcount != 1:
                raise TodoLinkNotFoundError(f"TODO-LINK-NOTFOUND-001: {link_id}")
            trigger("LINK_AFTER_SOFT_DELETE_BEFORE_COMMIT")

    def links_for_todo(self, todo_id: str) -> list[TodoCalendarLink]:
        with self.database.session() as connection:
            rows = connection.execute(
                "SELECT * FROM todo_calendar_links WHERE todo_id=? AND deleted_at IS NULL ORDER BY created_at,link_id",
                (todo_id,),
            ).fetchall()
        return [_link(row) for row in rows]

    def links_for_event(self, event_id: str) -> list[TodoCalendarLink]:
        with self.database.session() as connection:
            rows = connection.execute(
                "SELECT * FROM todo_calendar_links WHERE event_id=? AND deleted_at IS NULL ORDER BY created_at,link_id",
                (event_id,),
            ).fetchall()
        return [_link(row) for row in rows]
