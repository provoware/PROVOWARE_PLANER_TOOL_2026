from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from services.calendar_service import CalendarService
from ui.calendar_views import DayView, MonthView, WeekView, YearView
from ui.design import DesignSystem, DesignTokens
from ui.dialogs import EventDialog, MarkerEditorDialog
from viewmodel.calendar_viewmodel import CalendarViewMode, CalendarViewModel


class CalendarWindow(QMainWindow):
    def __init__(
        self,
        service: CalendarService,
        *,
        repo_root: Path,
        workspace: Path,
        timezone_name: str = "Europe/Berlin",
    ) -> None:
        super().__init__()
        self.service = service
        self.repo_root = Path(repo_root)
        self.workspace = Path(workspace)
        self.timezone_name = timezone_name
        self.tokens = DesignTokens.from_repository(self.repo_root)
        self.design = DesignSystem(QApplication.instance(), self.tokens)
        self.view_model = CalendarViewModel(service, timezone_name=timezone_name)
        self._settings_path = self.workspace / "gui_settings.json"
        self._load_settings()

        self.setWindowTitle("PROVOWARE PLANER – Kalender")
        self.setMinimumSize(900, 600)
        self.resize(1280, 760)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        self.design.configure_layout(root)

        self.status_label = QLabel()
        self.status_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.design.accessible(self.status_label, "Systemstatus", "Ampelstatus mit Symbol und Klartext")
        root.addWidget(self.status_label)

        nav_primary = QHBoxLayout()
        nav_primary.setSpacing(self.design.spacing("S"))
        nav_actions = QHBoxLayout()
        nav_actions.setSpacing(self.design.spacing("S"))
        self.back_button = QPushButton("← Zurück")
        self.today_button = QPushButton("Heute")
        self.next_button = QPushButton("Vor →")
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        self.view_combo = QComboBox()
        self.view_combo.addItems([mode.value.title() for mode in CalendarViewMode])
        self.font_combo = QComboBox()
        for scale in self.tokens.font_scales:
            self.font_combo.addItem(f"{scale} %", scale)
        self.new_button = QPushButton("+ Termin")
        self.edit_button = QPushButton("Termin bearbeiten")
        self.marker_button = QPushButton("Markierungen")

        for widget in (self.back_button, self.today_button, self.next_button, self.date_edit, self.view_combo):
            nav_primary.addWidget(widget)
        nav_primary.addStretch(1)
        for widget in (self.new_button, self.edit_button, self.marker_button, self.font_combo):
            nav_actions.addWidget(widget)
        nav_actions.addStretch(1)
        root.addLayout(nav_primary)
        root.addLayout(nav_actions)

        for widget, name in (
            (self.back_button, "Kalender zurück"),
            (self.today_button, "Heute öffnen"),
            (self.next_button, "Kalender vor"),
            (self.date_edit, "Datum auswählen"),
            (self.view_combo, "Kalenderansicht auswählen"),
            (self.font_combo, "Schriftgröße auswählen"),
            (self.new_button, "Neuen Termin anlegen"),
            (self.edit_button, "Ausgewählten Termin bearbeiten"),
            (self.marker_button, "Fünf Markierungen bearbeiten"),
        ):
            self.design.accessible(widget, name)

        self.marker_bar = QHBoxLayout()
        self.marker_bar.setSpacing(self.design.spacing("S"))
        self.marker_labels = [QLabel() for _ in range(5)]
        for index, label in enumerate(self.marker_labels, start=1):
            label.setMinimumWidth(120)
            label.setWordWrap(True)
            self.design.accessible(label, f"Markierung {index}")
            self.marker_bar.addWidget(label, 1)
        root.addLayout(self.marker_bar)

        self.stack = QStackedWidget()
        self.day_view = DayView(self.design)
        self.week_view = WeekView(self.design)
        self.month_view = MonthView(self.design)
        self.year_view = YearView(self.design)
        for view in (self.day_view, self.week_view, self.month_view, self.year_view):
            self.stack.addWidget(view)
            view.dateSelected.connect(self._date_selected_from_view)
        self.design.accessible(self.stack, "Kalenderansicht")
        root.addWidget(self.stack, 1)

        events_title = QLabel("Termine am ausgewählten Tag")
        self.day_events = QListWidget()
        self.day_events.setMaximumHeight(170)
        self.design.accessible(self.day_events, "Terminliste des ausgewählten Tages")
        root.addWidget(events_title)
        root.addWidget(self.day_events)

        self.back_button.clicked.connect(lambda: self._navigate(-1))
        self.next_button.clicked.connect(lambda: self._navigate(1))
        self.today_button.clicked.connect(self._today)
        self.date_edit.dateChanged.connect(self._date_changed)
        self.view_combo.currentIndexChanged.connect(self._mode_changed)
        self.font_combo.currentIndexChanged.connect(self._font_changed)
        self.new_button.clicked.connect(self.new_event)
        self.edit_button.clicked.connect(self.edit_selected_event)
        self.marker_button.clicked.connect(self.edit_markers)
        self.day_events.itemDoubleClicked.connect(lambda _item: self.edit_selected_event())

        QWidget.setTabOrder(self.back_button, self.today_button)
        QWidget.setTabOrder(self.today_button, self.next_button)
        QWidget.setTabOrder(self.next_button, self.date_edit)
        QWidget.setTabOrder(self.date_edit, self.view_combo)
        QWidget.setTabOrder(self.view_combo, self.new_button)
        QWidget.setTabOrder(self.new_button, self.edit_button)
        QWidget.setTabOrder(self.edit_button, self.marker_button)
        QWidget.setTabOrder(self.marker_button, self.font_combo)
        QWidget.setTabOrder(self.font_combo, self.day_events)
        self._install_shortcuts()
        self.design.apply_font_scale(self.view_model.font_scale_percent)
        self._sync_controls_from_model()
        self.refresh()
        self._set_status("GREEN", "Kalenderdaten und Oberfläche sind bereit.")

    def _install_shortcuts(self) -> None:
        bindings = (
            ("Neuer Termin", "Ctrl+N", self.new_event),
            ("Termin bearbeiten", "Ctrl+E", self.edit_selected_event),
            ("Heute", "Ctrl+T", self._today),
            ("Zurück", "Ctrl+Left", lambda: self._navigate(-1)),
            ("Vor", "Ctrl+Right", lambda: self._navigate(1)),
        )
        for title, shortcut, callback in bindings:
            action = QAction(title, self)
            action.setShortcut(QKeySequence(shortcut))
            action.triggered.connect(callback)
            self.addAction(action)
        for index, mode in enumerate(CalendarViewMode, start=1):
            action = QAction(f"Ansicht {mode.value}", self)
            action.setShortcut(QKeySequence(f"Alt+{index}"))
            action.triggered.connect(lambda checked=False, value=mode: self._set_mode(value))
            self.addAction(action)

    def _load_settings(self) -> None:
        if not self._settings_path.is_file():
            return
        try:
            data = json.loads(self._settings_path.read_text(encoding="utf-8"))
            scale = int(data.get("font_scale_percent", 100))
            if scale in self.tokens.font_scales:
                self.view_model.font_scale_percent = scale
            mode = data.get("calendar_view_mode")
            if mode:
                self.view_model.mode = CalendarViewMode(mode)
        except Exception:
            pass

    def _save_settings(self) -> None:
        data = {
            "schema_version": 1,
            "font_scale_percent": self.view_model.font_scale_percent,
            "calendar_view_mode": self.view_model.mode.value,
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
        value = self.view_model.reference_date
        self.date_edit.blockSignals(True)
        self.date_edit.setDate(QDate(value.year, value.month, value.day))
        self.date_edit.blockSignals(False)
        self.view_combo.blockSignals(True)
        self.view_combo.setCurrentIndex(list(CalendarViewMode).index(self.view_model.mode))
        self.view_combo.blockSignals(False)
        self.font_combo.blockSignals(True)
        index = self.font_combo.findData(self.view_model.font_scale_percent)
        self.font_combo.setCurrentIndex(max(index, 0))
        self.font_combo.blockSignals(False)
        self.stack.setCurrentIndex(list(CalendarViewMode).index(self.view_model.mode))

    def _date_selected_from_view(self, selected: date) -> None:
        self.view_model.select_date(selected)
        self._sync_controls_from_model()
        self.refresh_day_events()

    def _date_changed(self, qdate: QDate) -> None:
        self.view_model.select_date(date(qdate.year(), qdate.month(), qdate.day()))
        self.refresh()

    def _mode_changed(self, index: int) -> None:
        if index < 0:
            return
        self.view_model.set_mode(list(CalendarViewMode)[index])
        self.stack.setCurrentIndex(index)
        self._save_settings()
        self.refresh()

    def _set_mode(self, mode: CalendarViewMode) -> None:
        self.view_model.set_mode(mode)
        self._sync_controls_from_model()
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

    def _navigate(self, direction: int) -> None:
        self.view_model.navigate(direction)
        self._sync_controls_from_model()
        self.refresh()

    def _today(self) -> None:
        self.view_model.today()
        self._sync_controls_from_model()
        self.refresh()

    def refresh(self) -> None:
        try:
            snapshot = self.view_model.snapshot()
            markers = self.view_model.markers()
            marker_names = {marker.marker_id: f"{marker.symbol} {marker.title}" for marker in markers}
            if self.view_model.mode == CalendarViewMode.DAY:
                self.day_view.set_data(snapshot)
            elif self.view_model.mode == CalendarViewMode.WEEK:
                self.week_view.set_data(snapshot)
            elif self.view_model.mode == CalendarViewMode.MONTH:
                self.month_view.set_data(snapshot)
            else:
                self.year_view.set_data(snapshot, marker_names)
            self._refresh_marker_bar(markers)
            self.refresh_day_events()
            self._set_status("GREEN", "Ansicht aktualisiert.")
        except Exception as exc:
            self._handle_error("GUI-CALENDAR-REFRESH-001", "Kalenderansicht konnte nicht aktualisiert werden.", exc)

    def _refresh_marker_bar(self, markers) -> None:
        by_id = {marker.marker_id: marker for marker in markers}
        for index, label in enumerate(self.marker_labels, start=1):
            marker = by_id.get(index)
            if marker is None:
                label.setText(f"○ Markierung {index}: nicht verfügbar")
                label.setStyleSheet("")
                continue
            label.setText(f"{marker.symbol} {marker.title}\n{marker.short_title}")
            label.setToolTip(f"Farbe: {marker.color} | {marker.description}")
            label.setStyleSheet(f"border-left: 4px solid {marker.color}; padding-left: 8px;")

    def refresh_day_events(self) -> None:
        self.day_events.clear()
        for event in self.view_model.day_events():
            item = QListWidgetItem(event.display_text)
            item.setData(Qt.UserRole, event.event_id)
            self.day_events.addItem(item)
        if self.day_events.count() == 0:
            item = QListWidgetItem("Keine Termine am ausgewählten Tag")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.day_events.addItem(item)

    def new_event(self) -> None:
        dialog = EventDialog(
            self.design,
            tuple(self.service.list_markers()),
            timezone_name=self.timezone_name,
            initial_date=self.view_model.reference_date,
            parent=self,
        )
        if dialog.exec() != dialog.Accepted:
            return
        try:
            self.service.create_event(**dialog.values())
            self.refresh()
            self._set_status("GREEN", "Termin wurde gespeichert.")
        except Exception as exc:
            self._handle_error("GUI-EVENT-SAVE-001", "Termin konnte nicht gespeichert werden.", exc)

    def _selected_event_id(self) -> str | None:
        item = self.day_events.currentItem()
        if item is None:
            return None
        value = item.data(Qt.UserRole)
        return str(value) if value else None

    def edit_selected_event(self) -> None:
        event_id = self._selected_event_id()
        if not event_id:
            self._set_status("YELLOW", "Bitte zuerst einen Termin in der Terminliste auswählen.")
            return
        try:
            event = self.service.get_event(event_id)
            dialog = EventDialog(
                self.design,
                tuple(self.service.list_markers()),
                timezone_name=self.timezone_name,
                event=event,
                parent=self,
            )
            if dialog.exec() != dialog.Accepted:
                return
            updated = dialog.updated_event()
            self.service.update_event(updated, expected_version=event.version)
            self.refresh()
            self._set_status("GREEN", "Termin wurde aktualisiert.")
        except Exception as exc:
            self._handle_error("GUI-EVENT-EDIT-001", "Termin konnte nicht aktualisiert werden.", exc)

    def edit_markers(self) -> None:
        try:
            dialog = MarkerEditorDialog(self.design, tuple(self.service.list_markers()), self)
            if dialog.exec() != dialog.Accepted:
                return
            self.service.update_markers(dialog.marker_values())
            self.refresh()
            self._set_status("GREEN", "Fünf Markierungen wurden gespeichert.")
        except Exception as exc:
            self._handle_error("GUI-MARKER-SAVE-001", "Markierungen konnten nicht gespeichert werden.", exc)

    def _handle_error(self, code: str, message: str, exc: Exception) -> None:
        self._set_status("RED", f"{code}: {message}")
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Critical)
        box.setWindowTitle("PROVOWARE PLANER – Fehler")
        box.setText(message)
        box.setInformativeText(f"Fehler-ID: {code}\nDie Daten wurden nicht absichtlich überschrieben.")
        box.setDetailedText(repr(exc))
        box.exec()
