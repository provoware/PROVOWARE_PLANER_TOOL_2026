from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from PySide6.QtCore import QDateTime
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from calendar_core.model import CalendarEvent, MarkerType
from ui.design import DesignSystem


class EventDialog(QDialog):
    def __init__(
        self,
        design: DesignSystem,
        markers: tuple[MarkerType, ...],
        *,
        timezone_name: str,
        event: CalendarEvent | None = None,
        initial_date: date | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Termin bearbeiten" if event else "Neuer Termin")
        self._event = event
        self._timezone_name = timezone_name
        layout = QVBoxLayout(self)
        design.configure_layout(layout)
        form = QFormLayout()
        form.setSpacing(design.spacing("S"))
        self.title_edit = QLineEdit(event.title if event else "")
        self.description_edit = QPlainTextEdit(event.description if event else "")
        zone = ZoneInfo(self._timezone_name)
        if event:
            default_start = event.start_at
        elif initial_date:
            now = datetime.now(zone)
            default_start = datetime(
                initial_date.year, initial_date.month, initial_date.day,
                now.hour, (now.minute // 5) * 5, tzinfo=zone,
            )
        else:
            default_start = datetime.now(zone).replace(second=0, microsecond=0)
        default_end = event.end_at if event and event.end_at else default_start + timedelta(hours=1)
        self.start_edit = self._date_time_edit(default_start)
        self.end_edit = self._date_time_edit(default_end)
        self.all_day = QCheckBox("Ganztägig")
        self.all_day.setChecked(bool(event.all_day) if event else False)
        self.marker = QComboBox()
        self.marker.addItem("○ Ohne Markierung", None)
        for marker in markers:
            self.marker.addItem(f"{marker.symbol} {marker.title}", marker.marker_id)
        if event and event.marker_id is not None:
            index = self.marker.findData(event.marker_id)
            if index >= 0:
                self.marker.setCurrentIndex(index)

        form.addRow("Titel", self.title_edit)
        form.addRow("Beschreibung", self.description_edit)
        form.addRow("Beginn", self.start_edit)
        form.addRow("Ende", self.end_edit)
        form.addRow("", self.all_day)
        form.addRow("Markierung", self.marker)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        for widget, name in (
            (self.title_edit, "Termintitel"),
            (self.description_edit, "Terminbeschreibung"),
            (self.start_edit, "Terminbeginn"),
            (self.end_edit, "Terminende"),
            (self.all_day, "Ganztägiger Termin"),
            (self.marker, "Terminmarkierung"),
        ):
            design.accessible(widget, name)

    def _date_time_edit(self, value: datetime | None):
        from PySide6.QtWidgets import QDateTimeEdit
        zone = ZoneInfo(self._timezone_name)
        dt = value.astimezone(zone) if value else datetime.now(zone).replace(second=0, microsecond=0)
        editor = QDateTimeEdit(QDateTime(dt.year, dt.month, dt.day, dt.hour, dt.minute))
        editor.setCalendarPopup(True)
        editor.setDisplayFormat("dd.MM.yyyy HH:mm")
        return editor

    def values(self) -> dict:
        zone = ZoneInfo(self._timezone_name)
        start_qt = self.start_edit.dateTime()
        end_qt = self.end_edit.dateTime()
        start = datetime(
            start_qt.date().year(), start_qt.date().month(), start_qt.date().day(),
            start_qt.time().hour(), start_qt.time().minute(), tzinfo=zone,
        )
        end = datetime(
            end_qt.date().year(), end_qt.date().month(), end_qt.date().day(),
            end_qt.time().hour(), end_qt.time().minute(), tzinfo=zone,
        )
        return {
            "title": self.title_edit.text(),
            "description": self.description_edit.toPlainText(),
            "start_at": start,
            "end_at": end,
            "timezone_name": self._timezone_name,
            "all_day": self.all_day.isChecked(),
            "marker_id": self.marker.currentData(),
        }

    def updated_event(self) -> CalendarEvent:
        if self._event is None:
            raise RuntimeError("Dialog enthält keinen bestehenden Termin")
        values = self.values()
        return replace(
            self._event,
            title=values["title"],
            description=values["description"],
            start_at=values["start_at"],
            end_at=values["end_at"],
            timezone=values["timezone_name"],
            all_day=values["all_day"],
            marker_id=values["marker_id"],
        )


class MarkerEditorDialog(QDialog):
    def __init__(self, design: DesignSystem, markers: tuple[MarkerType, ...], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Fünf Markierungen bearbeiten")
        layout = QVBoxLayout(self)
        design.configure_layout(layout)
        grid = QGridLayout()
        grid.setSpacing(design.spacing("S"))
        for column, title in enumerate(("Nr.", "Name", "Kürzel", "Farbe", "Symbol")):
            grid.addWidget(QLabel(title), 0, column)
        self.rows: list[tuple[MarkerType, QLineEdit, QLineEdit, QLineEdit, QLineEdit]] = []
        for row, marker in enumerate(markers, start=1):
            grid.addWidget(QLabel(str(marker.marker_id)), row, 0)
            title = QLineEdit(marker.title)
            short = QLineEdit(marker.short_title)
            color = QLineEdit(marker.color)
            symbol = QLineEdit(marker.symbol)
            grid.addWidget(title, row, 1)
            grid.addWidget(short, row, 2)
            grid.addWidget(color, row, 3)
            grid.addWidget(symbol, row, 4)
            self.rows.append((marker, title, short, color, symbol))
            for widget, name in (
                (title, f"Name Markierung {marker.marker_id}"),
                (short, f"Kürzel Markierung {marker.marker_id}"),
                (color, f"Farbe Markierung {marker.marker_id}"),
                (symbol, f"Symbol Markierung {marker.marker_id}"),
            ):
                design.accessible(widget, name)
        layout.addLayout(grid)
        note = QLabel("Farbe wird als Hexwert angegeben, z. B. #2E7D32. Symbol und Text bleiben immer sichtbar.")
        note.setWordWrap(True)
        layout.addWidget(note)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def marker_values(self) -> tuple[MarkerType, ...]:
        result = []
        for original, title, short, color, symbol in self.rows:
            result.append(MarkerType(
                marker_id=original.marker_id,
                title=title.text(),
                short_title=short.text(),
                color=color.text(),
                symbol=symbol.text(),
                description=original.description,
                enabled=original.enabled,
            ))
        return tuple(result)
