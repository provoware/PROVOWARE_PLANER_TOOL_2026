from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from services.factory import open_planner_services
from todo_core.model import LinkConflictStatus, LinkDirection, TodoStatus
from viewmodel.todo_query import TodoListMode, TodoQueryService
from viewmodel.todo_viewmodel import TodoViewModel


class I007QueryViewModelTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name)
        self.services = open_planner_services(self.workspace / "planer.sqlite3")
        self.zone = ZoneInfo("Europe/Berlin")
        self.now = datetime(2026, 8, 14, 10, 0, tzinfo=self.zone)
        self.query = TodoQueryService(self.services.todos, self.services.links, timezone_name="Europe/Berlin")
        self.vm = TodoViewModel(self.services.todos, self.services.links, timezone_name="Europe/Berlin")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _titles(self, mode: TodoListMode) -> set[str]:
        return {item.title for item in self.query.list(mode, now=self.now).items}

    def test_five_required_views_are_semantically_distinct(self) -> None:
        self.services.todos.create_todo(title="Heute", due_at=self.now + timedelta(hours=2))
        self.services.todos.create_todo(title="Diese Woche", due_at=self.now + timedelta(days=1))
        self.services.todos.create_todo(title="Überfällig", due_at=self.now - timedelta(days=1))
        self.services.todos.create_todo(title="Ohne Datum")
        self.services.todos.create_todo(title="Erledigt", status=TodoStatus.DONE, progress=100, due_at=self.now)

        self.assertIn("Heute", self._titles(TodoListMode.TODAY))
        self.assertIn("Diese Woche", self._titles(TodoListMode.THIS_WEEK))
        self.assertIn("Überfällig", self._titles(TodoListMode.OVERDUE))
        self.assertEqual(self._titles(TodoListMode.WITHOUT_DATE), {"Ohne Datum"})
        self.assertEqual(self._titles(TodoListMode.DONE), {"Erledigt"})
        self.assertNotIn("Erledigt", self._titles(TodoListMode.TODAY))

    def test_viewmodel_create_edit_status_progress_subtask_and_soft_delete(self) -> None:
        parent = self.vm.create_todo(title="Hauptaufgabe")
        child = self.vm.create_todo(title="Unteraufgabe", parent_id=parent.todo_id)
        self.assertEqual(child.parent_id, parent.todo_id)

        updated = self.vm.update_todo(
            parent.todo_id,
            title="Hauptaufgabe neu",
            description="Beschreibung",
            priority=parent.priority,
            status=TodoStatus.IN_PROGRESS,
            progress=40,
            start_at=None,
            due_at=None,
        )
        self.assertEqual(updated.progress, 40)
        progressed = self.vm.set_progress(parent.todo_id, 65)
        self.assertEqual(progressed.progress, 65)
        done = self.vm.set_status(parent.todo_id, TodoStatus.DONE)
        self.assertEqual(done.progress, 100)

        self.vm.soft_delete(child.todo_id)
        self.assertEqual(self.services.todos.list_children(parent.todo_id), [])
        self.assertIsNotNone(self.services.todos.get_todo(child.todo_id, include_deleted=True).deleted_at)

    def test_conflict_preview_is_visible_but_does_not_mutate_link(self) -> None:
        start = self.now + timedelta(hours=1)
        event = self.services.calendar.create_event(
            title="Termin",
            start_at=start,
            end_at=start + timedelta(hours=1),
            timezone_name="Europe/Berlin",
        )
        todo = self.services.todos.create_todo(title="Gekoppelt", due_at=start)
        link = self.services.links.create_link(todo.todo_id, event.event_id, direction=LinkDirection.BIDIRECTIONAL)

        todo_changed = self.services.todos.update_todo(replace(todo, title="Todo geändert"), expected_version=todo.version)
        event_changed = self.services.calendar.update_event(replace(event, title="Termin geändert"), expected_version=event.version)
        self.assertEqual(todo_changed.version, 2)
        self.assertEqual(event_changed.version, 2)

        view = self.query.one(todo.todo_id)
        self.assertEqual(view.links[0].conflict_status, LinkConflictStatus.BOTH_CHANGED)
        self.assertIn("Manuelle Prüfung", view.links[0].conflict_text)
        stored = self.services.links.get_link(link.link_id)
        self.assertEqual(stored.conflict_status, LinkConflictStatus.CLEAN)
        self.assertEqual(stored.version, 1)

    def test_unlink_never_deletes_todo_or_event(self) -> None:
        start = self.now + timedelta(hours=2)
        event = self.services.calendar.create_event(
            title="Bleibt",
            start_at=start,
            end_at=start + timedelta(hours=1),
            timezone_name="Europe/Berlin",
        )
        todo = self.services.todos.create_todo(title="Bleibt auch")
        link_id = self.vm.link_calendar(todo.todo_id, event.event_id, LinkDirection.MANUAL)
        self.vm.unlink(link_id)
        self.assertEqual(self.services.todos.get_todo(todo.todo_id).title, "Bleibt auch")
        self.assertEqual(self.services.calendar.get_event(event.event_id).title, "Bleibt")


if __name__ == "__main__":
    unittest.main()
