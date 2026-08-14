from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from services.factory import open_planner_services
from services.resolution_service import ResolutionService
from sync_core.resolution import ResolutionChoice, ResolutionPlanState
from todo_core.model import LinkDirection
from viewmodel.sync_control_query import SyncControlQuery
from viewmodel.sync_control_viewmodel import SyncControlViewModel


class I010SyncControlQueryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="provoware-i010-query-")
        self.services = open_planner_services(Path(self.temp.name) / "planer.sqlite3")
        self.resolution = ResolutionService(self.services.sync, self.services.sync.repository)
        zone = ZoneInfo("Europe/Berlin")
        start = datetime(2026, 8, 14, 12, 0, tzinfo=zone)
        end = start + timedelta(hours=1)
        self.todo = self.services.todos.create_todo(
            title="Basis", description="Basis", start_at=start, due_at=end
        )
        self.event = self.services.calendar.create_event(
            title="Basis", description="Basis", start_at=start, end_at=end, timezone_name="Europe/Berlin"
        )
        self.link = self.services.links.create_link(
            self.todo.todo_id, self.event.event_id, direction=LinkDirection.BIDIRECTIONAL
        )
        self.services.sync.initialize_baseline(self.link.link_id)
        self.query = SyncControlQuery(self.services.sync)
        self.vm = SyncControlViewModel(self.query, self.services.sync, self.resolution)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_query_is_read_only_and_exposes_required_columns(self) -> None:
        before_receipts = self.services.sync.receipt_count(self.link.link_id)
        snapshot = self.query.load(self.link.link_id)
        self.assertEqual(len(snapshot.rows), 4)
        row = snapshot.rows[0]
        self.assertTrue(row.baseline_text)
        self.assertTrue(row.todo_text)
        self.assertTrue(row.calendar_text)
        self.assertTrue(row.state_text)
        self.assertTrue(row.action_text)
        self.assertTrue(row.reason)
        self.assertIn("AKTUELL", row.version_status)
        self.assertIn("SHA-256", row.hash_status)
        self.assertEqual(self.services.sync.receipt_count(self.link.link_id), before_receipts)

    def test_viewmodel_defaults_both_different_to_blocked(self) -> None:
        self.services.todos.update_todo(replace(self.todo, title="Todo"), expected_version=self.todo.version)
        self.services.calendar.update_event(replace(self.event, title="Kalender"), expected_version=self.event.version)
        snapshot = self.vm.load(self.link.link_id)
        self.assertIn(self.link.link_id, self.vm.link_ids())
        self.assertEqual(self.vm.decisions["TITLE"], ResolutionChoice.KEEP_BLOCKED)
        plan = self.vm.resolution_plan()
        self.assertEqual(plan.state, ResolutionPlanState.BLOCKED)
        self.vm.choose("TITLE", ResolutionChoice.TODO_VALUE)
        self.assertEqual(self.vm.prepare_resolution().state, ResolutionPlanState.READY)

    def test_non_conflict_field_cannot_receive_manual_decision(self) -> None:
        self.vm.load(self.link.link_id)
        with self.assertRaises(ValueError):
            self.vm.choose("DESCRIPTION", ResolutionChoice.TODO_VALUE)


if __name__ == "__main__":
    unittest.main()
