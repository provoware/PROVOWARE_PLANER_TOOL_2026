from __future__ import annotations

import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from calendar_core.errors import MarkerNotFoundError
from calendar_core.model import MarkerType
from services.factory import open_calendar_service
from viewmodel.calendar_viewmodel import CalendarViewMode, CalendarViewModel


class I005ViewModelTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.service = open_calendar_service(self.root / "planer.sqlite3")
        self.zone = ZoneInfo("Europe/Berlin")
        self.vm = CalendarViewModel(
            self.service,
            timezone_name="Europe/Berlin",
            reference_date=date(2026, 8, 14),
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _event(self, day: int, marker_id: int = 1):
        start = datetime(2026, 8, day, 10, 0, tzinfo=self.zone)
        return self.service.create_event(
            title=f"Termin {day}",
            description="Test",
            start_at=start,
            end_at=start + timedelta(hours=1),
            timezone_name="Europe/Berlin",
            marker_id=marker_id,
        )

    def test_four_views_use_same_service_data(self) -> None:
        self._event(14, 1)
        self._event(15, 2)
        self.vm.set_mode(CalendarViewMode.DAY)
        self.assertEqual(len(self.vm.snapshot().events), 1)
        self.vm.set_mode(CalendarViewMode.WEEK)
        self.assertEqual(sum(len(day.events) for day in self.vm.snapshot().days), 2)
        self.vm.set_mode(CalendarViewMode.MONTH)
        self.assertEqual(sum(len(cell.events) for week in self.vm.snapshot().weeks for cell in week), 2)
        self.vm.set_mode(CalendarViewMode.YEAR)
        self.assertEqual(sum(month.event_count for month in self.vm.snapshot().months), 2)

    def test_navigation_respects_view_granularity(self) -> None:
        expected = {
            CalendarViewMode.DAY: date(2026, 8, 15),
            CalendarViewMode.WEEK: date(2026, 8, 21),
            CalendarViewMode.MONTH: date(2026, 9, 14),
            CalendarViewMode.YEAR: date(2027, 8, 14),
        }
        for mode, target in expected.items():
            self.vm.reference_date = date(2026, 8, 14)
            self.vm.set_mode(mode)
            self.vm.navigate(1)
            self.assertEqual(self.vm.reference_date, target)

    def test_marker_edit_is_persistent_and_visible_in_view(self) -> None:
        marker = self.service.list_markers()[0]
        updated = MarkerType(
            marker_id=marker.marker_id,
            title="Gesundheit",
            short_title="GES",
            color="#008577",
            symbol="◆",
            description="Arzt und Gesundheit",
            enabled=True,
        )
        self.vm.update_marker(updated)
        self._event(14, 1)
        visible = self.vm.query.day(date(2026, 8, 14)).events[0]
        self.assertEqual(visible.marker.title, "Gesundheit")
        reopened = open_calendar_service(self.root / "planer.sqlite3")
        self.assertEqual(reopened.list_markers()[0].title, "Gesundheit")

    def test_marker_semantics_do_not_depend_on_color(self) -> None:
        self._event(14, 3)
        visible = self.vm.query.day(date(2026, 8, 14)).events[0]
        self.assertIn("M3", visible.marker_text)
        self.assertIn("Markierung 3", visible.marker_text)
        self.assertNotIn(visible.marker.color, visible.display_text)

    def test_marker_batch_is_atomic_on_missing_fixed_marker(self) -> None:
        original = tuple(self.service.list_markers())
        changed_first = MarkerType(
            marker_id=1,
            title="Geändert",
            short_title="NEU",
            color="#112233",
            symbol="◆",
            description="Soll zurückgerollt werden",
            enabled=True,
        )
        with self.service.repository.database.transaction() as connection:
            connection.execute("DELETE FROM marker_types WHERE marker_id = 5")
        batch = (changed_first,) + original[1:]
        with self.assertRaises(MarkerNotFoundError):
            self.service.update_markers(batch)
        self.assertEqual(self.service.list_markers()[0].title, original[0].title)


if __name__ == "__main__":
    unittest.main()
