from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services.history_service import SyncJournalService
from sync_core.history import RecoveryMode
from ui.design import DesignSystem, DesignTokens
from viewmodel.sync_history_query import SyncHistoryQuery
from viewmodel.sync_history_viewmodel import SyncHistoryViewModel


HISTORY_COLUMNS = (
    "Zeitpunkt",
    "Art",
    "Verknüpfung",
    "Integrität",
    "Recovery",
    "Versionen",
    "Receipt-SHA-256",
    "Plan-ID",
    "Receipt-ID",
)

DETAIL_COLUMNS = (
    "Feld",
    "Vorher Todo",
    "Vorher Kalender",
    "Nachher Todo",
    "Nachher Kalender",
)


class SyncHistoryWindow(QMainWindow):
    def __init__(self, service: SyncJournalService, *, repo_root: Path) -> None:
        super().__init__()
        self.repo_root = Path(repo_root)
        self.tokens = DesignTokens.from_repository(self.repo_root)
        self.design = DesignSystem(QApplication.instance(), self.tokens)
        self.view_model = SyncHistoryViewModel(SyncHistoryQuery(service), service)
        self._row_receipts: list[str] = []

        self.setWindowTitle("PROVOWARE PLANER – Synchronisationsjournal")
        self.setMinimumSize(900, 650)
        self.resize(1500, 860)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        self.design.configure_layout(root)

        intro = QLabel(
            "Hier sehen Sie unveränderliche Synchronisationsnachweise. "
            "Ein alter Nachweis wird niemals still erneut ausgeführt. "
            "Jede Wiederholung erzeugt zuerst einen neuen, aktuellen RecoveryPlan."
        )
        intro.setWordWrap(True)
        root.addWidget(intro)

        controls = QHBoxLayout()
        controls.setSpacing(self.design.spacing("S"))
        controls.addWidget(QLabel("Verknüpfung"))
        self.link_filter = QComboBox()
        self.refresh_button = QPushButton("Journal neu laden")
        controls.addWidget(self.link_filter, 1)
        controls.addWidget(self.refresh_button)
        root.addLayout(controls)

        splitter = QSplitter(Qt.Orientation.Vertical)
        self.history_table = QTableWidget(0, len(HISTORY_COLUMNS))
        self.history_table.setHorizontalHeaderLabels(HISTORY_COLUMNS)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.history_table.setWordWrap(True)
        self.history_table.horizontalHeader().setStretchLastSection(True)

        self.detail_table = QTableWidget(0, len(DETAIL_COLUMNS))
        self.detail_table.setHorizontalHeaderLabels(DETAIL_COLUMNS)
        self.detail_table.setAlternatingRowColors(True)
        self.detail_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.detail_table.setWordWrap(True)
        self.detail_table.horizontalHeader().setStretchLastSection(True)
        splitter.addWidget(self.history_table)
        splitter.addWidget(self.detail_table)
        splitter.setSizes([430, 260])
        root.addWidget(splitter, 1)

        actions = QHBoxLayout()
        actions.setSpacing(self.design.spacing("S"))
        self.reapply_button = QPushButton("Nachher-Stand prüfen")
        self.restore_button = QPushButton("Vorher-Stand prüfen")
        self.execute_button = QPushButton("RecoveryPlan atomar ausführen")
        actions.addWidget(self.reapply_button)
        actions.addWidget(self.restore_button)
        actions.addWidget(self.execute_button)
        actions.addStretch(1)
        root.addLayout(actions)

        self.status_label = QLabel("Noch kein Journalnachweis ausgewählt.")
        self.status_label.setWordWrap(True)
        self.status_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        root.addWidget(self.status_label)

        self.design.accessible(self.link_filter, "Journal nach Verknüpfung filtern")
        self.design.accessible(self.refresh_button, "Synchronisationsjournal neu laden")
        self.design.accessible(
            self.history_table,
            "Synchronisationsjournal",
            "Zeigt Zeitpunkt, Planart, Integrität, Recovery-Verfügbarkeit, Versionen und Hashnachweise.",
        )
        self.design.accessible(
            self.detail_table,
            "Vorher-Nachher-Feldvergleich",
            "Zeigt die gespeicherten Todo- und Kalenderwerte vor und nach dem ausgewählten Commit.",
        )
        self.design.accessible(self.reapply_button, "Neuen RecoveryPlan für den historischen Nachher-Stand prüfen")
        self.design.accessible(self.restore_button, "Neuen RecoveryPlan für den historischen Vorher-Stand prüfen")
        self.design.accessible(self.execute_button, "Nur den zuvor geprüften RecoveryPlan atomar ausführen")
        self.design.accessible(self.status_label, "Journal- und Recovery-Status mit Klartext")

        self.refresh_button.clicked.connect(self.refresh)
        self.link_filter.currentIndexChanged.connect(lambda _index: self.refresh_table())
        self.history_table.itemSelectionChanged.connect(self.select_current)
        self.reapply_button.clicked.connect(
            lambda: self.prepare(RecoveryMode.REAPPLY_AFTER)
        )
        self.restore_button.clicked.connect(
            lambda: self.prepare(RecoveryMode.RESTORE_BEFORE)
        )
        self.execute_button.clicked.connect(self.execute)

        QWidget.setTabOrder(self.link_filter, self.refresh_button)
        QWidget.setTabOrder(self.refresh_button, self.history_table)
        QWidget.setTabOrder(self.history_table, self.detail_table)
        QWidget.setTabOrder(self.detail_table, self.reapply_button)
        QWidget.setTabOrder(self.reapply_button, self.restore_button)
        QWidget.setTabOrder(self.restore_button, self.execute_button)

        self.refresh()

    def refresh(self) -> None:
        current = self.link_filter.currentData()
        rows = self.view_model.rows()
        link_ids = sorted({row.link_id for row in rows})
        self.link_filter.blockSignals(True)
        self.link_filter.clear()
        self.link_filter.addItem("Alle Verknüpfungen", None)
        for link_id in link_ids:
            self.link_filter.addItem(link_id, link_id)
        if current is not None:
            index = self.link_filter.findData(current)
            if index >= 0:
                self.link_filter.setCurrentIndex(index)
        self.link_filter.blockSignals(False)
        self.refresh_table()

    def refresh_table(self) -> None:
        link_id = self.link_filter.currentData()
        rows = self.view_model.rows(link_id)
        self._row_receipts = [row.receipt_id for row in rows]
        self.history_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = (
                row.created_at,
                row.plan_kind,
                row.link_id,
                row.integrity,
                row.recovery_status,
                row.versions,
                row.receipt_hash,
                row.plan_id,
                row.receipt_id,
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setToolTip(str(value))
                self.history_table.setItem(row_index, column, item)
        self.history_table.resizeColumnsToContents()
        if not rows:
            self.detail_table.setRowCount(0)
            self.status_label.setText("Noch keine Synchronisationsnachweise vorhanden.")

    def select_current(self) -> None:
        row = self.history_table.currentRow()
        if row < 0 or row >= len(self._row_receipts):
            return
        try:
            detail = self.view_model.select(self._row_receipts[row])
        except Exception as exc:
            self.status_label.setText(f"Journalnachweis konnte nicht gelesen werden: {exc}")
            return
        self.detail_table.setRowCount(len(detail.fields))
        for row_index, field in enumerate(detail.fields):
            for column, value in enumerate(
                (
                    field.field_id,
                    field.before_todo,
                    field.before_calendar,
                    field.after_todo,
                    field.after_calendar,
                )
            ):
                item = QTableWidgetItem(str(value))
                item.setToolTip(str(value))
                self.detail_table.setItem(row_index, column, item)
        self.detail_table.resizeColumnsToContents()
        record = detail.record
        self.status_label.setText(
            f"{record.integrity.value} – {record.integrity_reason} | "
            f"Receipt {record.receipt_id} | SHA-256 {record.receipt_sha256}"
        )

    def prepare(self, mode: RecoveryMode) -> None:
        if self.view_model.selected is None:
            self.select_current()
        if self.view_model.selected is None:
            self.status_label.setText("Zuerst einen Journalnachweis auswählen.")
            return
        try:
            plan = self.view_model.prepare_recovery(mode)
        except Exception as exc:
            self.status_label.setText(f"RecoveryPlan konnte nicht erstellt werden: {exc}")
            return
        self.status_label.setText(
            f"{plan.state.value} – {plan.blocking_reason} | "
            f"RecoveryPlan {plan.recovery_plan_id} | SHA-256 {plan.recovery_sha256}"
        )

    def execute(self) -> None:
        try:
            receipt = self.view_model.execute_recovery()
        except Exception as exc:
            self.status_label.setText(f"Nicht ausgeführt: {exc}")
            return
        self.status_label.setText(
            f"● GRÜN – BEREIT: Recovery atomar abgeschlossen. "
            f"Neues Audit-Receipt {receipt.receipt_id} | SHA-256 {receipt.receipt_sha256}"
        )
        self.refresh()
