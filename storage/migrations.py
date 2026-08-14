from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from calendar_core.errors import MigrationError, MigrationTamperedError
from storage.database import Database


class MigrationRunner:
    def __init__(self, database: Database, migrations_dir: Path) -> None:
        self.database = database
        self.migrations_dir = Path(migrations_dir)

    @staticmethod
    def _hash(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    @staticmethod
    def _version(path: Path) -> int:
        prefix = path.name.split("_", 1)[0]
        if not prefix.isdigit():
            raise MigrationError(f"CAL-MIGRATION-001: ungültiger Migrationsname {path.name}")
        return int(prefix)

    def _files(self) -> list[Path]:
        files = sorted(self.migrations_dir.glob("*.sql"))
        versions = [self._version(path) for path in files]
        if versions != sorted(set(versions)):
            raise MigrationError("CAL-MIGRATION-001: Migrationsversionen sind nicht eindeutig")
        return files

    def apply_all(self) -> list[int]:
        applied_now: list[int] = []
        connection = self.database.connect()
        try:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    applied_at TEXT NOT NULL
                )
                """
            )
            connection.commit()
            applied = {
                int(row["version"]): row["sha256"]
                for row in connection.execute("SELECT version, sha256 FROM schema_migrations")
            }
            for path in self._files():
                version = self._version(path)
                digest = self._hash(path)
                if version in applied:
                    if applied[version] != digest:
                        raise MigrationTamperedError(
                            f"CAL-MIGRATION-HASH-001: angewandte Migration {version} wurde verändert"
                        )
                    continue
                try:
                    connection.execute("BEGIN IMMEDIATE")
                    connection.executescript(path.read_text(encoding="utf-8"))
                    connection.execute(
                        "INSERT INTO schema_migrations(version, name, sha256, applied_at) VALUES (?, ?, ?, ?)",
                        (version, path.name, digest, datetime.now(timezone.utc).isoformat()),
                    )
                    connection.commit()
                    applied_now.append(version)
                except Exception as exc:
                    connection.rollback()
                    if isinstance(exc, MigrationError):
                        raise
                    raise MigrationError(
                        f"CAL-MIGRATION-001: Migration {path.name} fehlgeschlagen"
                    ) from exc
        finally:
            connection.close()
        self.database.quick_check()
        return applied_now

    def verify_history(self) -> None:
        connection = self.database.connect()
        try:
            rows = {
                int(row["version"]): row["sha256"]
                for row in connection.execute("SELECT version, sha256 FROM schema_migrations")
            }
        finally:
            connection.close()
        files = {self._version(path): self._hash(path) for path in self._files()}
        for version, digest in rows.items():
            if files.get(version) != digest:
                raise MigrationTamperedError(
                    f"CAL-MIGRATION-HASH-001: Historie für Migration {version} ist nicht reproduzierbar"
                )
