from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from services.factory import open_planner_services
from sync_core.errors import SyncStalePlanError
from sync_core.model import PlanFieldAction
from todo_core.model import LinkDirection


class I009PlanTamperTest(unittest.TestCase):
    def test_manually_changed_field_action_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provoware-i009-tamper-") as temp:
            services = open_planner_services(Path(temp) / "planer.sqlite3")
            zone = ZoneInfo("Europe/Berlin")
            start = datetime(2026, 8, 14, 9, 0, tzinfo=zone)
            end = start + timedelta(hours=1)
            todo = services.todos.create_todo(title="Basis", description="Text", start_at=start, due_at=end)
            event = services.calendar.create_event(
                title="Basis", description="Text", start_at=start, end_at=end, timezone_name="Europe/Berlin"
            )
            link = services.links.create_link(todo.todo_id, event.event_id, direction=LinkDirection.BIDIRECTIONAL)
            services.sync.initialize_baseline(link.link_id)
            services.todos.update_todo(replace(todo, title="Todo neu"), expected_version=todo.version)
            plan = services.sync.plan(link.link_id)
            title = next(field for field in plan.fields if field.field_id == "TITLE")
            tampered_title = replace(title, action=PlanFieldAction.CALENDAR_TO_TODO)
            tampered = replace(
                plan,
                fields=tuple(tampered_title if field.field_id == "TITLE" else field for field in plan.fields),
            )
            with self.assertRaises(SyncStalePlanError):
                services.sync.commit(tampered)
            self.assertEqual(services.calendar.get_event(event.event_id).title, "Basis")
            self.assertEqual(services.sync.receipt_count(link.link_id), 0)


if __name__ == "__main__":
    unittest.main()
