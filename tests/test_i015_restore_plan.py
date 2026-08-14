from __future__ import annotations

import json
import shutil
import sqlite3
import tempfile
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

from backup_core.model import CandidateState
from calendar_core.errors import RestoreRejectedError
from services.factory import open_planner_services
from services.restore_service import RestoreService
from storage.backup import create_backup


class I015RestorePlanTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.workspace = self.root / "workspace"
        self.backups = self.workspace / "Sicherungen"
        self.backups.mkdir(parents=True)
        self.target = self.workspace / "planer.sqlite3"
        self.services = open_planner_services(self.target, backup_dir=self.backups / "migrationen")
        self.backup = self.backups / "stand.sqlite3"
        create_backup(self.services.database, self.backup)
        self.restore = RestoreService(backup_root=self.backups, target_database=self.target)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _mutate_target(self, name: str) -> None:
        connection = sqlite3.connect(self.target)
        try:
            connection.execute(f"CREATE TABLE {name}(id INTEGER PRIMARY KEY, value TEXT)")
            connection.execute(f"INSERT INTO {name}(value) VALUES ('x')")
            connection.commit()
        finally:
            connection.close()

    def test_candidate_qualification_is_read_only_and_complete(self) -> None:
        manifest = self.backup.with_suffix(self.backup.suffix + ".json")
        before = (self.backup.stat().st_mtime_ns, manifest.stat().st_mtime_ns)
        candidate = self.restore.qualify_candidate(self.backup)
        after = (self.backup.stat().st_mtime_ns, manifest.stat().st_mtime_ns)
        self.assertEqual(candidate.state, CandidateState.QUALIFIED)
        self.assertEqual(candidate.quick_check, "ok")
        self.assertEqual(candidate.schema_version, 4)
        self.assertEqual(before, after)

    def test_candidate_outside_backup_boundary_is_blocked(self) -> None:
        external = self.root / "external.sqlite3"
        shutil.copy2(self.backup, external)
        shutil.copy2(self.backup.with_suffix(self.backup.suffix + ".json"), external.with_suffix(external.suffix + ".json"))
        result = self.restore.qualify_candidate(external)
        self.assertEqual(result.state, CandidateState.BLOCKED)
        self.assertIn("RESTORE-BOUNDARY-001", result.reason)

    def test_manifest_hash_or_size_tamper_is_blocked(self) -> None:
        manifest = self.backup.with_suffix(self.backup.suffix + ".json")
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data["database_sha256"] = "0" * 64
        manifest.write_text(json.dumps(data), encoding="utf-8")
        result = self.restore.qualify_candidate(self.backup)
        self.assertEqual(result.state, CandidateState.BLOCKED)
        self.assertIn("RESTORE-CANDIDATE-HASH-001", result.reason)

    def test_malformed_manifest_fields_are_blocked_without_crash(self) -> None:
        manifest = self.backup.with_suffix(self.backup.suffix + ".json")
        valid = json.loads(manifest.read_text(encoding="utf-8"))
        invalid_documents = (
            [valid],
            {**valid, "schema_version": 2},
            {**valid, "created_at": "2026-01-01T12:00:00"},
            {**valid, "created_at": "kein-zeitpunkt"},
            {**valid, "size": None},
            {**valid, "size": "not-a-number"},
            {**valid, "source": ""},
        )

        for document in invalid_documents:
            with self.subTest(document=document):
                manifest.write_text(json.dumps(document), encoding="utf-8")
                result = self.restore.qualify_candidate(self.backup)
                self.assertEqual(result.state, CandidateState.BLOCKED)
                self.assertIn("RESTORE-CANDIDATE-003", result.reason)

    def test_restore_plan_is_frozen_and_hash_bound(self) -> None:
        plan = self.restore.prepare_restore(self.backup)
        self.assertTrue(plan.verify_hash())
        with self.assertRaises(FrozenInstanceError):
            plan.target_sha256 = "x"  # type: ignore[misc]
        tampered = replace(plan, target_sha256="0" * 64)
        self.assertFalse(tampered.verify_hash())
        with self.assertRaisesRegex(RestoreRejectedError, "RESTORE-PLAN-HASH-001"):
            self.restore.commit_restore(tampered)

    def test_manifest_changed_after_plan_is_rejected(self) -> None:
        plan = self.restore.prepare_restore(self.backup)
        manifest = self.backup.with_suffix(self.backup.suffix + ".json")
        manifest.write_text(manifest.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        with self.assertRaisesRegex(RestoreRejectedError, "RESTORE-PLAN-STALE-001"):
            self.restore.commit_restore(plan)

    def test_target_wal_or_main_change_after_plan_is_rejected(self) -> None:
        plan = self.restore.prepare_restore(self.backup)
        self._mutate_target("stale_after_plan")
        with self.assertRaisesRegex(RestoreRejectedError, "RESTORE-STALE-001"):
            self.restore.commit_restore(plan)

    def test_successful_restore_removes_newer_target_state(self) -> None:
        self._mutate_target("target_only")
        plan = self.restore.prepare_restore(self.backup)
        result = self.restore.commit_restore(plan)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["schema_version"], 4)
        connection = sqlite3.connect(self.target)
        try:
            exists = connection.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='target_only'").fetchone()[0]
            quick = connection.execute("PRAGMA quick_check").fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(exists, 0)
        self.assertEqual(quick, "ok")
        self.assertFalse(self.target.with_suffix(self.target.suffix + ".pre-restore").exists())
        self.assertFalse(self.target.with_suffix(self.target.suffix + ".restore-candidate").exists())


if __name__ == "__main__":
    unittest.main()
