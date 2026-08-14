from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from services.factory import open_calendar_service


class CalendarFactoryTest(unittest.TestCase):
    def test_factory_initializes_schema_backup_and_service(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            database = root / "planner.sqlite3"
            backups = root / "migration-backups"
            service = open_calendar_service(database, backup_dir=backups)
            start = datetime(2026, 8, 14, 10, 0, tzinfo=ZoneInfo("Europe/Berlin"))
            event = service.create_event(
                title="Factory-Test",
                start_at=start,
                end_at=start + timedelta(hours=1),
                timezone_name="Europe/Berlin",
            )
            self.assertEqual(service.get_event(event.event_id).title, "Factory-Test")
            backup = backups / "pre_migration_v0001.sqlite3"
            self.assertTrue(backup.is_file())
            self.assertTrue(backup.with_suffix(backup.suffix + ".json").is_file())


if __name__ == "__main__":
    unittest.main()
