from __future__ import annotations

import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path

from services.factory import open_planner_services
from services.restore_service import RestoreService
from storage.backup import create_backup


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class I015RestoreFaultTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.workspace = self.root / "workspace"
        self.backups = self.workspace / "Sicherungen"
        self.backups.mkdir(parents=True)
        self.target = self.workspace / "planer.sqlite3"
        services = open_planner_services(self.target, backup_dir=self.backups / "migrationen")
        self.backup = self.backups / "stand.sqlite3"
        create_backup(services.database, self.backup)
        connection = sqlite3.connect(self.target)
        try:
            connection.execute("CREATE TABLE newer_target_state(id INTEGER PRIMARY KEY, value TEXT)")
            connection.execute("INSERT INTO newer_target_state(value) VALUES ('vorher')")
            connection.commit()
        finally:
            connection.close()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_exception_after_replace_rolls_back_old_target(self) -> None:
        before = sha256(self.target)

        def fault(point: str) -> None:
            if point == "after_replace_before_postcheck":
                raise RuntimeError("I015 injected postcheck fault")

        service = RestoreService(backup_root=self.backups, target_database=self.target, fault_hook=fault)
        plan = service.prepare_restore(self.backup)
        with self.assertRaisesRegex(RuntimeError, "injected postcheck fault"):
            service.commit_restore(plan)
        self.assertEqual(sha256(self.target), before)
        connection = sqlite3.connect(self.target)
        try:
            row = connection.execute("SELECT value FROM newer_target_state").fetchone()
            quick = connection.execute("PRAGMA quick_check").fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(row[0], "vorher")
        self.assertEqual(quick, "ok")

    def test_fault_in_physical_precheck_writes_nothing(self) -> None:
        before = sha256(self.target)

        def fault(point: str) -> None:
            if point == "physical_core_precheck":
                raise RuntimeError("I015 injected precheck fault")

        service = RestoreService(backup_root=self.backups, target_database=self.target, fault_hook=fault)
        plan = service.prepare_restore(self.backup)
        with self.assertRaisesRegex(RuntimeError, "injected precheck fault"):
            service.commit_restore(plan)
        self.assertEqual(sha256(self.target), before)
        self.assertFalse(self.target.with_suffix(self.target.suffix + ".pre-restore").exists())
        self.assertFalse(self.target.with_suffix(self.target.suffix + ".restore-candidate").exists())


if __name__ == "__main__":
    unittest.main()
