from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from services.factory import open_planner_services
from sync_core.canonical import payload_hash
from sync_core.errors import SyncPlanBlockedError, SyncStalePlanError
from sync_core.model import FieldChangeState, PlanFieldAction, SyncPlanState
from todo_core.model import LinkDirection


class I009ThreeWaySyncTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="provoware-i009-")
        self.services = open_planner_services(Path(self.temp.name) / "planer.sqlite3")
        zone = ZoneInfo("Europe/Berlin")
        self.start = datetime(2026, 8, 14, 10, 0, tzinfo=zone)
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

    def field(self, plan, field_id: str):
        return next(item for item in plan.fields if item.field_id == field_id)

    def test_four_field_baselines_are_bound_with_hashes(self) -> None:
        baselines = self.services.sync.baselines(self.link.link_id)
        self.assertEqual({item.field_id for item in baselines}, {"TITLE", "DESCRIPTION", "START_AT", "DUE_END"})
        self.assertTrue(all(len(item.baseline_sha256) == 64 for item in baselines))
        self.assertEqual(self.services.database.schema_version(), 3)

    def test_todo_only_change_commits_to_calendar_and_receipt(self) -> None:
        changed = self.services.todos.update_todo(
            replace(self.todo, title="Todo neu"), expected_version=self.todo.version
        )
        plan = self.services.sync.plan(self.link.link_id)
        title = self.field(plan, "TITLE")
        self.assertEqual(title.state, FieldChangeState.TODO_ONLY)
        self.assertEqual(title.action, PlanFieldAction.TODO_TO_CALENDAR)
        self.assertEqual(plan.state, SyncPlanState.READY)
        receipt = self.services.sync.commit(plan)
        stored = self.services.calendar.get_event(self.event.event_id)
        self.assertEqual(stored.title, changed.title)
        self.assertEqual(receipt.event_version_after, self.event.version + 1)
        self.assertEqual(self.services.sync.receipt_count(self.link.link_id), 1)
        self.assertEqual(payload_hash(json.loads(receipt.payload_json)), receipt.receipt_sha256)

    def test_disjoint_both_changed_is_losslessly_merged(self) -> None:
        todo = self.services.todos.update_todo(
            replace(self.todo, title="Nur Todo"), expected_version=self.todo.version
        )
        event = self.services.calendar.update_event(
            replace(self.event, description="Nur Kalender"), expected_version=self.event.version
        )
        self.assertEqual(self.services.links.preview_conflict(self.link.link_id).value, "BOTH_CHANGED")
        plan = self.services.sync.plan(self.link.link_id)
        self.assertEqual(self.field(plan, "TITLE").state, FieldChangeState.TODO_ONLY)
        self.assertEqual(self.field(plan, "DESCRIPTION").state, FieldChangeState.CALENDAR_ONLY)
        self.assertEqual(plan.state, SyncPlanState.READY)
        receipt = self.services.sync.commit(plan)
        stored_todo = self.services.todos.get_todo(todo.todo_id)
        stored_event = self.services.calendar.get_event(event.event_id)
        self.assertEqual(stored_event.title, "Nur Todo")
        self.assertEqual(stored_todo.description, "Nur Kalender")
        self.assertEqual(self.services.links.preview_conflict(self.link.link_id).value, "CLEAN")
        self.assertEqual(receipt.todo_version_after, todo.version + 1)
        self.assertEqual(receipt.event_version_after, event.version + 1)

    def test_same_field_both_same_promotes_baseline_without_entity_write(self) -> None:
        todo = self.services.todos.update_todo(
            replace(self.todo, title="Gleicher neuer Wert"), expected_version=self.todo.version
        )
        event = self.services.calendar.update_event(
            replace(self.event, title="Gleicher neuer Wert"), expected_version=self.event.version
        )
        plan = self.services.sync.plan(self.link.link_id)
        title = self.field(plan, "TITLE")
        self.assertEqual(title.state, FieldChangeState.BOTH_SAME)
        self.assertEqual(title.action, PlanFieldAction.PROMOTE_BASELINE)
        self.assertEqual(plan.entity_write_count, 0)
        receipt = self.services.sync.commit(plan)
        self.assertEqual(receipt.todo_version_after, todo.version)
        self.assertEqual(receipt.event_version_after, event.version)
        self.assertEqual(self.services.links.preview_conflict(self.link.link_id).value, "CLEAN")

    def test_same_field_both_different_is_hard_blocked(self) -> None:
        self.services.todos.update_todo(
            replace(self.todo, title="Todo A"), expected_version=self.todo.version
        )
        self.services.calendar.update_event(
            replace(self.event, title="Kalender B"), expected_version=self.event.version
        )
        plan = self.services.sync.plan(self.link.link_id)
        self.assertEqual(self.field(plan, "TITLE").state, FieldChangeState.BOTH_DIFFERENT)
        self.assertEqual(plan.state, SyncPlanState.BLOCKED_CONFLICT)
        self.assertFalse(plan.write_permitted)
        with self.assertRaises(SyncPlanBlockedError):
            self.services.sync.commit(plan)
        self.assertEqual(self.services.sync.receipt_count(self.link.link_id), 0)

    def test_missing_baseline_blocks_existing_link(self) -> None:
        todo = self.services.todos.create_todo(title="Ohne Baseline", start_at=self.start, due_at=self.end)
        event = self.services.calendar.create_event(
            title="Ohne Baseline", start_at=self.start, end_at=self.end, timezone_name="Europe/Berlin"
        )
        link = self.services.links.create_link(todo.todo_id, event.event_id, direction=LinkDirection.BIDIRECTIONAL)
        plan = self.services.sync.plan(link.link_id)
        self.assertEqual(plan.state, SyncPlanState.BLOCKED_BASELINE)
        self.assertTrue(all(field.state is FieldChangeState.BASELINE_MISSING for field in plan.fields))

    def test_due_end_one_sided_change_requires_manual_review(self) -> None:
        self.services.todos.update_todo(
            replace(self.todo, due_at=self.end + timedelta(hours=1)), expected_version=self.todo.version
        )
        plan = self.services.sync.plan(self.link.link_id)
        due = self.field(plan, "DUE_END")
        self.assertEqual(due.action, PlanFieldAction.REVIEW_REQUIRED)
        self.assertEqual(plan.state, SyncPlanState.MANUAL_REVIEW)
        self.assertFalse(plan.write_permitted)

    def test_direction_contract_blocks_wrong_side(self) -> None:
        todo = self.services.todos.create_todo(
            title="Richtung", description="X", start_at=self.start, due_at=self.end
        )
        event = self.services.calendar.create_event(
            title="Richtung", description="X", start_at=self.start, end_at=self.end,
            timezone_name="Europe/Berlin"
        )
        link = self.services.links.create_link(todo.todo_id, event.event_id, direction=LinkDirection.TODO_TO_CALENDAR)
        self.services.sync.initialize_baseline(link.link_id)
        self.services.calendar.update_event(replace(event, description="Kalender neu"), expected_version=event.version)
        plan = self.services.sync.plan(link.link_id)
        self.assertEqual(self.field(plan, "DESCRIPTION").state, FieldChangeState.CALENDAR_ONLY)
        self.assertEqual(self.field(plan, "DESCRIPTION").action, PlanFieldAction.BLOCKED)
        self.assertEqual(plan.state, SyncPlanState.BLOCKED_DIRECTION)

    def test_stale_plan_is_rejected_before_any_commit(self) -> None:
        todo = self.services.todos.update_todo(
            replace(self.todo, title="Geplant"), expected_version=self.todo.version
        )
        plan = self.services.sync.plan(self.link.link_id)
        self.services.todos.update_todo(
            replace(todo, description="Nach PRECHECK geändert"), expected_version=todo.version
        )
        with self.assertRaises(SyncStalePlanError):
            self.services.sync.commit(plan)
        self.assertEqual(self.services.calendar.get_event(self.event.event_id).title, "Basis")
        self.assertEqual(self.services.sync.receipt_count(self.link.link_id), 0)


if __name__ == "__main__":
    unittest.main()
