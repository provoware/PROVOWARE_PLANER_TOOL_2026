from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from todo_core.errors import TodoValidationError
from todo_core.model import LinkConflictStatus, LinkDirection, TodoCalendarLink, TodoItem, TodoStatus


class I006DomainTest(unittest.TestCase):
    def test_done_requires_full_progress(self) -> None:
        with self.assertRaisesRegex(TodoValidationError, "TODO-DOMAIN-008"):
            TodoItem(todo_id="t1", title="Erledigt", status=TodoStatus.DONE, progress=99)

    def test_due_must_not_be_before_start(self) -> None:
        start = datetime.now(timezone.utc)
        with self.assertRaisesRegex(TodoValidationError, "TODO-DOMAIN-005"):
            TodoItem(todo_id="t1", title="Zeit", start_at=start, due_at=start - timedelta(minutes=1))

    def test_self_parent_is_forbidden(self) -> None:
        with self.assertRaisesRegex(TodoValidationError, "TODO-DOMAIN-006"):
            TodoItem(todo_id="t1", title="Selbst", parent_id="t1")

    def test_naive_datetime_is_forbidden(self) -> None:
        with self.assertRaisesRegex(TodoValidationError, "TODO-DOMAIN-004"):
            TodoItem(todo_id="t1", title="Zeit", due_at=datetime(2026, 8, 14, 10, 0))

    def test_link_has_own_identity_direction_and_conflict_state(self) -> None:
        link = TodoCalendarLink(
            link_id="l1", todo_id="t1", event_id="e1", direction=LinkDirection.BIDIRECTIONAL,
            conflict_status=LinkConflictStatus.CLEAN,
        )
        self.assertEqual(link.link_id, "l1")
        self.assertEqual(link.direction, LinkDirection.BIDIRECTIONAL)
        self.assertEqual(link.conflict_status, LinkConflictStatus.CLEAN)


if __name__ == "__main__":
    unittest.main()
