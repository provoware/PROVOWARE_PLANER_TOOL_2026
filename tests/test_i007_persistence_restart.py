from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from services.factory import open_planner_services
from todo_core.model import LinkDirection
from viewmodel.todo_query import TodoListMode, TodoQueryService


class I007PersistenceRestartTest(unittest.TestCase):
    def test_todo_and_calendar_link_survive_service_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            db_path = workspace / "planer.sqlite3"
            zone = ZoneInfo("Europe/Berlin")
            now = datetime.now(zone).replace(second=0, microsecond=0)

            first = open_planner_services(db_path)
            todo = first.todos.create_todo(title="Bleibt nach Neustart", due_at=now + timedelta(hours=1))
            event = first.calendar.create_event(
                title="Persistenter Termin",
                start_at=now + timedelta(hours=2),
                end_at=now + timedelta(hours=3),
                timezone_name="Europe/Berlin",
            )
            link = first.links.create_link(todo.todo_id, event.event_id, direction=LinkDirection.MANUAL)
            first.database.quick_check()

            second = open_planner_services(db_path)
            loaded = second.todos.get_todo(todo.todo_id)
            loaded_link = second.links.get_link(link.link_id)
            query = TodoQueryService(second.todos, second.links, timezone_name="Europe/Berlin")
            snapshot = query.list(TodoListMode.TODAY, now=now)

            self.assertEqual(loaded.title, "Bleibt nach Neustart")
            self.assertEqual(loaded_link.todo_id, todo.todo_id)
            self.assertEqual(loaded_link.event_id, event.event_id)
            self.assertIn(todo.todo_id, {item.todo_id for item in snapshot.items})
            second.database.quick_check()


if __name__ == "__main__":
    unittest.main()
