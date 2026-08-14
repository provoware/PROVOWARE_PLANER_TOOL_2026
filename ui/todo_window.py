from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from services.calendar_service import CalendarService
from services.todo_service import TodoCalendarLinkService, TodoService
from todo_core.model import TodoStatus
from ui.design import DesignSystem, DesignTokens
from ui.todo_dialogs import LinkDialog, TodoDialog
from viewmodel.todo_query import STATUS_TEXT, TodoListMode
from viewmodel.todo_viewmodel import TodoViewModel

MODE_TEXT = {
    TodoListMode.TODAY: "Heute",
    TodoListMode.THIS_WEEK: "Diese Woche",
    TodoListMode.OVERDUE: "Überfällig",
    TodoListMode.WITHOUT_DATE: "Ohne Datum",
    TodoListMode.DONE: "Erledigt",
}


class TodoWindow(QMainWindow):
    def __init__(
        self,
        todo_service: TodoService,
        link_service: TodoCalendarLinkService,
        calendar_service: CalendarService,
        *,
        repo_root: Path,
        workspace: Path,
        timezone_name: str = "Europe/Berlin",
    ) -> None:
        super().__init__()
        self.todo_service = todo_service
        self.link_service = link_service
        self.calendar_service = calendar_service
        self.repo_root = Path(repo_root)
        self.workspace = Path(workspace)
        self.timezone_name = timezone_name
        self.zone = ZoneInfo(timezone_name)
        self.tokens = DesignTokens.from_repository(self.repo_root)
        self.design = DesignSystem(QApplication.instance(), self.tokens)
        self.view_model = TodoViewModel(todo_service, link_service, timezone_name=timezone_name)
        self._settings_path = self.workspace / "todo_gui_settings.json"
        self._load_settings()

        self.setWindowTitle("PROVOWARE PLANER – Aufgaben")
        self.setMinimumSize(900, 600)
        self.resize(1280, 760)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        self.design.configure_layout(root)

        self.status_label = QLabel()
        self.status_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.design.accessible(self.status_label, "Aufgabenstatus", "Ampelstatus mit Symbol und Klartext")
        root.addWidget(self.status_label)

        filters = QHBoxLayout()
        filters.setSpacing(self.design.spacing("S"))
        self.mode_combo = QComboBox()
        for mode in TodoListMode:
            self.mode_combo.addItem(MODE_TEXT[mode], mode)
        self.font_combo = QComboBox()
        for scale in self.tokens.font_scales:
            self.font_combo.addItem(f"{scale} %", scale)
        self.refresh_button = QPushButton("Aktualisieren")
        filters.addWidget(QLabel("Ansicht"))
        filters.addWidget(self.mode_combo)
        filters.addStretch(1)
        filters.addWidget(self.refresh_button)
        filters.addWidget(QLabel("Schrift"))
        filters.addWidget(self.font_combo)
        root.addLayout(filters)

        actions = QHBoxLayout()
        actions.setSpacing(self.design.spacing("S"))
        self.new_button = QPushButton("+ Aufgabe")
        self.edit_button = QPushButton("Bearbeiten")
        self.subtask_button = QPushButton("+ Unteraufgabe")
        self.link_button = QPushButton("Mit Kalender verbinden")
        self.unlink_button = QPushButton("Verknüpfung lösen")
        self.delete_button = QPushButton("In Papierkorb")
        for button in (
            self.new_button,
            self.edit_button,
            self.subtask_button,
            self.link_button,
            self.unlink_button,
            self.delete_button,
        ):
            actions.addWidget(button)
        actions.addStretch(1)
        root.addLayout(actions)

        quick = QHBoxLayout()
        quick.setSpacing(self.design.spacing("S"))
        self.status_combo = QComboBox()
        for status in TodoStatus:
            self.status_combo.addItem(STATUS_TEXT[status], status)
        self.set_status_button = QPushButton("Status setzen")
        self.progress_spin = QSpinBox()
        self.progress_spin.setRange(0, 100)
        self.progress_spin.setSuffix(" %")
        self.set_progress_button = QPushButton("Fortschritt setzen")
        quick.addWidget(QLabel("Status"))
        quick.addWidget(self.status_combo)
        quick.addWidget(self.set_status_button)
        quick.addSpacing(self.design.spacing("M"))
        quick.addWidget(QLabel("Fortschritt"))
        quick.addWidget(self.progress_spin)
        quick.addWidget(self.set_progress_button)
        quick.addStretch(1)
        root.addLayout(quick)

        body = QHBoxLayout()
        body.setSpacing(self.design.spacing("M"))
        left = QVBoxLayout()
        left.setSpacing(self.design.spacing("S"))
        left.addWidget(QLabel("Aufgaben"))
        self.todo_list = QListWidget()
        self.design.accessible(self.todo_list, "Aufgabenliste der gewählten Ansicht")
        left.addWidget(self.todo_list, 1)
        body.addLayout(left, 3)

        right = QVBoxLayout()
        right.setSpacing(self.design.spacing("S"))
        right.addWidget(QLabel("Details"))
        self.detail_label = QLabel("Keine Aufgabe ausgewählt.")
        self.detail_label.setWordWrap(True)
        self.detail_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.design.accessible(self.detail_label, "Details der ausgewählten Aufgabe")
        right.addWidget(self.detail_label)
        right.addWidget(QLabel("Kalender-Verknüpfungen und Konflikte"))
        self.links_list = QListWidget()
        self.links_list.setMinimumHeight(2 * self.design.spacing("XXL"))
        self.design.accessible(
            self.links_list,
            "Kalender-Verknüpfungen",
            "Zeigt Kopplungsrichtung und Konfliktstatus. I007 löst Konflikte nicht automatisch.",
        )
        right.addWidget(self.links_list, 1)
        notice = QLabel("I007 zeigt Konflikte nur an: keine automatische Synchronisation oder Konfliktauflösung.")
        notice.setWordWrap(True)
        right.addWidget(notice)
        body.addLayout(right, 2)
        root.addLayout(body, 1)

        for widget, name in (
            (self.mode_combo, "Aufgabenansicht auswählen"),
            (self.font_combo, "Schriftgröße auswählen"),
            (self.refresh_button, "Aufgaben aktualisieren"),
            (self.new_button, "Neue Aufgabe anlegen"),
            (self.edit_button, "Ausgewählte Aufgabe bearbeiten"),
            (self.subtask_button, "Unteraufgabe zur ausgewählten Aufgabe anlegen"),
            (self.link_button, "Ausgewählte Aufgabe mit Kalendertermin verbinden"),
            (self.unlink_button, "Ausgewählte Kalender-Verknüpfung lösen"),
            (self.delete_button, "Ausgewählte Aufgabe in Papierkorb verschieben"),
            (self.status_combo, "Neuen Aufgabenstatus auswählen"),
            (self.set_status_button, "Aufgabenstatus speichern"),
            (self.progress_spin, "Neuen Aufgabenfortschritt wählen"),
            (self.set_progress_button, "Aufgabenfortschritt speichern"),
        ):
            self.design.accessible(widget, name)

        self.mode_combo.currentIndexChanged.connect(self._mode_changed)
        self.font_combo.currentIndexChanged.connect(self._font_changed)
        self.refresh_button.clicked.connect(self.refresh)
        self.new_button.clicked.connect(self.new_todo)
        self.edit_button.clicked.connect(self.edit_selected)
        self.subtask_button.clicked.connect(self.new_subtask)
        self.link_button.clicked.connect(self.link_selected)
        self.unlink_button.clicked.connect(self.unlink_selected)
        self.delete_button.clicked.connect(self.delete_selected)
        self.set_status_button.clicked.connect(self.set_selected_status)
        self.set_progress_button.clicked.connect(self.set_selected_progress)
        self.todo_list.currentItemChanged.connect(lambda _current, _previous: self._selection_changed())
        self.todo_list.itemDoubleClicked.connect(lambda _item: self.edit_selected())

        QWidget.setTabOrder(self.mode_combo, self.refresh_button)
        QWidget.setTabOrder(self.refresh_button, self.font_combo)
        QWidget.setTabOrder(self.font_combo, self.new_button)
        QWidget.setTabOrder(self.new_button, self.edit_button)
        QWidget.setTabOrder(self.edit_button, self.subtask_button)
        QWidget.setTabOrder(self.subtask_button, self.link_button)
        QWidget.setTabOrder(self.link_button, self.unlink_button)
        QWidget.setTabOrder(self.unlink_button, self.delete_button)
        QWidget.setTabOrder(self.delete_button, self.status_combo)
        QWidget.setTabOrder(self.status_combo, self.set_status_button)
        QWidget.setTabOrder(self.set_status_button, self.progress_spin)
        QWidget.setTabOrder(self.progress_spin, self.set_progress_button)
        QWidget.setTabOrder(self.set_progress_button, self.todo_list)
        QWidget.setTabOrder(self.todo_list, self.links_list)

        self._install_shortcuts()
        self.design.apply_font_scale(self.view_model.font_scale_percent)
        self._sync_controls_from_model()
        self.refresh()

    def _install_shortcuts(self) -> None:
        bindings = (
            ("Neue Aufgabe", "Ctrl+N", self.new_todo),
            ("Aufgabe bearbeiten", "Ctrl+E", self.edit_selected),
            ("Unteraufgabe", "Ctrl+Shift+N", self.new_subtask),
            ("Kalender verbinden", "Ctrl+L", self.link_selected),
            ("Aktualisieren", "F5", self.refresh),
            ("In Papierkorb", "Delete", self.delete_selected),
        )
        for title, shortcut, callback in bindings:
            action = QAction(title, self)
            action.setShortcut(QKeySequence(shortcut))
            action.triggered.connect(callback)
            self.addAction(action)

    def _load_settings(self) -> None:
        if not self._settings_path.is_file():
            return
        try:
            data = json.loads(self._settings_path.read_text(encoding="utf-8"))
            scale = int(data.get("font_scale_percent", 100))
            if scale in self.tokens.font_scales:
                self.view_model.font_scale_percent = scale
            mode = data.get("todo_view_mode")
            if mode:
                self.view_model.mode = TodoListMode(mode)
        except Exception:
            pass

    def _save_settings(self) -> None:
        data = {
            "schema_version": 1,
            "font_scale_percent": self.view_model.font_scale_percent,
            "todo_view_mode": self.view_model.mode.value,
        }
        self._settings_path.parent.mkdir(parents=True, exist_ok=True)
        temp = self._settings_path.with_suffix(".tmp")
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temp.replace(self._settings_path)

    def closeEvent(self, event) -> None:
        self._save_settings()
        super().closeEvent(event)

    def _set_status(self, level: str, detail: str) -> None:
        symbol = {"GREEN": "●", "YELLOW": "▲", "RED": "●"}[level]
        self.status_label.setText(f"{symbol} {self.tokens.status_text[level]} | {detail}")

    def _sync_controls_from_model(self) -> None:
        self.mode_combo.blockSignals(True)
        self.mode_combo.setCurrentIndex(self.mode_combo.findData(self.view_model.mode))
        self.mode_combo.blockSignals(False)
        self.font_combo.blockSignals(True)
        self.font_combo.setCurrentIndex(max(self.font_combo.findData(self.view_model.font_scale_percent), 0))
        self.font_combo.blockSignals(False)

    def _mode_changed(self, index: int) -> None:
        if index < 0:
            return
        self.view_model.set_mode(self.mode_combo.itemData(index))
        self._save_settings()
        self.refresh()

    def _font_changed(self, index: int) -> None:
        if index < 0:
            return
        percent = int(self.font_combo.itemData(index))
        self.view_model.font_scale_percent = percent
        self.design.apply_font_scale(percent)
        self._save_settings()
        self.updateGeometry()

    def refresh(self) -> None:
        selected_id = self._selected_todo_id() or self.view_model.selected_todo_id
        try:
            snapshot = self.view_model.snapshot()
            self.todo_list.clear()
            selected_row = -1
            for row, todo in enumerate(snapshot.items):
                item = QListWidgetItem(todo.display_text)
                item.setData(Qt.UserRole, todo.todo_id)
                self.todo_list.addItem(item)
                if todo.todo_id == selected_id:
                    selected_row = row
            if self.todo_list.count() == 0:
                empty = QListWidgetItem("Keine Aufgaben in dieser Ansicht")
                empty.setFlags(empty.flags() & ~Qt.ItemIsSelectable)
                self.todo_list.addItem(empty)
                self.view_model.select(None)
            elif selected_row >= 0:
                self.todo_list.setCurrentRow(selected_row)
            else:
                self.todo_list.setCurrentRow(0)
            self._selection_changed()
            if snapshot.conflict_count:
                self._set_status("YELLOW", f"{snapshot.conflict_count} Kalender-Kopplung(en) benötigen manuelle Prüfung.")
            else:
                self._set_status("GREEN", f"Ansicht „{MODE_TEXT[snapshot.mode]}“ ist aktuell.")
        except Exception as exc:
            self._handle_error("GUI-TODO-REFRESH-001", "Aufgaben konnten nicht aktualisiert werden.", exc)

    def _selected_todo_id(self) -> str | None:
        item = self.todo_list.currentItem()
        if item is None:
            return None
        value = item.data(Qt.UserRole)
        return str(value) if value else None

    def _selected_link_id(self) -> str | None:
        item = self.links_list.currentItem()
        if item is None:
            return None
        value = item.data(Qt.UserRole)
        return str(value) if value else None

    def _selection_changed(self) -> None:
        todo_id = self._selected_todo_id()
        self.view_model.select(todo_id)
        self.links_list.clear()
        if not todo_id:
            self.detail_label.setText("Keine Aufgabe ausgewählt.")
            self.detail_label.setToolTip("")
            return
        try:
            view = self.view_model.selected_view()
            if view is None:
                return
            self.status_combo.setCurrentIndex(self.status_combo.findData(view.status))
            self.progress_spin.setValue(view.progress)
            self.progress_spin.setEnabled(view.status is not TodoStatus.DONE)
            self.set_progress_button.setEnabled(view.status is not TodoStatus.DONE)
            parent = view.parent_id or "Keine"
            description = view.description.strip() or "Keine Beschreibung"
            compact_description = " ".join(description.split())
            if len(compact_description) > 160:
                compact_description = compact_description[:157].rstrip() + "…"
            self.detail_label.setText(
                f"{view.title}\n"
                f"{view.status_text} | {view.priority_text} | {view.progress}%\n"
                f"Start: {view.start_text} | Fällig: {view.due_text}\n"
                f"Unteraufgabe von: {parent} | Version: {view.version} | {compact_description}"
            )
            self.detail_label.setToolTip(description)
            for link in view.links:
                item = QListWidgetItem(link.display_text)
                item.setData(Qt.UserRole, link.link_id)
                self.links_list.addItem(item)
            if self.links_list.count() == 0:
                empty = QListWidgetItem("Keine Kalender-Verknüpfung")
                empty.setFlags(empty.flags() & ~Qt.ItemIsSelectable)
                self.links_list.addItem(empty)
        except Exception as exc:
            self._handle_error("GUI-TODO-DETAIL-001", "Aufgabendetails konnten nicht geladen werden.", exc)

    def new_todo(self) -> None:
        dialog = TodoDialog(self.design, timezone_name=self.timezone_name, parent=self)
        if dialog.exec() != dialog.Accepted:
            return
        try:
            self.view_model.create_todo(**dialog.values())
            self.refresh()
            self._set_status("GREEN", "Aufgabe wurde gespeichert. Sie kann abhängig vom Datum in einer anderen Ansicht erscheinen.")
        except Exception as exc:
            self._handle_error("GUI-TODO-SAVE-001", "Aufgabe konnte nicht gespeichert werden.", exc)

    def edit_selected(self) -> None:
        todo_id = self._selected_todo_id()
        if not todo_id:
            self._set_status("YELLOW", "Bitte zuerst eine Aufgabe auswählen.")
            return
        try:
            todo = self.todo_service.get_todo(todo_id)
            dialog = TodoDialog(self.design, timezone_name=self.timezone_name, todo=todo, parent=self)
            if dialog.exec() != dialog.Accepted:
                return
            self.view_model.update_todo(todo_id, **dialog.values())
            self.refresh()
            self._set_status("GREEN", "Aufgabe wurde aktualisiert.")
        except Exception as exc:
            self._handle_error("GUI-TODO-EDIT-001", "Aufgabe konnte nicht aktualisiert werden.", exc)

    def new_subtask(self) -> None:
        parent_id = self._selected_todo_id()
        if not parent_id:
            self._set_status("YELLOW", "Bitte zuerst die übergeordnete Aufgabe auswählen.")
            return
        dialog = TodoDialog(self.design, timezone_name=self.timezone_name, parent=self)
        if dialog.exec() != dialog.Accepted:
            return
        try:
            self.view_model.create_todo(parent_id=parent_id, **dialog.values())
            self.refresh()
            self._set_status("GREEN", "Unteraufgabe wurde gespeichert.")
        except Exception as exc:
            self._handle_error("GUI-TODO-SUBTASK-001", "Unteraufgabe konnte nicht gespeichert werden.", exc)

    def set_selected_status(self) -> None:
        todo_id = self._selected_todo_id()
        if not todo_id:
            self._set_status("YELLOW", "Bitte zuerst eine Aufgabe auswählen.")
            return
        try:
            self.view_model.set_status(todo_id, self.status_combo.currentData())
            self.refresh()
            self._set_status("GREEN", "Status wurde gespeichert.")
        except Exception as exc:
            self._handle_error("GUI-TODO-STATUS-001", "Status konnte nicht gespeichert werden.", exc)

    def set_selected_progress(self) -> None:
        todo_id = self._selected_todo_id()
        if not todo_id:
            self._set_status("YELLOW", "Bitte zuerst eine Aufgabe auswählen.")
            return
        try:
            current = self.todo_service.get_todo(todo_id)
            if current.status is TodoStatus.DONE:
                self._set_status("YELLOW", "Erledigte Aufgaben behalten 100 % Fortschritt.")
                return
            self.view_model.set_progress(todo_id, self.progress_spin.value())
            self.refresh()
            self._set_status("GREEN", "Fortschritt wurde gespeichert.")
        except Exception as exc:
            self._handle_error("GUI-TODO-PROGRESS-001", "Fortschritt konnte nicht gespeichert werden.", exc)

    def _calendar_candidates(self) -> tuple:
        now = datetime.now(self.zone)
        events = self.calendar_service.list_events(now - timedelta(days=365), now + timedelta(days=365))
        return tuple(events[:500])

    def link_selected(self) -> None:
        todo_id = self._selected_todo_id()
        if not todo_id:
            self._set_status("YELLOW", "Bitte zuerst eine Aufgabe auswählen.")
            return
        try:
            dialog = LinkDialog(
                self.design,
                self._calendar_candidates(),
                timezone_name=self.timezone_name,
                parent=self,
            )
            if dialog.exec() != dialog.Accepted:
                return
            event_id, direction = dialog.values()
            self.view_model.link_calendar(todo_id, event_id, direction)
            self.refresh()
            self._set_status("GREEN", "Kalender-Verknüpfung wurde gespeichert; automatische Synchronisation bleibt deaktiviert.")
        except Exception as exc:
            self._handle_error("GUI-TODO-LINK-001", "Kalender-Verknüpfung konnte nicht gespeichert werden.", exc)

    def unlink_selected(self) -> None:
        link_id = self._selected_link_id()
        if not link_id:
            self._set_status("YELLOW", "Bitte zuerst eine Kalender-Verknüpfung auswählen.")
            return
        try:
            self.view_model.unlink(link_id)
            self.refresh()
            self._set_status("GREEN", "Verknüpfung wurde gelöst. Aufgabe und Termin bleiben erhalten.")
        except Exception as exc:
            self._handle_error("GUI-TODO-UNLINK-001", "Verknüpfung konnte nicht gelöst werden.", exc)

    def delete_selected(self) -> None:
        todo_id = self._selected_todo_id()
        if not todo_id:
            self._set_status("YELLOW", "Bitte zuerst eine Aufgabe auswählen.")
            return
        answer = QMessageBox.question(
            self,
            "Aufgabe in Papierkorb verschieben",
            "Die Aufgabe wird weich gelöscht. Gekoppelte Kalendertermine werden nicht gelöscht. Fortfahren?",
        )
        if answer != QMessageBox.Yes:
            return
        try:
            self.view_model.soft_delete(todo_id)
            self.refresh()
            self._set_status("GREEN", "Aufgabe wurde in den Papierkorb verschoben. Kalendertermine blieben erhalten.")
        except Exception as exc:
            self._handle_error("GUI-TODO-DELETE-001", "Aufgabe konnte nicht in den Papierkorb verschoben werden.", exc)

    def _handle_error(self, code: str, message: str, exc: Exception) -> None:
        self._set_status("RED", f"{code}: {message}")
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Critical)
        box.setWindowTitle("PROVOWARE PLANER – Fehler")
        box.setText(message)
        box.setInformativeText(f"Fehler-ID: {code}\nEs wurde keine automatische Konfliktauflösung durchgeführt.")
        box.setDetailedText(repr(exc))
        box.exec()
