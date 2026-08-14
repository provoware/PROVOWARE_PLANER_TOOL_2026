from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class RuntimeState(str, Enum):
    INIT = "INIT"
    CHECKING = "CHECKING"
    READY = "READY"
    DEGRADED = "DEGRADED"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"
    BLOCKED = "BLOCKED"


class Phase(str, Enum):
    PRECHECK = "PRECHECK"
    ACTION = "ACTION"
    POSTCHECK = "POSTCHECK"


class PhaseStatus(str, Enum):
    PASS = "PASS"
    INFO = "INFO"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    RECOVERED = "RECOVERED"
    DEGRADED = "DEGRADED"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"


@dataclass(frozen=True)
class PhaseResult:
    phase: Phase
    status: PhaseStatus
    code: str
    user_message: str
    technical_details: str = ""
    automatic_action: str = "KEINE"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["phase"] = self.phase.value
        data["status"] = self.status.value
        return data


@dataclass
class StepResult:
    step_id: str
    title: str
    phases: list[PhaseResult] = field(default_factory=list)

    @property
    def final_status(self) -> PhaseStatus:
        priority = {
            PhaseStatus.BLOCKED: 7,
            PhaseStatus.RECOVERY_REQUIRED: 6,
            PhaseStatus.DEGRADED: 5,
            PhaseStatus.RECOVERED: 4,
            PhaseStatus.ACTION_REQUIRED: 3,
            PhaseStatus.PASS: 2,
            PhaseStatus.INFO: 1,
            PhaseStatus.SKIPPED: 0,
        }
        return max((p.status for p in self.phases), key=priority.__getitem__, default=PhaseStatus.INFO)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "title": self.title,
            "final_status": self.final_status.value,
            "phases": [phase.to_dict() for phase in self.phases],
        }


@dataclass
class RuntimeReport:
    state: RuntimeState
    state_history: list[RuntimeState]
    workspace: str
    steps: list[StepResult]
    faults: list[str]
    recovery_actions: list[str]
    started_at_utc: str
    finished_at_utc: str
    user_summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "state": self.state.value,
            "state_history": [s.value for s in self.state_history],
            "workspace": self.workspace,
            "faults": self.faults,
            "recovery_actions": self.recovery_actions,
            "started_at_utc": self.started_at_utc,
            "finished_at_utc": self.finished_at_utc,
            "user_summary": self.user_summary,
            "steps": [step.to_dict() for step in self.steps],
        }
