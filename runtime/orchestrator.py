from __future__ import annotations

from datetime import datetime, timezone

from .checks import CHECKS, p
from .faults import RuntimeContext, prepare_fault_environment
from .model import Phase, PhaseStatus, RuntimeReport, RuntimeState, StepResult


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class StartOrchestrator:
    def __init__(self, ctx: RuntimeContext) -> None:
        self.ctx = ctx
        self.state = RuntimeState.INIT
        self.history = [RuntimeState.INIT]
        self.results: list[StepResult] = []
        self.degraded = False

    def _state(self, value: RuntimeState) -> None:
        if self.state != value:
            self.state = value
            self.history.append(value)

    def run(self) -> RuntimeReport:
        started = utc_now()
        try:
            prepare_fault_environment(self.ctx)
        except Exception as exc:
            self._state(RuntimeState.BLOCKED)
            self.results.append(StepResult("fault_safety", "Fault-Injection-Sicherheit", [
                p(Phase.PRECHECK, PhaseStatus.BLOCKED, "START-FAULT-SAFETY-001",
                  "Fault-Injection wurde aus Sicherheitsgründen blockiert.", repr(exc),
                  "KEINE TESTMANIPULATION AUSFÜHREN")
            ]))
            return self._report(started)

        self._state(RuntimeState.CHECKING)
        for check in CHECKS:
            result = check(self.ctx)
            self.results.append(result)
            status = result.final_status
            if status == PhaseStatus.BLOCKED:
                self._state(RuntimeState.BLOCKED)
                break
            if status == PhaseStatus.RECOVERY_REQUIRED:
                self._state(RuntimeState.RECOVERY_REQUIRED)
                break
            if status == PhaseStatus.DEGRADED:
                self.degraded = True
            if status == PhaseStatus.RECOVERED:
                self._state(RuntimeState.RECOVERY_REQUIRED)
                self._state(RuntimeState.CHECKING)

        if self.state == RuntimeState.CHECKING:
            self._state(RuntimeState.DEGRADED if self.degraded else RuntimeState.READY)
        return self._report(started)

    def _report(self, started: str) -> RuntimeReport:
        messages = {
            RuntimeState.READY: "Startprüfung erfolgreich. Das Programm kann gestartet werden.",
            RuntimeState.DEGRADED: "Start möglich, aber mindestens eine nichtkritische Funktion ist eingeschränkt.",
            RuntimeState.RECOVERY_REQUIRED: "Start angehalten. Eine sichere Wiederherstellung ist erforderlich.",
            RuntimeState.BLOCKED: "Start blockiert. Ein sicherheits- oder integritätsrelevantes Problem wurde erkannt.",
            RuntimeState.INIT: "Startprüfung wurde noch nicht ausgeführt.",
            RuntimeState.CHECKING: "Startprüfung läuft.",
        }
        return RuntimeReport(
            state=self.state,
            state_history=self.history,
            workspace=str(self.ctx.workspace),
            steps=self.results,
            faults=sorted(self.ctx.faults),
            recovery_actions=list(self.ctx.recovery_actions),
            started_at_utc=started,
            finished_at_utc=utc_now(),
            user_summary=messages[self.state],
        )
