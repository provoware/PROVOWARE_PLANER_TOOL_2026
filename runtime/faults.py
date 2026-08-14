from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

FAULTS = {
    "workspace_missing",
    "config_corrupt",
    "manifest_tampered",
    "missing_permissions",
    "sqlite_locked",
    "sqlite_corrupt",
    "disk_full",
    "optional_module_missing",
}


@dataclass
class RuntimeContext:
    repo_root: Path
    workspace: Path
    faults: set[str] = field(default_factory=set)
    allow_fault_injection: bool = False
    recovery_actions: list[str] = field(default_factory=list)
    gui_handoff: dict = field(default_factory=dict)

    def fault(self, name: str) -> bool:
        return name in self.faults

    @property
    def config_path(self) -> Path:
        return self.workspace / "config.json"

    @property
    def database_path(self) -> Path:
        return self.workspace / "planer.sqlite3"

    @property
    def log_path(self) -> Path:
        return self.workspace / "logs" / "start.log"


def prepare_fault_environment(ctx: RuntimeContext) -> None:
    unknown = ctx.faults - FAULTS
    if unknown:
        raise ValueError(f"Unbekannte Fault-Injection: {sorted(unknown)}")
    if not ctx.faults:
        return
    if not ctx.allow_fault_injection:
        raise PermissionError("START-FAULT-SAFETY-001: Fault-Injection ist nicht freigegeben.")
    workspace = ctx.workspace.resolve()
    temp = Path(tempfile.gettempdir()).resolve()
    if workspace != temp and temp not in workspace.parents:
        raise PermissionError("START-FAULT-SAFETY-001: Fault-Injection ist nur in temporären Test-Workspaces erlaubt.")
    if ctx.fault("workspace_missing") and ctx.workspace.exists():
        shutil.rmtree(ctx.workspace)
    if ctx.fault("config_corrupt"):
        ctx.workspace.mkdir(parents=True, exist_ok=True)
        ctx.config_path.write_text("{ungueltig", encoding="utf-8")
    if ctx.fault("sqlite_corrupt"):
        ctx.workspace.mkdir(parents=True, exist_ok=True)
        ctx.database_path.write_bytes(b"NOT-A-SQLITE-DATABASE")
