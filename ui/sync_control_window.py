from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services.resolution_service import ResolutionService
from services.sync_service import SynchronizationService
from sync_core.model import FieldChangeState, SyncPlanState
from sync_core.resolution import ResolutionChoice
from ui.design import DesignSystem, DesignTokens
from viewmodel.sync_control_query import SyncControlQuery
from viewmodel.sync_control_viewmodel import SyncControlViewModel


CHOICE_TEXT = {
    ResolutionChoice.KEEP_BLOCKED: "Blockiert lassen",
    ResolutionChoice.TODO_VALUE: "Todo-Wert übernehmen",
    ResolutionChoice.CALENDAR_VALUE: "Kalender-Wert übernehmen",
}

COLUMNS = (
    "Feld",
    "Baseline",
    "Todo",
    "Kalender",
    "Zustand",
    "Geplante Aktion",
    "Grund",
    "Versionsstatus",
    "Hashstatus",
    "Entscheidung",
)


class SyncControlWindow(QMainWindow):
    def __init__(
        self,
        sync_service: SynchronizationService,
        resolution_service: ResolutionService,
        *,
        repo_root: Path,
    ) -> None:
        super().__init__()
        self.repo_root = Path(repo_root)
        self.tokens = DesignTokens.from_repository(self.repo_root)
        self.design = DesignSystem(QApplication.instance(), self.tokens)
        self.view_model = SyncControlViewModel(
            SyncControlQuery(sync_service),
            sync_service,
            resolution_service,
        )
        self._decision_widgets: dict[str, QComboBox] = {}

        self.setWindowTitle("PROVOWARE PLANER – Synchronisationskontrolle")
        self.setMinimumSize(900, 600)
        self.resize(1500, 780)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        self.design.configure_layout(root)

        intro = QLabel(
            "Diese Ansicht zeigt nur den qualifizierten Synchronisationskern. "
            "Echte Feldkonflikte werden niemals automatisch entschieden."
        )
        intro.setWordWrap(True)
        root.addWidget(intro)

        selector = QHBoxLayout()
        selector.setSpacing(self.design.spacing("S"))
        selector.addWidget(QLabel("Verknüpfung"))
        self.link_combo = QComboBox()
        self.refresh_links_button = QPushButton("Verknüpfungen laden")
        self.inspect_button = QPushButton("Prüfen")
        selector.addWidget(self.link_combo, 1)
        selector.addWidget(self.refresh_links_button)
        selector.addWidget(self.inspect_button)
        root.addLayout(selector)

        actions = QHBoxLayout()
        actions.setSpacing(self.design.spacing("S"))
        self.plan_button = QPushButton("Entscheidungsplan prüfen")
        self.execute_button = QPushButton("Atomar ausführen")
        actions.addWidget(self.plan_button)
        actions.addWidget(self.execute_button)
        actions.addStretch(1)
        root.addLayout(actions)

        self.status_label = QLabel("Noch keine Verknüpfung geprüft.")
        self.status_label.setWordWrap(True)
        self.status_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        root.addWidget(self.status_label)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        root.addWidget(self.table, 1)

        self.receipt_label = QLabel("Noch kein Audit-Receipt erzeugt.")
        self.receipt_label.setWordWrap(True)
        self.receipt_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        root.addWidget(self.receipt_label)

        self.design.accessible(self.link_combo, "Synchronisations-Verknüpfung auswählen")
        self.design.accessible(self.refresh_links_button, "Verknüpfungsliste neu laden")
        self.design.accessible(self.inspect_button, "Synchronisationsplan read-only prüfen")
        self.design.accessible(self.plan_button, "Explizite Konfliktentscheidungen als neuen ResolutionPlan prüfen")
        self.design.accessible(self.execute_button, "Freigegebenen Synchronisationsplan atomar ausführen")
        self.design.accessible(
            self.table,
            "Synchronisations-Feldtabelle",
            "Zeigt Baseline, Todo, Kalender, Zustand, Aktion, Grund, Versionen, Hashstatus und explizite Entscheidung.",
        )
        self.design.accessible(self.status_label, "Synchronisationsstatus mit Klartext")
        self.design.accessible(self.receipt_label, "Letztes Audit-Receipt")

        self.refresh_links_button.clicked.connect(self.refresh_links)
        self.inspect_button.clicked.connect(self.inspect)
        self.plan_button.clicked.connect(self.preview_resolution)
        self.execute_button.clicked.connect(self.execute)

        QWidget.setTabOrder(self.link_combo, self.refresh_links_button)
        QWidget.setTabOrder(self.refresh_links_button, self.inspect_button)
        QWidget.setTabOrder(self.inspect_button, self.plan_button)
        QWidget.setTabOrder(self.plan_button, self.execute_button)
        QWidget.setTabOrder(self.execute_button, self.table)

        self.refresh_links()

    def refresh_links(self) -> None:
        current = self.link_combo.currentText()
        self.link_combo.clear()
        for link_id in self.view_model.link_ids():
            self.link_combo.addItem(link_id)
        if current:
            index = self.link_combo.findText(current)
            if index >= 0:
                self.link_combo.setCurrentIndex(index)
        if self.link_combo.count() == 0:
            self.status_label.setText("Keine aktive Todo-Kalender-Verknüpfung vorhanden.")
            self.table.setRowCount(0)

    def inspect(self) -> None:
        link_id = self.link_combo.currentText().strip()
        if not link_id:
            self.status_label.setText("Keine Verknüpfung ausgewählt.")
            return
        try:
            snapshot = self.view_model.load(link_id)
        except Exception as exc:
            self.status_label.setText(f"Prüfung fehlgeschlagen: {exc}")
            return
        self._render(snapshot)
        self.status_label.setText(
            f"{snapshot.plan.state.value} – {snapshot.plan.blocking_reason} | {snapshot.version_status}"
        )

    def _render(self, snapshot) -> None:
        self._decision_widgets.clear()
        self.table.setRowCount(len(snapshot.rows))
        plan_fields = {field.field_id: field for field in snapshot.plan.fields}
        for row_index, row in enumerate(snapshot.rows):
            values = (
                row.field_id,
                row.baseline_text,
                row.todo_text,
                row.calendar_text,
                row.state_text,
                row.action_text,
                row.reason,
                row.version_status,
                row.hash_status,
            )
            for column, text in enumerate(values):
                item = QTableWidgetItem(str(text))
                item.setToolTip(str(text))
                self.table.setItem(row_index, column, item)

            field = plan_fields[row.field_id]
            if field.state is FieldChangeState.BOTH_DIFFERENT:
                combo = QComboBox()
                for choice in (
                    ResolutionChoice.KEEP_BLOCKED,
                    ResolutionChoice.TODO_VALUE,
                    ResolutionChoice.CALENDAR_VALUE,
                ):
                    combo.addItem(CHOICE_TEXT[choice], choice)
                combo.setCurrentIndex(0)
                combo.setAccessibleName(f"Entscheidung für Konfliktfeld {row.field_id}")
                combo.currentIndexChanged.connect(
                    lambda _index, field_id=row.field_id, widget=combo: self._decision_changed(field_id, widget)
                )
                self.table.setCellWidget(row_index, 9, combo)
                self._decision_widgets[row.field_id] = combo
            else:
                self.table.setItem(row_index, 9, QTableWidgetItem("Nicht erforderlich"))
        self.table.resizeColumnsToContents()

    def _decision_changed(self, field_id: str, combo: QComboBox) -> None:
        choice = combo.currentData()
        if isinstance(choice, ResolutionChoice):
            self.view_model.choose(field_id, choice)
            self.status_label.setText(
                f"Entscheidung vorgemerkt für {field_id}: {CHOICE_TEXT[choice]}. "
                "Noch wurde nichts geschrieben."
            )

    def preview_resolution(self) -> None:
        if self.view_model.snapshot is None:
            self.inspect()
        if self.view_model.snapshot is None:
            return
        if self.view_model.snapshot.plan.state is not SyncPlanState.BLOCKED_CONFLICT:
            self.status_label.setText(
                f"Kein BOTH_DIFFERENT-Konflikt: {self.view_model.snapshot.plan.state.value}. "
                "Ein ResolutionPlan ist nicht erforderlich."
            )
            return
        try:
            plan = self.view_model.prepare_resolution()
        except Exception as exc:
            self.status_label.setText(f"Entscheidungsplan konnte nicht erstellt werden: {exc}")
            return
        self.status_label.setText(
            f"{plan.state.value} – {plan.blocking_reason} | ResolutionPlan {plan.resolution_plan_id} | "
            f"SHA-256 {plan.resolution_sha256}"
        )

    def execute(self) -> None:
        if self.view_model.snapshot is None:
            self.inspect()
        if self.view_model.snapshot is None:
            return
        try:
            receipt = self.view_model.execute()
        except Exception as exc:
            self.status_label.setText(f"Nicht ausgeführt: {exc}")
            return
        self.receipt_label.setText(
            f"Audit-Receipt {receipt.receipt_id} | Plan {receipt.plan_id} | "
            f"SHA-256 {receipt.receipt_sha256} | COMMITTED"
        )
        self.status_label.setText("● GRÜN – BEREIT: Synchronisation atomar abgeschlossen und nachgeprüft.")
        self.inspect()
