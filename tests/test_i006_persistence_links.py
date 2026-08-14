from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from services.factory import open_planner_services
from todo_core.model import LinkConflictStatus, LinkDirection, TodoPriority

ROOT = Path(__file__).resolve().parents[1]


def _current_iteration() -> int:
    value = json.loads((ROOT / "VERSION.json").read_text(encoding="utf-8")).get("iteration", "I000")
    try:
        return int(str(value).removeprefix("I"))
    except ValueError:
        return 0


class I006PersistenceLinksTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "planer.sqlite3"
        self.services = open_planner_services(self.path)
        zone = ZoneInfo("Europe/Berlin")
        start = datetime(2026, 8, 14, 9, 0, tzinfo=zone)
        self.event = self.services.calendar.create_event(
            title="Termin", start_at=start, end_at=start + timedelta(hours=1), timezone_name="Europe/Berlin"
        )
        self.todo = self.services.todos.create_todo(
            title="Aufgabe", priority=TodoPriority.HIGH, start_at=start, due_at=start + timedelta(hours=2)
        )
        self.link = self.services.links.create_link(
            self.todo.todo_id, self.event.event_id, direction=LinkDirection.BIDIRECTIONAL
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_restart_preserves_todo_and_link(self) -> None:
        reopened = open_planner_services(self.path)
        todo = reopened.todos.get_todo(self.todo.todo_id)
        link = reopened.links.get_link(self.link.link_id)
        self.assertEqual(todo.title, "Aufgabe")
        self.assertEqual(link.todo_id, todo.todo_id)
        self.assertEqual(link.event_id, self.event.event_id)
        schema = reopened.database.schema_version()
        if _current_iteration() == 6:
            self.assertEqual(schema, 2)
        else:
            self.assertGreaterEqual(schema, 2)

    def test_unlink_does_not_delete_entities(self) -> None:
        self.services.links.unlink(self.link.link_id, expected_version=self.link.version)
        self.assertEqual(self.services.todos.get_todo(self.todo.todo_id).title, "Aufgabe")
        self.assertEqual(self.services.calendar.get_event(self.event.event_id).title, "Termin")
        self.assertIsNotNone(self.services.links.get_link(self.link.link_id, include_deleted=True).deleted_at)

    def test_soft_deleted_todo_does_not_delete_event_or_link(self) -> None:
        self.services.todos.delete_todo(self.todo.todo_id, expected_version=self.todo.version)
        self.assertEqual(self.services.calendar.get_event(self.event.event_id).title, "Termin")
        self.assertIsNone(self.services.links.get_link(self.link.link_id).deleted_at)
        assessed = self.services.links.assess_conflict(self.link.link_id)
        self.assertEqual(assessed.conflict_status, LinkConflictStatus.DETACHED)

    def test_soft_deleted_event_does_not_delete_todo_or_link(self) -> None:
        self.services.calendar.delete_event(self.event.event_id, expected_version=self.event.version)
        self.assertEqual(self.services.todos.get_todo(self.todo.todo_id).title, "Aufgabe")
        assessed = self.services.links.assess_conflict(self.link.link_id)
        self.assertEqual(assessed.conflict_status, LinkConflictStatus.DETACHED)

    def test_conflict_matrix_detects_each_side(self) -> None:
        changed_todo = self.services.todos.update_todo(
            replace(self.todo, title="Aufgabe geändert"), expected_version=self.todo.version
        )
        assessed = self.services.links.assess_conflict(self.link.link_id)
        self.assertEqual(assessed.conflict_status, LinkConflictStatus.TODO_CHANGED)
        synced = self.services.links.mark_synchronized(assessed.link_id, expected_version=assessed.version)

        changed_event = self.services.calendar.update_event(
            replace(self.event, title="Termin geändert"), expected_version=self.event.version
        )
        assessed = self.services.links.assess_conflict(synced.link_id)
        self.assertEqual(assessed.conflict_status, LinkConflictStatus.CALENDAR_CHANGED)
        synced = self.services.links.mark_synchronized(assessed.link_id, expected_version=assessed.version)

        changed_todo = self.services.todos.update_todo(
            replace(changed_todo, description="nochmals"), expected_version=changed_todo.version
        )
        changed_event = self.services.calendar.update_event(
            replace(changed_event, description="nochmals"), expected_version=changed_event.version
        )
        assessed = self.services.links.assess_conflict(synced.link_id)
        self.assertEqual(assessed.conflict_status, LinkConflictStatus.BOTH_CHANGED)

    def test_subtasks_use_parent_without_cascade(self) -> None:
        child = self.services.todos.create_todo(title="Unteraufgabe", parent_id=self.todo.todo_id)
        self.assertEqual(self.services.todos.list_children(self.todo.todo_id)[0].todo_id, child.todo_id)
        self.services.todos.delete_todo(self.todo.todo_id, expected_version=self.todo.version)
        reopened_child = self.services.todos.get_todo(child.todo_id)
        self.assertEqual(reopened_child.parent_id, self.todo.todo_id)


if __name__ == "__main__":
    unittest.main()
