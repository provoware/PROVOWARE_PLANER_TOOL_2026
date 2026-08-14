from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui.design import DesignSystem
from viewmodel.calendar_query import DayViewData, MonthViewData, WeekViewData, YearViewData

WEEKDAYS = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")
MONTHS = (
    "", "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
)


class DayView(QWidget):
    dateSelected = Signal(object)

    def __init__(self, design: DesignSystem) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        design.configure_layout(layout)
        self.title = QLabel()
        self.events = QListWidget()
        design.accessible(self.title, "Tagesüberschrift")
        design.accessible(self.events, "Termine des Tages", "Liste aller Termine am ausgewählten Tag")
        layout.addWidget(self.title)
        layout.addWidget(self.events, 1)

    def set_data(self, data: DayViewData) -> None:
        self.title.setText(data.day.strftime("%A, %d.%m.%Y"))
        self.events.clear()
        if not data.events:
            item = QListWidgetItem("Keine Termine")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.events.addItem(item)
        for event in data.events:
            item = QListWidgetItem(event.display_text)
            item.setData(Qt.UserRole, event.event_id)
            self.events.addItem(item)


class WeekView(QWidget):
    dateSelected = Signal(object)

    def __init__(self, design: DesignSystem) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        design.configure_layout(layout)
        self.table = QTableWidget(1, 7)
        self.table.setHorizontalHeaderLabels(WEEKDAYS)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setSelectionBehavior(QTableWidget.SelectItems)
        self.table.cellClicked.connect(self._clicked)
        design.accessible(self.table, "Wochenkalender", "Sieben Spalten von Montag bis Sonntag")
        layout.addWidget(self.table)
        self._dates: dict[int, date] = {}

    def _clicked(self, _row: int, column: int) -> None:
        if column in self._dates:
            self.dateSelected.emit(self._dates[column])

    def set_data(self, data: WeekViewData) -> None:
        self._dates.clear()
        for column, day_data in enumerate(data.days):
            self._dates[column] = day_data.day
            lines = [day_data.day.strftime("%d.%m.%Y")]
            lines.extend(event.display_text for event in day_data.events)
            if len(lines) == 1:
                lines.append("Keine Termine")
            item = QTableWidgetItem("\n".join(lines))
            item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
            self.table.setItem(0, column, item)
        self.table.resizeRowsToContents()


class MonthView(QWidget):
    dateSelected = Signal(object)

    def __init__(self, design: DesignSystem) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        design.configure_layout(layout)
        self.table = QTableWidget(6, 7)
        self.table.setHorizontalHeaderLabels(WEEKDAYS)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.cellClicked.connect(self._clicked)
        design.accessible(self.table, "Monatskalender", "Kalenderraster mit sieben Wochentagen")
        layout.addWidget(self.table)
        self._dates: dict[tuple[int, int], date] = {}

    def _clicked(self, row: int, column: int) -> None:
        selected = self._dates.get((row, column))
        if selected is not None:
            self.dateSelected.emit(selected)

    def set_data(self, data: MonthViewData) -> None:
        self.table.setRowCount(max(6, len(data.weeks)))
        self._dates.clear()
        for row in range(self.table.rowCount()):
            for column in range(7):
                self.table.setItem(row, column, QTableWidgetItem(""))
        for row, week in enumerate(data.weeks):
            for column, cell in enumerate(week):
                self._dates[(row, column)] = cell.day
                prefix = "" if cell.in_month else "↳ "
                lines = [f"{prefix}{cell.day.day:02d}"]
                lines.extend(event.display_text for event in cell.events[:4])
                if len(cell.events) > 4:
                    lines.append(f"+ {len(cell.events) - 4} weitere")
                item = QTableWidgetItem("\n".join(lines))
                item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
                if not cell.in_month:
                    item.setToolTip("Tag gehört zum angrenzenden Monat")
                self.table.setItem(row, column, item)


class YearView(QWidget):
    dateSelected = Signal(object)

    def __init__(self, design: DesignSystem) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        design.configure_layout(layout)
        self.table = QTableWidget(4, 3)
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.cellClicked.connect(self._clicked)
        design.accessible(self.table, "Jahreskalender", "Zwölf Monatsfelder mit Termin- und Markierungsübersicht")
        layout.addWidget(self.table)
        self._months: dict[tuple[int, int], date] = {}

    def _clicked(self, row: int, column: int) -> None:
        selected = self._months.get((row, column))
        if selected is not None:
            self.dateSelected.emit(selected)

    def set_data(self, data: YearViewData, marker_names: dict[int, str]) -> None:
        self._months.clear()
        for month_data in data.months:
            index = month_data.month - 1
            row, column = divmod(index, 3)
            selected = date(data.year, month_data.month, 1)
            self._months[(row, column)] = selected
            lines = [MONTHS[month_data.month], f"Termine: {month_data.event_count}"]
            for marker_id, count in month_data.marker_counts:
                lines.append(f"{marker_names.get(marker_id, f'Markierung {marker_id}')}: {count}")
            item = QTableWidgetItem("\n".join(lines))
            item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
            self.table.setItem(row, column, item)
