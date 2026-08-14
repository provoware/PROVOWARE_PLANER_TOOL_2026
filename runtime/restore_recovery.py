from __future__ import annotations

from pathlib import Path

from services.restore_execution_service import RestoreExecutionService
from services.restore_service import RestoreService


def restore_recovery_preflight(workspace: Path) -> list[str]:
    """Schließt einen nach Prozessabbruch offenen Restore vor jeder DB-Schreibprobe."""
    workspace = Path(workspace).resolve()
    database = workspace / "planer.sqlite3"
    service = RestoreExecutionService(
        RestoreService(
            backup_root=workspace / "backups",
            target_database=database,
        )
    )
    state = service.inspect_pending()
    if state["status"] in {"CLEAR", "CLOSED"}:
        # CLOSED räumt ggf. nur noch verwaiste, nachweisbar tote Laufzeitreste auf.
        result = service.recover_pending()
        return [] if result.get("status") in {"CLEAR", "CLOSED"} else [f"restore_{result.get('status','').lower()}"]
    result = service.recover_pending()
    return [f"restore_{result.get('outcome') or result.get('status','recovered').lower()}"]
