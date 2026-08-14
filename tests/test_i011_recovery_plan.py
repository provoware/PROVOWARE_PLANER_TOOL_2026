from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from services.factory import open_planner_services
from sync_core.errors import SyncPlanBlockedError, SyncStalePlanError
from sync_core.history import RecoveryMode, RecoveryPlanState
from sync_core.model import PlanFieldAction
from todo_core.model import LinkDirection


class I011RecoveryPlanTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="provoware-i011-recovery-")
        self.services = open_planner_services(Path(self.temp.name) / "planer.sqlite3")
        zone = ZoneInfo("Europe/Berlin")
        start = datetime(2026, 8, 14, 13, 0, tzinfo=zone)
        end = start + timedelta(hours=1)
        self.todo = self.services.todos.create_todo(
            title="Basis", description="Gemeinsam", start_at=start, due_at=end
        )
        self.event = self.services.calendar.create_event(
            title="Basis",
            description="Gemeinsam",
            start_at=start,
            end_at=end,
            timezone_name="Europe/Berlin",
        )
        self.link = self.services.links.create_link(
            self.todo.todo_id,
            self.event.event_id,
            direction=LinkDirection.BIDIRECTIONAL,
        )
        self.services.sync.initialize_baseline(self.link.link_id)
        todo2 = self.services.todos.update_todo(
            replace(self.todo, title="Nachher"),
            expected_version=self.todo.version,
        )
        self.first_receipt = self.services.sync.commit(self.services.sync.plan(self.link.link_id))
        self.todo = todo2

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _field(self, plan, field_id: str):
        return next(field for field in plan.fields if field.field_id == field_id)

    def test_reapply_after_builds_new_hash_bound_plan_and_reuses_current_side(self) -> None:
        current_event = self.services.calendar.get_event(self.event.event_id)
        self.services.calendar.update_event(
            replace(current_event, title="Abweichung"),
            expected_version=current_event.version,
        )
        plan = self.services.journal.build_recovery(
            self.first_receipt.receipt_id,
            RecoveryMode.REAPPLY_AFTER,
        )
        self.assertEqual(plan.state, RecoveryPlanState.READY)
        self.assertTrue(plan.write_permitted)
        self.assertTrue(plan.recovery_plan_id.startswith("RECOVERYPLAN-"))
        self.assertEqual(len(plan.recovery_sha256), 64)
        self.assertEqual(plan.source_receipt_sha256, self.first_receipt.receipt_sha256)
        title = self._field(plan, "TITLE")
        self.assertEqual(title.target_value, "Nachher")
        self.assertEqual(title.resolved_action, PlanFieldAction.TODO_TO_CALENDAR)

        receipt = self.services.journal.commit_recovery(plan)
        self.assertEqual(self.services.calendar.get_event(self.event.event_id).title, "Nachher")
        self.assertTrue(receipt.plan_id.startswith("RECOVERYPLAN-"))
        self.assertEqual(receipt.precondition_sha256, plan.recovery_sha256)
        self.assertEqual(self.services.journal.history_repository.snapshot_count(self.link.link_id), 2)

    def test_restore_before_divergent_historical_state_is_blocked(self) -> None:
        plan = self.services.journal.build_recovery(
            self.first_receipt.receipt_id,
            RecoveryMode.RESTORE_BEFORE,
        )
        self.assertEqual(plan.state, RecoveryPlanState.BLOCKED)
        self.assertFalse(plan.write_permitted)
        self.assertIn("unterschiedlich", plan.blocking_reason)
        with self.assertRaises(SyncPlanBlockedError):
            self.services.journal.commit_recovery(plan)

    def test_historical_target_absent_on_both_current_sides_is_blocked(self) -> None:
        current_todo = self.services.todos.get_todo(self.todo.todo_id)
        current_event = self.services.calendar.get_event(self.event.event_id)
        self.services.todos.update_todo(
            replace(current_todo, title="Todo ganz neu"),
            expected_version=current_todo.version,
        )
        self.services.calendar.update_event(
            replace(current_event, title="Kalender ganz neu"),
            expected_version=current_event.version,
        )
        plan = self.services.journal.build_recovery(
            self.first_receipt.receipt_id,
            RecoveryMode.REAPPLY_AFTER,
        )
        self.assertEqual(plan.state, RecoveryPlanState.BLOCKED)
        self.assertIn("keiner aktuellen Seite", plan.blocking_reason)

    def test_stale_recovery_plan_is_rejected_before_write(self) -> None:
        current_event = self.services.calendar.get_event(self.event.event_id)
        self.services.calendar.update_event(
            replace(current_event, title="Abweichung"),
            expected_version=current_event.version,
        )
        plan = self.services.journal.build_recovery(
            self.first_receipt.receipt_id,
            RecoveryMode.REAPPLY_AFTER,
        )
        current_todo = self.services.todos.get_todo(self.todo.todo_id)
        self.services.todos.update_todo(
            replace(current_todo, description="Nach Plan geändert"),
            expected_version=current_todo.version,
        )
        with self.assertRaises(SyncStalePlanError):
            self.services.journal.commit_recovery(plan)

    def test_tampered_recovery_plan_is_rejected(self) -> None:
        from dataclasses import replace as dc_replace

        current_event = self.services.calendar.get_event(self.event.event_id)
        self.services.calendar.update_event(
            replace(current_event, title="Abweichung"),
            expected_version=current_event.version,
        )
        plan = self.services.journal.build_recovery(
            self.first_receipt.receipt_id,
            RecoveryMode.REAPPLY_AFTER,
        )
        title = self._field(plan, "TITLE")
        tampered_title = dc_replace(title, resolved_action=PlanFieldAction.CALENDAR_TO_TODO)
        tampered = dc_replace(
            plan,
            fields=tuple(tampered_title if f.field_id == "TITLE" else f for f in plan.fields),
        )
        with self.assertRaises(SyncStalePlanError):
            self.services.journal.commit_recovery(tampered)

    def test_legacy_receipt_can_never_be_recovered_automatically(self) -> None:
        with self.services.database.transaction() as connection:
            connection.execute(
                "DELETE FROM sync_history_snapshots WHERE receipt_id=?",
                (self.first_receipt.receipt_id,),
            )
        plan = self.services.journal.build_recovery(
            self.first_receipt.receipt_id,
            RecoveryMode.REAPPLY_AFTER,
        )
        self.assertEqual(plan.state, RecoveryPlanState.BLOCKED)
        self.assertIn("keinen I011-Wertsnapshot", plan.blocking_reason)


if __name__ == "__main__":
    unittest.main()
