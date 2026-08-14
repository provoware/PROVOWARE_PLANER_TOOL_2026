from __future__ import annotations

import dataclasses
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from services.factory import open_planner_services
from services.restore_execution_service import RestoreExecutionService, logical_database_sha256
from services.restore_service import RestoreService
from storage.backup import create_backup
from storage.restore_guard import lease_owner_alive, lease_path, read_intent, snapshot_path


ROOT = Path(__file__).resolve().parents[1]


class I016RestoreCrashRecoveryTest(unittest.TestCase):
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
        connection = sqlite3.connect(self.target)
        try:
            connection.execute("CREATE TABLE state_after_backup(id INTEGER PRIMARY KEY, value TEXT)")
            connection.execute("INSERT INTO state_after_backup(value) VALUES ('neu')")
            connection.commit()
        finally:
            connection.close()
        self.restore = RestoreService(backup_root=self.backups, target_database=self.target)
        self.plan = self.restore.prepare_restore(self.backup)
        self.plan_file = self.root / "plan.json"
        self.plan_file.write_text(json.dumps(dataclasses.asdict(self.plan)), encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _crash(self, point: str, code: int) -> subprocess.CompletedProcess[str]:
        script = r'''
import json, os, sys
from pathlib import Path
from backup_core.model import RestorePlan
from services.restore_execution_service import RestoreExecutionService
from services.restore_service import RestoreService
plan = RestorePlan(**json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
point = sys.argv[4]
code = int(sys.argv[5])
def fault(name):
    if name == point:
        os._exit(code)
service = RestoreExecutionService(RestoreService(backup_root=Path(sys.argv[2]), target_database=Path(sys.argv[3]), fault_hook=fault))
service.execute(plan)
'''
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.run(
            [sys.executable, "-c", script, str(self.plan_file), str(self.backups), str(self.target), point, str(code)],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_process_exit_after_atomic_replace_is_finalized_on_restart(self) -> None:
        expected = logical_database_sha256(self.backup)
        process = self._crash("after_replace_before_postcheck", 92)
        self.assertEqual(process.returncode, 92, process.stderr)
        intent = read_intent(self.target)
        self.assertIsNotNone(intent)
        assert intent is not None
        self.assertEqual(intent.state.value, "COMMITTING")
        self.assertTrue(lease_path(self.target).exists())
        self.assertFalse(lease_owner_alive(self.target))
        self.assertTrue(snapshot_path(self.target).exists())
        self.assertEqual(logical_database_sha256(self.target), expected)

        result = RestoreExecutionService(
            RestoreService(backup_root=self.backups, target_database=self.target)
        ).recover_pending()
        self.assertEqual(result["status"], "RECOVERED")
        self.assertEqual(result["outcome"], "RECOVERED_COMMIT")
        self.assertEqual(logical_database_sha256(self.target), expected)
        self.assertFalse(lease_path(self.target).exists())
        self.assertFalse(snapshot_path(self.target).exists())
        self.assertFalse(self.target.with_suffix(self.target.suffix + ".pre-restore").exists())

    def test_process_exit_before_physical_write_recovers_no_change(self) -> None:
        before = logical_database_sha256(self.target)
        process = self._crash("precheck_begin", 93)
        self.assertEqual(process.returncode, 93, process.stderr)
        intent = read_intent(self.target)
        self.assertIsNotNone(intent)
        assert intent is not None
        self.assertEqual(intent.state.value, "COMMITTING")
        self.assertEqual(logical_database_sha256(self.target), before)

        result = RestoreExecutionService(
            RestoreService(backup_root=self.backups, target_database=self.target)
        ).recover_pending()
        self.assertEqual(result["outcome"], "RECOVERED_NO_CHANGE")
        self.assertEqual(logical_database_sha256(self.target), before)
        self.assertFalse(lease_path(self.target).exists())
        self.assertFalse(snapshot_path(self.target).exists())


if __name__ == "__main__":
    unittest.main()
