from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from services.factory import open_planner_services
from sync_core.model import SyncFieldAction, SyncPreviewState
from todo_core.model import LinkConflictStatus, LinkDirection


class I008SyncPreviewTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="provoware-i008-")
        self.workspace = Path(self.temp.name)
        self.services = open_planner_services(self.workspace / "planer.sqlite3")
        zone = ZoneInfo("Europe/Berlin")
        self.start = datetime(2026, 8, 14, 9, 0, tzinfo=zone)
        self.todo = self.services.todos.create_todo(
            title="Plan",
            description="Beschreibung",
            start_at=self.start,
            due_at=self.start + timedelta(hours=2),
        )
        self.event = self.services.calendar.create_event(
            title="Plan",
            description="Beschreibung",
            start_at=self.start,
            end_at=self.start + timedelta(hours=2),
            timezone_name="Europe/Berlin",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _link(self, direction: LinkDirection = LinkDirection.BIDIRECTIONAL):
        return self.services.links.create_link(self.todo.todo_id, self.event.event_id, direction=direction)

    def test_clean_equal_link_has_no_change_and_never_writes(self) -> None:
        link = self._link()
        preview = self.services.sync_preview.preview(link.link_id)
        self.assertEqual(preview.state, SyncPreviewState.KEINE_AENDERUNG)
        self.assertFalse(preview.write_permitted)
        self.assertFalse(preview.has_differences)
        stored = self.services.links.get_link(link.link_id)
        self.assertEqual(stored.version, 1)
        self.assertEqual(stored.conflict_status, LinkConflictStatus.CLEAN)

    def test_todo_changed_proposes_only_allowed_safe_fields(self) -> None:
        link = self._link(LinkDirection.TODO_TO_CALENDAR)
        changed = self.services.todos.update_todo(
            replace(self.todo, title="Neuer Plan", description="Neu"), expected_version=self.todo.version
        )
        preview = self.services.sync_preview.preview(link.link_id)
        self.assertEqual(preview.conflict_status, LinkConflictStatus.TODO_CHANGED)
        actions = {field.field_id: field.action for field in preview.fields}
        self.assertEqual(actions["TITLE"], SyncFieldAction.TODO_ZU_KALENDER)
        self.assertEqual(actions["DESCRIPTION"], SyncFieldAction.TODO_ZU_KALENDER)
        self.assertEqual(actions["DUE_END"], SyncFieldAction.IDENTISCH)
        self.assertEqual(preview.todo_version, changed.version)
        self.assertFalse(preview.write_permitted)

    def test_due_end_difference_requires_semantic_review(self) -> None:
        link = self._link(LinkDirection.TODO_TO_CALENDAR)
        self.services.todos.update_todo(
            replace(self.todo, due_at=self.start + timedelta(hours=3)), expected_version=self.todo.version
        )
        preview = self.services.sync_preview.preview(link.link_id)
        due = next(field for field in preview.fields if field.field_id == "DUE_END")
        self.assertEqual(due.action, SyncFieldAction.PRUEFUNG_ERFORDERLICH)
        self.assertFalse(due.automatic_candidate)
        self.assertEqual(preview.state, SyncPreviewState.MANUELLE_PRUEFUNG)

    def test_wrong_direction_blocks_proposal(self) -> None:
        link = self._link(LinkDirection.CALENDAR_TO_TODO)
        self.services.todos.update_todo(replace(self.todo, title="Todo neu"), expected_version=self.todo.version)
        preview = self.services.sync_preview.preview(link.link_id)
        title = next(field for field in preview.fields if field.field_id == "TITLE")
        self.assertEqual(title.action, SyncFieldAction.BLOCKIERT)
        self.assertEqual(preview.state, SyncPreviewState.BLOCKIERT_RICHTUNG)

    def test_both_changed_is_hard_blocked_without_link_mutation(self) -> None:
        link = self._link()
        self.services.todos.update_todo(replace(self.todo, title="Todo neu"), expected_version=self.todo.version)
        self.services.calendar.update_event(replace(self.event, title="Termin neu"), expected_version=self.event.version)
        preview = self.services.sync_preview.preview(link.link_id)
        self.assertEqual(preview.conflict_status, LinkConflictStatus.BOTH_CHANGED)
        self.assertEqual(preview.state, SyncPreviewState.BLOCKIERT_BEIDSEITIG)
        self.assertTrue(all(
            field.action in {SyncFieldAction.IDENTISCH, SyncFieldAction.BLOCKIERT}
            for field in preview.fields
        ))
        stored = self.services.links.get_link(link.link_id)
        self.assertEqual(stored.version, 1)
        self.assertEqual(stored.conflict_status, LinkConflictStatus.CLEAN)

    def test_clean_but_divergent_baseline_is_blocked(self) -> None:
        other = self.services.calendar.create_event(
            title="Anderer Titel",
            description="Andere Beschreibung",
            start_at=self.start + timedelta(hours=1),
            end_at=self.start + timedelta(hours=2),
            timezone_name="Europe/Berlin",
        )
        link = self.services.links.create_link(self.todo.todo_id, other.event_id, direction=LinkDirection.BIDIRECTIONAL)
        preview = self.services.sync_preview.preview(link.link_id)
        self.assertEqual(preview.conflict_status, LinkConflictStatus.CLEAN)
        self.assertEqual(preview.state, SyncPreviewState.BLOCKIERT_BASISABWEICHUNG)
        self.assertFalse(preview.write_permitted)

    def test_detached_endpoint_is_hard_blocked(self) -> None:
        link = self._link()
        self.services.todos.delete_todo(self.todo.todo_id, expected_version=self.todo.version)
        preview = self.services.sync_preview.preview(link.link_id)
        self.assertEqual(preview.conflict_status, LinkConflictStatus.DETACHED)
        self.assertEqual(preview.state, SyncPreviewState.BLOCKIERT_GETRENNT)
        self.assertFalse(preview.write_permitted)


if __name__ == "__main__":
    unittest.main()
