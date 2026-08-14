from __future__ import annotations

import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from services.factory import open_calendar_service
from viewmodel.calendar_query import CalendarQueryService


class I005PersistenceRestartTest(unittest.TestCase):
    def test_event_survives_service_and_viewmodel_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            db = root / "planer.sqlite3"
            zone = ZoneInfo("Europe/Berlin")
            first = open_calendar_service(db)
            start = datetime(2026, 8, 14, 18, 30, tzinfo=zone)
            created = first.create_event(
                title="Persistenz nach Neustart",
                start_at=start,
                end_at=start + timedelta(hours=2),
                timezone_name="Europe/Berlin",
                marker_id=5,
            )
            second = open_calendar_service(db)
            query = CalendarQueryService(second, timezone_name="Europe/Berlin")
            events = query.day(date(2026, 8, 14)).events
            self.assertEqual([item.event_id for item in events], [created.event_id])
            self.assertEqual(events[0].title, "Persistenz nach Neustart")
            self.assertEqual(events[0].marker.marker_id, 5)


if __name__ == "__main__":
    unittest.main()
