from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from enum import StrEnum


class CandidateState(StrEnum):
    QUALIFIED = "QUALIFIED"
    BLOCKED = "BLOCKED"


def _canonical_sha256(payload: dict) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class BackupCandidate:
    backup_path: str
    backup_sha256: str
    backup_size: int
    manifest_path: str
    manifest_sha256: str
    schema_version: int
    quick_check: str
    state: CandidateState
    reason: str

    @property
    def qualified(self) -> bool:
        return self.state is CandidateState.QUALIFIED


@dataclass(frozen=True, slots=True)
class RestorePlan:
    backup_path: str
    backup_sha256: str
    backup_size: int
    manifest_path: str
    manifest_sha256: str
    backup_schema_version: int
    target_path: str
    target_existed: bool
    target_sha256: str
    target_size: int
    prepared_at: str
    plan_sha256: str

    @classmethod
    def create(
        cls,
        *,
        backup_path: str,
        backup_sha256: str,
        backup_size: int,
        manifest_path: str,
        manifest_sha256: str,
        backup_schema_version: int,
        target_path: str,
        target_existed: bool,
        target_sha256: str,
        target_size: int,
        prepared_at: str,
    ) -> "RestorePlan":
        payload = {
            "backup_path": backup_path,
            "backup_sha256": backup_sha256,
            "backup_size": int(backup_size),
            "manifest_path": manifest_path,
            "manifest_sha256": manifest_sha256,
            "backup_schema_version": int(backup_schema_version),
            "target_path": target_path,
            "target_existed": bool(target_existed),
            "target_sha256": target_sha256,
            "target_size": int(target_size),
            "prepared_at": prepared_at,
        }
        return cls(**payload, plan_sha256=_canonical_sha256(payload))

    def payload(self) -> dict:
        data = asdict(self)
        data.pop("plan_sha256")
        return data

    def verify_hash(self) -> bool:
        return _canonical_sha256(self.payload()) == self.plan_sha256
