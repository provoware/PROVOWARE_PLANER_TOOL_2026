from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, replace
from enum import StrEnum


class RestoreIntentState(StrEnum):
    PREPARED = "PREPARED"
    COMMITTING = "COMMITTING"
    VERIFIED = "VERIFIED"
    CLOSED = "CLOSED"


def _canonical_sha256(payload: dict) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True, slots=True)
class RestoreIntent:
    schema_version: int
    intent_id: str
    revision: int
    previous_intent_sha256: str
    state: RestoreIntentState
    plan_sha256: str
    backup_path: str
    backup_sha256: str
    target_path: str
    target_existed_before: bool
    target_state_sha256_before: str
    target_logical_sha256_before: str
    expected_restored_logical_sha256: str
    snapshot_path: str
    snapshot_sha256: str
    lease_id: str
    created_at: str
    updated_at: str
    outcome: str
    intent_sha256: str

    def _unsigned(self) -> dict:
        payload = asdict(self)
        payload["state"] = self.state.value
        payload.pop("intent_sha256", None)
        return payload

    def verify_hash(self) -> bool:
        return self.intent_sha256 == _canonical_sha256(self._unsigned())

    def to_dict(self) -> dict:
        payload = self._unsigned()
        payload["intent_sha256"] = self.intent_sha256
        return payload

    @classmethod
    def create(
        cls,
        *,
        intent_id: str,
        plan_sha256: str,
        backup_path: str,
        backup_sha256: str,
        target_path: str,
        target_existed_before: bool,
        target_state_sha256_before: str,
        target_logical_sha256_before: str,
        expected_restored_logical_sha256: str,
        snapshot_path: str,
        snapshot_sha256: str,
        lease_id: str,
        timestamp: str,
    ) -> "RestoreIntent":
        value = cls(
            schema_version=1,
            intent_id=intent_id,
            revision=1,
            previous_intent_sha256="",
            state=RestoreIntentState.PREPARED,
            plan_sha256=plan_sha256,
            backup_path=backup_path,
            backup_sha256=backup_sha256,
            target_path=target_path,
            target_existed_before=target_existed_before,
            target_state_sha256_before=target_state_sha256_before,
            target_logical_sha256_before=target_logical_sha256_before,
            expected_restored_logical_sha256=expected_restored_logical_sha256,
            snapshot_path=snapshot_path,
            snapshot_sha256=snapshot_sha256,
            lease_id=lease_id,
            created_at=timestamp,
            updated_at=timestamp,
            outcome="",
            intent_sha256="",
        )
        return replace(value, intent_sha256=_canonical_sha256(value._unsigned()))

    def transition(self, state: RestoreIntentState, *, timestamp: str, outcome: str = "") -> "RestoreIntent":
        allowed = {
            RestoreIntentState.PREPARED: {RestoreIntentState.COMMITTING, RestoreIntentState.CLOSED},
            RestoreIntentState.COMMITTING: {RestoreIntentState.VERIFIED, RestoreIntentState.CLOSED},
            RestoreIntentState.VERIFIED: {RestoreIntentState.CLOSED},
            RestoreIntentState.CLOSED: set(),
        }
        if state not in allowed[self.state]:
            raise ValueError(f"RESTORE-INTENT-STATE-001: Übergang {self.state.value} -> {state.value} ist nicht erlaubt")
        value = replace(
            self,
            revision=self.revision + 1,
            previous_intent_sha256=self.intent_sha256,
            state=state,
            updated_at=timestamp,
            outcome=outcome,
            intent_sha256="",
        )
        return replace(value, intent_sha256=_canonical_sha256(value._unsigned()))

    @classmethod
    def from_dict(cls, payload: dict) -> "RestoreIntent":
        value = cls(
            schema_version=int(payload["schema_version"]),
            intent_id=str(payload["intent_id"]),
            revision=int(payload["revision"]),
            previous_intent_sha256=str(payload.get("previous_intent_sha256", "")),
            state=RestoreIntentState(payload["state"]),
            plan_sha256=str(payload["plan_sha256"]),
            backup_path=str(payload["backup_path"]),
            backup_sha256=str(payload["backup_sha256"]),
            target_path=str(payload["target_path"]),
            target_existed_before=bool(payload["target_existed_before"]),
            target_state_sha256_before=str(payload["target_state_sha256_before"]),
            target_logical_sha256_before=str(payload["target_logical_sha256_before"]),
            expected_restored_logical_sha256=str(payload["expected_restored_logical_sha256"]),
            snapshot_path=str(payload["snapshot_path"]),
            snapshot_sha256=str(payload["snapshot_sha256"]),
            lease_id=str(payload["lease_id"]),
            created_at=str(payload["created_at"]),
            updated_at=str(payload["updated_at"]),
            outcome=str(payload.get("outcome", "")),
            intent_sha256=str(payload["intent_sha256"]),
        )
        if value.schema_version != 1 or not value.verify_hash():
            raise ValueError("RESTORE-INTENT-HASH-001: Restore-Intent ist verändert oder ungültig")
        return value
