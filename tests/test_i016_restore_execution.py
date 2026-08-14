from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from calendar_core.errors import RestoreRejectedError
from services.factory import open_planner_services
from services.restore_execution_service import RestoreExecutionService, logical_database_sha256
from services.restore_service import RestoreService
from storage.backup import create_backup
from storage.restore_guard import (
    acquire_restore_lease,
    intent_path,
    lease_path,
    read_intent,
    release_restore_lease,
    snapshot_path,
)


class I016RestoreExecutionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.workspace = self.root / "workspace"
        self.backups = self.workspace / "backups"
        self.backups.mkdir(parents=True)
        self.target = self.workspace / "planer.sqlite3"
        self.services = open_planner_services(self.target, backup_dir=self.backups / "migrationen")
        self.backup = self.backups / "stand.sqlite3"
        create_backup(self.services.database, self.backup)
        self.restore = RestoreService(backup_root=self.backups, target_database=self.target)
        self.execution = RestoreExecutionService(self.restore)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _mutate(self, table: str) -> None:
        connection = sqlite3.connect(self.target)
        try:
            connection.execute(f"CREATE TABLE {table}(id INTEGER PRIMARY KEY, value TEXT)")
            connection.execute(f"INSERT INTO {table}(value) VALUES ('neu')")
            connection.commit()
        finally:
            connection.close()

    def test_execute_closes_intent_and_releases_runtime_residue(self) -> None:
        backup_logical = logical_database_sha256(self.backup)
        self._mutate("newer_state")
        plan = self.restore.prepare_restore(self.backup)
        result = self.execution.execute(plan)
        self.assertEqual(result["execution_status"], "CLOSED")
        self.assertEqual(logical_database_sha256(self.target), backup_logical)
        intent = read_intent(self.target)
        self.assertIsNotNone(intent)
        assert intent is not None
        self.assertEqual(intent.state.value, "CLOSED")
        self.assertEqual(intent.outcome, "RESTORE_OK")
        self.assertTrue(intent.verify_hash())
        self.assertFalse(lease_path(self.target).exists())
        self.assertFalse(snapshot_path(self.target).exists())

    def test_active_lease_blocks_normal_database_transaction(self) -> None:
        lease = acquire_restore_lease(self.target, plan_sha256="test-plan")
        try:
            with self.assertRaisesRegex(RestoreRejectedError, "RESTORE-LEASE-001"):
                with self.services.database.transaction():
                    pass
        finally:
            release_restore_lease(self.target, str(lease["lease_id"]))

    def test_parallel_restore_lease_is_blocked(self) -> None:
        plan = self.restore.prepare_restore(self.backup)
        lease = acquire_restore_lease(self.target, plan_sha256="other-plan")
        try:
            with self.assertRaisesRegex(RestoreRejectedError, "RESTORE-LEASE-001"):
                self.execution.execute(plan)
        finally:
            release_restore_lease(self.target, str(lease["lease_id"]))

    def test_tampered_intent_blocks_recovery(self) -> None:
        self._mutate("newer_state")
        plan = self.restore.prepare_restore(self.backup)

        def fail_after_replace(point: str) -> None:
            if point == "after_replace_before_postcheck":
                raise RuntimeError("simulierter Fehler")

        failing = RestoreExecutionService(
            RestoreService(backup_root=self.backups, target_database=self.target, fault_hook=fail_after_replace)
        )
        with self.assertRaises(RuntimeError):
            failing.execute(plan)
        # Exception-Recovery schließt sauber; wir manipulieren anschließend den Receipt,
        # um die fail-closed Hashprüfung isoliert nachzuweisen.
        path = intent_path(self.target)
        data = json.loads(path.read_text(encoding="utf-8"))
        data["outcome"] = "MANIPULIERT"
        path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(RestoreRejectedError, "RESTORE-INTENT-HASH-001"):
            self.execution.inspect_pending()

    def test_exception_after_replace_returns_to_exact_logical_prestate(self) -> None:
        self._mutate("newer_state")
        before = logical_database_sha256(self.target)
        plan = self.restore.prepare_restore(self.backup)

        def fail_after_replace(point: str) -> None:
            if point == "after_replace_before_postcheck":
                raise RuntimeError("post-replace-fault")

        failing = RestoreExecutionService(
            RestoreService(backup_root=self.backups, target_database=self.target, fault_hook=fail_after_replace)
        )
        with self.assertRaises(RuntimeError):
            failing.execute(plan)
        self.assertEqual(logical_database_sha256(self.target), before)
        intent = read_intent(self.target)
        self.assertIsNotNone(intent)
        assert intent is not None
        self.assertEqual(intent.state.value, "CLOSED")
        self.assertEqual(intent.outcome, "ROLLBACK_OK")
        self.assertFalse(lease_path(self.target).exists())
        self.assertFalse(snapshot_path(self.target).exists())


if __name__ == "__main__":
    unittest.main()
