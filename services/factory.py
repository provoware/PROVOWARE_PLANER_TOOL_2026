from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from services.calendar_service import CalendarService
from services.history_service import SyncJournalService
from services.sync_preview_service import SynchronizationPreviewService
from services.sync_service import SynchronizationService
from services.todo_service import TodoCalendarLinkService, TodoService
from storage.database import Database
from storage.history_repository import SyncHistoryRepository
from storage.migrations import MigrationRunner
from storage.repository import CalendarRepository
from storage.sync_repository import SyncRepository
from storage.todo_repository import TodoRepository

ROOT = Path(__file__).resolve().parents[1]


def _prepare_database(
    database_path: Path,
    *,
    migrations_dir: Path | None = None,
    backup_dir: Path | None = None,
) -> Database:
    database = Database(Path(database_path))
    runner = MigrationRunner(database, migrations_dir or ROOT / "migrations", backup_dir=backup_dir)
    runner.apply_all()
    runner.verify_history()
    database.quick_check()
    return database


def open_calendar_service(
    database_path: Path,
    *,
    migrations_dir: Path | None = None,
    backup_dir: Path | None = None,
) -> CalendarService:
    database = _prepare_database(database_path, migrations_dir=migrations_dir, backup_dir=backup_dir)
    return CalendarService(CalendarRepository(database))


@dataclass(frozen=True, slots=True)
class PlannerServices:
    database: Database
    calendar: CalendarService
    todos: TodoService
    links: TodoCalendarLinkService
    sync_preview: SynchronizationPreviewService
    sync: SynchronizationService
    journal: SyncJournalService


def open_planner_services(
    database_path: Path,
    *,
    migrations_dir: Path | None = None,
    backup_dir: Path | None = None,
) -> PlannerServices:
    database = _prepare_database(database_path, migrations_dir=migrations_dir, backup_dir=backup_dir)
    calendar_repository = CalendarRepository(database)
    todo_repository = TodoRepository(database)
    sync_repository = SyncRepository(database)
    history_repository = SyncHistoryRepository(database)
    calendar = CalendarService(calendar_repository)
    todos = TodoService(todo_repository)
    links = TodoCalendarLinkService(todo_repository, calendar_repository)
    sync = SynchronizationService(sync_repository)
    return PlannerServices(
        database=database,
        calendar=calendar,
        todos=todos,
        links=links,
        sync_preview=SynchronizationPreviewService(todos, calendar, links),
        sync=sync,
        journal=SyncJournalService(sync, sync_repository, history_repository),
    )
