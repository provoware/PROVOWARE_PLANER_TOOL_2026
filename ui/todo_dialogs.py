from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from PySide6.QtCore import QDateTime
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QSpinBox,
    QVBoxLayout,
)

from calendar_core.model import CalendarEvent
from todo_core.model import LinkDirection, TodoItem, TodoPriority, TodoStatus
from ui.design import DesignSystem
from viewmodel.todo_query import DIRECTION_TEXT, PRIORITY_TEXT, STATUS_TEXT


class TodoDialog(QDialog):
    def __init__(
        self,
        design: DesignSystem,
        *,
        timezone_name: str,
        todo: TodoItem | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.design = design
        self.timezone_name = timezone_name
        self.zone = ZoneInfo(timezone_name)
        self.todo = todo
        self.setWindowTitle("Aufgabe bearbeiten" if todo else "Neue Aufgabe")
        self.setMinimumWidth(520)

        root = QVBoxLayout(self)
        self.design.configure_layout(root)
        form = QFormLayout()
        form.setSpacing(self.design.spacing("S"))

        self.title_edit = QLineEdit()
        self.description_edit = QPlainTextEdit()
        self.description_edit.setMaximumHeight(120)
        self.status_combo = QComboBox()
        for value in TodoStatus:
            self.status_combo.addItem(STATUS_TEXT[value], value)
        self.priority_combo = QComboBox()
        for value in TodoPriority:
            self.priority_combo.addItem(PRIORITY_TEXT[value], value)
        self.progress_spin = QSpinBox()
        self.progress_spin.setRange(0, 100)
        self.progress_spin.setSuffix(" %")

        self.start_check = QCheckBox("Startdatum verwenden")
        self.start_edit = QDateTimeEdit()
        self.start_edit.setCalendarPopup(True)
        self.start_edit.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.due_check = QCheckBox("Fälligkeit verwenden")
        self.due_edit = QDateTimeEdit()
        self.due_edit.setCalendarPopup(True)
        self.due_edit.setDisplayFormat("dd.MM.yyyy HH:mm")

        form.addRow("Titel", self.title_edit)
        form.addRow("Beschreibung", self.description_edit)
        form.addRow("Status", self.status_combo)
        form.addRow("Priorität", self.priority_combo)
        form.addRow("Fortschritt", self.progress_spin)
        form.addRow(self.start_check, self.start_edit)
        form.addRow(self.due_check, self.due_edit)
        root.addLayout(form)

        info = QLabel("Alle Zeiten werden mit Zeitzone gespeichert. Erledigte Aufgaben erhalten automatisch 100 % Fortschritt.")
        info.setWordWrap(True)
        root.addWidget(info)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        root.addWidget(self.buttons)

        for widget, name in (
            (self.title_edit, "Aufgabentitel"),
            (self.description_edit, "Aufgabenbeschreibung"),
            (self.status_combo, "Aufgabenstatus"),
            (self.priority_combo, "Aufgabenpriorität"),
            (self.progress_spin, "Aufgabenfortschritt"),
            (self.start_check, "Startdatum verwenden"),
            (self.start_edit, "Startdatum und Uhrzeit"),
            (self.due_check, "Fälligkeit verwenden"),
            (self.due_edit, "Fälligkeit Datum und Uhrzeit"),
        ):
            self.design.accessible(widget, name)

        now = QDateTime.currentDateTime()
        self.start_edit.setDateTime(now)
        self.due_edit.setDateTime(now.addSecs(3600))
        self.start_check.toggled.connect(self.start_edit.setEnabled)
        self.due_check.toggled.connect(self.due_edit.setEnabled)
        self.start_edit.setEnabled(False)
        self.due_edit.setEnabled(False)
        self.status_combo.currentIndexChanged.connect(self._status_changed)

        if todo is not None:
            self._load(todo)

    def _load(self, todo: TodoItem) -> None:
        self.title_edit.setText(todo.title)
        self.description_edit.setPlainText(todo.description)
        self.status_combo.setCurrentIndex(self.status_combo.findData(todo.status))
        self.priority_combo.setCurrentIndex(self.priority_combo.findData(todo.priority))
        self.progress_spin.setValue(todo.progress)
        if todo.start_at is not None:
            self.start_check.setChecked(True)
            self.start_edit.setDateTime(self._qdatetime(todo.start_at.astimezone(self.zone)))
        if todo.due_at is not None:
            self.due_check.setChecked(True)
            self.due_edit.setDateTime(self._qdatetime(todo.due_at.astimezone(self.zone)))
        self._status_changed()

    @staticmethod
    def _qdatetime(value: datetime) -> QDateTime:
        return QDateTime(value.year, value.month, value.day, value.hour, value.minute, value.second)

    def _status_changed(self) -> None:
        status = self.status_combo.currentData()
        if status is TodoStatus.DONE:
            self.progress_spin.setValue(100)
            self.progress_spin.setEnabled(False)
        else:
            self.progress_spin.setEnabled(True)

    def _datetime(self, editor: QDateTimeEdit, enabled: bool) -> datetime | None:
        if not enabled:
            return None
        qdt = editor.dateTime()
        qdate = qdt.date()
        qtime = qdt.time()
        return datetime(
            qdate.year(), qdate.month(), qdate.day(),
            qtime.hour(), qtime.minute(), qtime.second(),
            tzinfo=self.zone,
        )

    def values(self) -> dict:
        status = self.status_combo.currentData()
        progress = 100 if status is TodoStatus.DONE else self.progress_spin.value()
        return {
            "title": self.title_edit.text(),
            "description": self.description_edit.toPlainText(),
            "status": status,
            "priority": self.priority_combo.currentData(),
            "progress": progress,
            "start_at": self._datetime(self.start_edit, self.start_check.isChecked()),
            "due_at": self._datetime(self.due_edit, self.due_check.isChecked()),
        }


class LinkDialog(QDialog):
    def __init__(
        self,
        design: DesignSystem,
        events: tuple[CalendarEvent, ...],
        *,
        timezone_name: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.design = design
        self.zone = ZoneInfo(timezone_name)
        self.setWindowTitle("Aufgabe mit Kalender verbinden")
        self.setMinimumWidth(560)

        root = QVBoxLayout(self)
        self.design.configure_layout(root)
        warning = QLabel(
            "Die Kopplung speichert nur Identität, Richtung und Konfliktzustand. I007 synchronisiert keine Inhalte automatisch."
        )
        warning.setWordWrap(True)
        root.addWidget(warning)

        form = QFormLayout()
        form.setSpacing(self.design.spacing("S"))
        self.event_combo = QComboBox()
        for event in events:
            local = event.start_at.astimezone(self.zone)
            self.event_combo.addItem(f"{local:%d.%m.%Y %H:%M} | {event.title}", event.event_id)
        self.direction_combo = QComboBox()
        for direction in LinkDirection:
            self.direction_combo.addItem(DIRECTION_TEXT[direction], direction)
        form.addRow("Kalendertermin", self.event_combo)
        form.addRow("Richtung", self.direction_combo)
        root.addLayout(form)

        self.design.accessible(self.event_combo, "Kalendertermin für Aufgabe auswählen")
        self.design.accessible(self.direction_combo, "Kopplungsrichtung auswählen")

        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        root.addWidget(self.buttons)
        if not events:
            self.event_combo.addItem("Keine Termine im Auswahlzeitraum verfügbar", None)
            self.buttons.button(QDialogButtonBox.Save).setEnabled(False)

    def values(self) -> tuple[str, LinkDirection]:
        event_id = self.event_combo.currentData()
        return str(event_id), self.direction_combo.currentData()
