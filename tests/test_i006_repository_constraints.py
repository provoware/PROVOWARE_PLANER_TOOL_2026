from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from services.factory import open_planner_services
from todo_core.errors import TodoConcurrentUpdateError, TodoLinkConflictError


class I006RepositoryConstraintsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "planer.sqlite3"
        self.services = open_planner_services(self.path)
        zone = ZoneInfo("Europe/Berlin")
        start = datetime(2026, 8, 14, 9, 0, tzinfo=zone)
        self.event = self.services.calendar.create_event(
            title="Termin", start_at=start, end_at=start + timedelta(hours=1), timezone_name="Europe/Berlin"
        )
        self.todo = self.services.todos.create_todo(title="Aufgabe")
        self.link = self.services.links.create_link(self.todo.todo_id, self.event.event_id)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_optimistic_locking_blocks_stale_update(self) -> None:
        self.services.todos.set_progress(self.todo.todo_id, 20, expected_version=self.todo.version)
        with self.assertRaisesRegex(TodoConcurrentUpdateError, "TODO-CONFLICT-001"):
            self.services.todos.set_progress(self.todo.todo_id, 30, expected_version=self.todo.version)

    def test_duplicate_active_pair_is_forbidden(self) -> None:
        with self.assertRaisesRegex(TodoLinkConflictError, "TODO-LINK-DUP-001"):
            self.services.links.create_link(self.todo.todo_id, self.event.event_id)

    def test_physical_endpoint_delete_is_restricted(self) -> None:
        with self.services.database.transaction() as connection:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("DELETE FROM todos WHERE todo_id=?", (self.todo.todo_id,))
        self.assertEqual(self.services.todos.get_todo(self.todo.todo_id).title, "Aufgabe")

    def test_foreign_keys_and_wal_are_active(self) -> None:
        with self.services.database.session() as connection:
            self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)
            self.assertEqual(connection.execute("PRAGMA journal_mode").fetchone()[0].lower(), "wal")


if __name__ == "__main__":
    unittest.main()
