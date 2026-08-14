from __future__ import annotations

from datetime import datetime

from calendar_core.errors import ConcurrentUpdateError, EventNotFoundError
from calendar_core.model import CalendarEvent, EventStatus, MarkerType
from storage.database import Database


def _dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _event(row) -> CalendarEvent:
    return CalendarEvent(
        event_id=row["event_id"],
        title=row["title"],
        description=row["description"],
        start_at=datetime.fromisoformat(row["start_at"]),
        end_at=_dt(row["end_at"]),
        timezone=row["timezone"],
        all_day=bool(row["all_day"]),
        marker_id=row["marker_id"],
        status=EventStatus(row["status"]),
        version=int(row["version"]),
        created_at=_dt(row["created_at"]),
        updated_at=_dt(row["updated_at"]),
        deleted_at=_dt(row["deleted_at"]),
    )


class CalendarRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def add(self, event: CalendarEvent) -> CalendarEvent:
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO calendar_events(
                    event_id, title, description, start_at, end_at, timezone,
                    all_day, marker_id, status, version, created_at, updated_at, deleted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.title.strip(),
                    event.description,
                    event.start_at.isoformat(),
                    event.end_at.isoformat() if event.end_at else None,
                    event.timezone,
                    int(event.all_day),
                    event.marker_id,
                    event.status.value,
                    event.version,
                    event.created_at.isoformat() if event.created_at else event.start_at.isoformat(),
                    event.updated_at.isoformat() if event.updated_at else event.start_at.isoformat(),
                    event.deleted_at.isoformat() if event.deleted_at else None,
                ),
            )
        return event

    def get(self, event_id: str, *, include_deleted: bool = False) -> CalendarEvent:
        with self.database.connect() as connection:
            sql = "SELECT * FROM calendar_events WHERE event_id = ?"
            params: list[object] = [event_id]
            if not include_deleted:
                sql += " AND deleted_at IS NULL"
            row = connection.execute(sql, params).fetchone()
        if row is None:
            raise EventNotFoundError(f"CAL-EVENT-NOTFOUND-001: {event_id}")
        return _event(row)

    def update(self, event: CalendarEvent, *, expected_version: int, updated_at: datetime) -> CalendarEvent:
        new_version = expected_version + 1
        with self.database.transaction() as connection:
            cursor = connection.execute(
                """
                UPDATE calendar_events
                SET title = ?, description = ?, start_at = ?, end_at = ?, timezone = ?,
                    all_day = ?, marker_id = ?, status = ?, version = ?, updated_at = ?
                WHERE event_id = ? AND version = ? AND deleted_at IS NULL
                """,
                (
                    event.title.strip(), event.description, event.start_at.isoformat(),
                    event.end_at.isoformat() if event.end_at else None, event.timezone,
                    int(event.all_day), event.marker_id, event.status.value, new_version,
                    updated_at.isoformat(), event.event_id, expected_version,
                ),
            )
            if cursor.rowcount != 1:
                exists = connection.execute(
                    "SELECT version, deleted_at FROM calendar_events WHERE event_id = ?",
                    (event.event_id,),
                ).fetchone()
                if exists is None or exists["deleted_at"] is not None:
                    raise EventNotFoundError(f"CAL-EVENT-NOTFOUND-001: {event.event_id}")
                raise ConcurrentUpdateError(
                    f"CAL-CONFLICT-001: erwartet Version {expected_version}, vorhanden {exists['version']}"
                )
        return event.with_version(new_version, updated_at)

    def soft_delete(self, event_id: str, *, expected_version: int, deleted_at: datetime) -> None:
        with self.database.transaction() as connection:
            cursor = connection.execute(
                """
                UPDATE calendar_events
                SET deleted_at = ?, updated_at = ?, version = version + 1
                WHERE event_id = ? AND version = ? AND deleted_at IS NULL
                """,
                (deleted_at.isoformat(), deleted_at.isoformat(), event_id, expected_version),
            )
            if cursor.rowcount != 1:
                row = connection.execute(
                    "SELECT version FROM calendar_events WHERE event_id = ? AND deleted_at IS NULL",
                    (event_id,),
                ).fetchone()
                if row is None:
                    raise EventNotFoundError(f"CAL-EVENT-NOTFOUND-001: {event_id}")
                raise ConcurrentUpdateError(
                    f"CAL-CONFLICT-001: erwartet Version {expected_version}, vorhanden {row['version']}"
                )

    def list_between(self, start: datetime, end: datetime) -> list[CalendarEvent]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM calendar_events
                WHERE deleted_at IS NULL
                  AND start_at < ?
                  AND COALESCE(end_at, start_at) >= ?
                ORDER BY start_at, event_id
                """,
                (end.isoformat(), start.isoformat()),
            ).fetchall()
        return [_event(row) for row in rows]

    def marker_types(self) -> list[MarkerType]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM marker_types ORDER BY sort_order"
            ).fetchall()
        return [
            MarkerType(
                marker_id=int(row["marker_id"]), title=row["title"],
                short_title=row["short_title"], color=row["color"], symbol=row["symbol"],
                description=row["description"], enabled=bool(row["enabled"]),
            )
            for row in rows
        ]
