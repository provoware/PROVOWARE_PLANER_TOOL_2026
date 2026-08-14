from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMainWindow

from services.factory import PlannerServices
from ui.todo_window import TodoWindow


def attach_todo_module(
    calendar_window: QMainWindow,
    services: PlannerServices,
    *,
    repo_root: Path,
    workspace: Path,
    timezone_name: str,
) -> QAction:
    menu = calendar_window.menuBar().addMenu("Module")
    action = QAction("Aufgaben öffnen", calendar_window)
    action.setShortcut(QKeySequence("Ctrl+Shift+T"))
    action.setToolTip("Öffnet die Aufgabenverwaltung. Konflikte werden nur angezeigt, nicht automatisch aufgelöst.")

    def open_todos() -> None:
        existing = getattr(calendar_window, "_provoware_todo_window", None)
        if existing is None:
            existing = TodoWindow(
                services.todos,
                services.links,
                services.calendar,
                repo_root=repo_root,
                workspace=workspace,
                timezone_name=timezone_name,
            )
            setattr(calendar_window, "_provoware_todo_window", existing)
        existing.show()
        existing.raise_()
        existing.activateWindow()

    action.triggered.connect(open_todos)
    menu.addAction(action)
    calendar_window.addAction(action)
    return action
