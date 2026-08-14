from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from calendar_core.errors import DatabaseBusyError, DatabaseIntegrityError
from storage.restore_guard import assert_restore_write_allowed


class Database:
    def __init__(self, path: Path, *, busy_timeout_ms: int = 1500) -> None:
        self.path = Path(path)
        self.busy_timeout_ms = busy_timeout_ms
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        try:
            connection = sqlite3.connect(self.path, timeout=self.busy_timeout_ms / 1000)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(f"PRAGMA busy_timeout = {int(self.busy_timeout_ms)}")
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA synchronous = FULL")
            return connection
        except sqlite3.OperationalError as exc:
            if "locked" in str(exc).lower() or "busy" in str(exc).lower():
                raise DatabaseBusyError("CAL-DB-LOCK-001: Datenbank ist belegt") from exc
            raise

    @contextmanager
    def session(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            yield connection
        finally:
            connection.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        # I016: Neue Planner-Schreibtransaktionen dürfen eine aktive Restore-Lease
        # niemals überholen. Leser bleiben erlaubt; der Restore prüft zusätzlich mit
        # BEGIN IMMEDIATE, dass bereits laufende Schreiber beendet sind.
        assert_restore_write_allowed(self.path)
        connection = self.connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except sqlite3.OperationalError as exc:
            connection.rollback()
            if "locked" in str(exc).lower() or "busy" in str(exc).lower():
                raise DatabaseBusyError("CAL-DB-LOCK-001: Transaktion konnte nicht gestartet werden") from exc
            raise
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def quick_check(self) -> None:
        try:
            with self.session() as connection:
                result = connection.execute("PRAGMA quick_check").fetchone()[0]
        except sqlite3.DatabaseError as exc:
            raise DatabaseIntegrityError("CAL-DB-INTEGRITY-001: SQLite-Datei kann nicht geprüft werden") from exc
        if result != "ok":
            raise DatabaseIntegrityError(f"CAL-DB-INTEGRITY-001: quick_check={result}")

    def schema_version(self) -> int:
        with self.session() as connection:
            row = connection.execute(
                "SELECT COALESCE(MAX(version), 0) FROM schema_migrations"
            ).fetchone()
            return int(row[0])
