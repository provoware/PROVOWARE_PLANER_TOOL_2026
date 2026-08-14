from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from services.factory import open_planner_services
from services.resolution_service import ResolutionService
from sync_core.errors import SyncPlanBlockedError, SyncStalePlanError
from sync_core.model import FieldChangeState, PlanFieldAction, SyncPlanState
from sync_core.resolution import ResolutionChoice, ResolutionPlanState, sync_plan_hash
from todo_core.model import LinkDirection


class I010ResolutionPlanTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="provoware-i010-")
        self.services = open_planner_services(Path(self.temp.name) / "planer.sqlite3")
        self.resolution = ResolutionService(self.services.sync, self.services.sync.repository)
        zone = ZoneInfo("Europe/Berlin")
        self.start = datetime(2026, 8, 14, 11, 0, tzinfo=zone)
        self.end = self.start + timedelta(hours=1)
        self.todo = self.services.todos.create_todo(
            title="Basis", description="Gemeinsam", start_at=self.start, due_at=self.end
        )
        self.event = self.services.calendar.create_event(
            title="Basis", description="Gemeinsam", start_at=self.start, end_at=self.end,
            timezone_name="Europe/Berlin"
        )
        self.link = self.services.links.create_link(
            self.todo.todo_id, self.event.event_id, direction=LinkDirection.BIDIRECTIONAL
        )
        self.services.sync.initialize_baseline(self.link.link_id)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _conflict(self):
        todo = self.services.todos.update_todo(
            replace(self.todo, title="Todo entscheidet"), expected_version=self.todo.version
        )
        event = self.services.calendar.update_event(
            replace(self.event, title="Kalender entscheidet"), expected_version=self.event.version
        )
        source = self.services.sync.plan(self.link.link_id)
        self.assertEqual(source.state, SyncPlanState.BLOCKED_CONFLICT)
        return todo, event, source

    def _field(self, plan, field_id: str):
        return next(item for item in plan.fields if item.field_id == field_id)

    def test_resolution_plan_is_new_immutable_hash_bound_object(self) -> None:
        _todo, _event, source = self._conflict()
        before = source
        plan = self.resolution.build(source, {"TITLE": ResolutionChoice.TODO_VALUE})
        self.assertIs(source, before)
        self.assertNotEqual(plan.resolution_plan_id, source.plan_id)
        self.assertEqual(plan.source_plan_id, source.plan_id)
        self.assertEqual(plan.source_plan_sha256, sync_plan_hash(source))
        self.assertEqual(len(plan.resolution_sha256), 64)
        self.assertEqual(plan.state, ResolutionPlanState.READY)
        title = self._field(plan, "TITLE")
        self.assertEqual(title.original_state, FieldChangeState.BOTH_DIFFERENT)
        self.assertEqual(title.choice, ResolutionChoice.TODO_VALUE)
        self.assertEqual(title.resolved_action, PlanFieldAction.TODO_TO_CALENDAR)

    def test_keep_blocked_is_default_and_never_writes(self) -> None:
        _todo, _event, source = self._conflict()
        plan = self.resolution.build(source, {})
        self.assertEqual(plan.state, ResolutionPlanState.BLOCKED)
        self.assertFalse(plan.write_permitted)
        with self.assertRaises(SyncPlanBlockedError):
            self.resolution.commit(plan)
        self.assertEqual(self.services.sync.receipt_count(self.link.link_id), 0)
        self.assertEqual(self.services.calendar.get_event(self.event.event_id).title, "Kalender entscheidet")

    def test_todo_choice_commits_atomically_and_receipt_proves_conflict_and_choice(self) -> None:
        todo, _event, source = self._conflict()
        plan = self.resolution.build(source, {"TITLE": ResolutionChoice.TODO_VALUE})
        receipt = self.resolution.commit(plan)
        self.assertEqual(self.services.calendar.get_event(self.event.event_id).title, todo.title)
        payload = json.loads(receipt.payload_json)
        title = next(item for item in payload["fields"] if item["field_id"] == "TITLE")
        self.assertEqual(title["state"], "BOTH_DIFFERENT")
        self.assertEqual(title["action"], "TODO_TO_CALENDAR")
        self.assertEqual(receipt.plan_id, plan.resolution_plan_id)
        self.assertEqual(receipt.precondition_sha256, plan.resolution_sha256)
        self.assertEqual(self.services.links.preview_conflict(self.link.link_id).value, "CLEAN")

    def test_calendar_choice_commits_calendar_value(self) -> None:
        _todo, event, source = self._conflict()
        plan = self.resolution.build(source, {"TITLE": ResolutionChoice.CALENDAR_VALUE})
        self.resolution.commit(plan)
        self.assertEqual(self.services.todos.get_todo(self.todo.todo_id).title, event.title)

    def test_stale_source_plan_is_rejected_before_write(self) -> None:
        todo, _event, source = self._conflict()
        plan = self.resolution.build(source, {"TITLE": ResolutionChoice.TODO_VALUE})
        self.services.todos.update_todo(
            replace(todo, description="Nach Entscheidung verändert"), expected_version=todo.version
        )
        with self.assertRaises(SyncStalePlanError):
            self.resolution.commit(plan)
        self.assertEqual(self.services.sync.receipt_count(self.link.link_id), 0)

    def test_tampered_resolution_plan_is_rejected(self) -> None:
        _todo, _event, source = self._conflict()
        plan = self.resolution.build(source, {"TITLE": ResolutionChoice.TODO_VALUE})
        title = self._field(plan, "TITLE")
        tampered_field = replace(title, resolved_action=PlanFieldAction.CALENDAR_TO_TODO)
        tampered = replace(
            plan,
            fields=tuple(tampered_field if field.field_id == "TITLE" else field for field in plan.fields),
        )
        with self.assertRaises(SyncStalePlanError):
            self.resolution.commit(tampered)
        self.assertEqual(self.services.sync.receipt_count(self.link.link_id), 0)

    def test_multiple_conflicts_require_explicit_decision_for_every_field(self) -> None:
        todo = self.services.todos.update_todo(
            replace(self.todo, title="Todo A", description="Todo B"), expected_version=self.todo.version
        )
        self.services.calendar.update_event(
            replace(self.event, title="Kal A", description="Kal B"), expected_version=self.event.version
        )
        source = self.services.sync.plan(self.link.link_id)
        partial = self.resolution.build(source, {"TITLE": ResolutionChoice.TODO_VALUE})
        self.assertEqual(partial.state, ResolutionPlanState.BLOCKED)
        complete = self.resolution.build(
            source,
            {
                "TITLE": ResolutionChoice.TODO_VALUE,
                "DESCRIPTION": ResolutionChoice.CALENDAR_VALUE,
            },
        )
        self.assertEqual(complete.state, ResolutionPlanState.READY)
        receipt = self.resolution.commit(complete)
        self.assertEqual(receipt.todo_version_after, todo.version + 1)


if __name__ == "__main__":
    unittest.main()
