from __future__ import annotations

import os

from .errors import InjectedTodoFault

_ALLOWED = {
    "TODO_AFTER_INSERT_BEFORE_COMMIT",
    "TODO_AFTER_UPDATE_BEFORE_COMMIT",
    "TODO_AFTER_SOFT_DELETE_BEFORE_COMMIT",
    "LINK_AFTER_INSERT_BEFORE_COMMIT",
    "LINK_AFTER_UPDATE_BEFORE_COMMIT",
    "LINK_AFTER_SOFT_DELETE_BEFORE_COMMIT",
}


def trigger(name: str) -> None:
    if name not in _ALLOWED:
        raise ValueError(f"Unbekannter Todo-Fault: {name}")
    if os.environ.get("PROVOWARE_FAULT_MODE") == name:
        raise InjectedTodoFault(f"TODO-FAULT-001: simulierter Transaktionsabbruch {name}")
