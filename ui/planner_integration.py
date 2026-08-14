from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMainWindow

from services.factory import PlannerServices
from services.resolution_service import ResolutionService
from ui.sync_control_window import SyncControlWindow
from ui.sync_history_window import SyncHistoryWindow
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
    action.setToolTip("Öffnet die Aufgabenverwaltung. Konflikte bleiben sichtbar und werden nicht still aufgelöst.")

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

    sync_action = QAction("Synchronisation prüfen", calendar_window)
    sync_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
    sync_action.setToolTip(
        "Zeigt Feld-Baselines, Hashstatus und Konflikte. BOTH_DIFFERENT wird nur nach ausdrücklicher Feldentscheidung freigegeben."
    )

    def open_sync_control() -> None:
        existing = getattr(calendar_window, "_provoware_sync_control_window", None)
        if existing is None:
            resolver = ResolutionService(services.sync, services.sync.repository)
            existing = SyncControlWindow(services.sync, resolver, repo_root=repo_root)
            setattr(calendar_window, "_provoware_sync_control_window", existing)
        existing.refresh_links()
        existing.show()
        existing.raise_()
        existing.activateWindow()

    sync_action.triggered.connect(open_sync_control)
    menu.addAction(sync_action)
    calendar_window.addAction(sync_action)
    setattr(calendar_window, "_provoware_sync_control_action", sync_action)

    history_action = QAction("Synchronisationsjournal öffnen", calendar_window)
    history_action.setShortcut(QKeySequence("Ctrl+Shift+H"))
    history_action.setToolTip(
        "Zeigt unveränderliche Sync-/Resolution-Receipts mit Vorher-/Nachher-Nachweisen. "
        "Alte Entscheidungen werden niemals still erneut ausgeführt."
    )

    def open_sync_history() -> None:
        existing = getattr(calendar_window, "_provoware_sync_history_window", None)
        if existing is None:
            existing = SyncHistoryWindow(services.journal, repo_root=repo_root)
            setattr(calendar_window, "_provoware_sync_history_window", existing)
        existing.refresh()
        existing.show()
        existing.raise_()
        existing.activateWindow()

    history_action.triggered.connect(open_sync_history)
    menu.addAction(history_action)
    calendar_window.addAction(history_action)
    setattr(calendar_window, "_provoware_sync_history_action", history_action)
    return action
