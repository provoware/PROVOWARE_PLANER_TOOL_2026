from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHeaderView,
    QLabel,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services.diagnostics_service import DiagnosticsService
from ui.design import DesignSystem, DesignTokens
from viewmodel.diagnostics_viewmodel import DiagnosticsViewModel


class DiagnosticsWindow(QMainWindow):
    """I012: rein lesende Diagnose-/Recovery-Zentrale."""

    def __init__(self, service: DiagnosticsService, *, repo_root: Path) -> None:
        super().__init__()
        app = QApplication.instance()
        if app is None:
            raise RuntimeError("QApplication fehlt")
        self.design = DesignSystem(app, DesignTokens.from_repository(repo_root))
        self.viewmodel = DiagnosticsViewModel(service)
        self.setWindowTitle("PROVOWARE – Diagnose- und Recovery-Zentrale")
        self.resize(1120, 720)
        self.setMinimumSize(900, 600)

        root = QWidget(self)
        layout = QVBoxLayout(root)
        self.design.configure_layout(layout, spacing="M", margins="M")

        self.title_label = QLabel("Diagnose- und Recovery-Zentrale")
        self.title_label.setObjectName("diagnosticsTitle")
        self.title_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.title_label.setAccessibleName("Titel Diagnosezentrale")
        layout.addWidget(self.title_label)

        self.overall_label = QLabel()
        self.overall_label.setObjectName("diagnosticsOverall")
        self.overall_label.setAccessibleName("Gesamtzustand")
        layout.addWidget(self.overall_label)

        self.time_label = QLabel()
        self.time_label.setAccessibleName("Prüfzeitpunkt")
        layout.addWidget(self.time_label)

        self.refresh_button = QPushButton("Erneut prüfen")
        self.design.accessible(
            self.refresh_button,
            "Diagnose erneut prüfen",
            "Liest vorhandene Nachweise neu ein. Es werden keine Reparaturen oder Nutzdatenänderungen ausgeführt.",
        )
        self.refresh_button.clicked.connect(self.refresh)
        layout.addWidget(self.refresh_button)

        self.table = QTableWidget(0, 5, root)
        self.table.setHorizontalHeaderLabels(("Bereich", "Zustand", "Kurzinfo", "Details", "Anzahl"))
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setWordWrap(True)
        self.table.setAccessibleName("Diagnoseergebnisse")
        self.table.setAccessibleDescription(
            "Read-only Übersicht über Startzustand, Datenbank, Journal, Sicherungen und Recovery-Pläne."
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        layout.addWidget(self.table, 1)

        self.note_label = QLabel(
            "Diese Ansicht prüft nur. Blockierte Recovery-Pläne werden nicht automatisch ausgeführt; "
            "Reparaturen bleiben ausschließlich den bereits qualifizierten Fachpfaden vorbehalten."
        )
        self.note_label.setWordWrap(True)
        self.note_label.setAccessibleName("Sicherheitshinweis")
        layout.addWidget(self.note_label)

        self.setCentralWidget(root)
        self.refresh()

    def refresh(self) -> None:
        snapshot = self.viewmodel.load()
        self.overall_label.setText(snapshot.overall_text)
        self.time_label.setText(f"Geprüft: {snapshot.generated_text}")
        self.table.setRowCount(len(snapshot.rows))
        for row_index, row in enumerate(snapshot.rows):
            values = (row.area, row.state_text, row.summary, row.details, row.count_text)
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row_index, column, item)
        self.table.resizeRowsToContents()
        self.design.fit_text_controls(self)
