from __future__ import annotations

from pathlib import Path

from services.calendar_service import CalendarService
from storage.database import Database
from storage.migrations import MigrationRunner
from storage.repository import CalendarRepository

ROOT = Path(__file__).resolve().parents[1]


def open_calendar_service(
    database_path: Path,
    *,
    migrations_dir: Path | None = None,
    backup_dir: Path | None = None,
) -> CalendarService:
    database = Database(Path(database_path))
    runner = MigrationRunner(
        database,
        migrations_dir or ROOT / "migrations",
        backup_dir=backup_dir,
    )
    runner.apply_all()
    runner.verify_history()
    database.quick_check()
    return CalendarService(CalendarRepository(database))
