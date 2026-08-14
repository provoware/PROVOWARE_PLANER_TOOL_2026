from __future__ import annotations

import os

from .errors import InjectedSyncFault

_ALLOWED = {
    "SYNC_AFTER_ENTITY_WRITE",
    "SYNC_AFTER_BASELINE_WRITE",
    "SYNC_BEFORE_RECEIPT",
    "SYNC_AFTER_RECEIPT_BEFORE_COMMIT",
}


def trigger(name: str) -> None:
    if name not in _ALLOWED:
        raise ValueError(f"Unbekannter Sync-Fault: {name}")
    if os.environ.get("PROVOWARE_SYNC_FAULTS") != "1":
        return
    if os.environ.get("PROVOWARE_SYNC_CRASH_MODE") == name:
        os._exit(92)
    if os.environ.get("PROVOWARE_SYNC_FAULT_MODE") == name:
        raise InjectedSyncFault(f"SYNC-FAULT-001: simulierter Transaktionsabbruch {name}")
