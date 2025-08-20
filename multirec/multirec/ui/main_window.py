"""Graphical user interface for the multistream recorder.

This module defines a `MainWindow` class derived from ``QMainWindow``.  The
window contains a table view listing all currently scheduled and running
recordings and provides buttons to add new streams.  On startup the user is
prompted with a consent dialog to ensure they agree to responsible use.

Note: This is a minimal UI skeleton.  It can be extended to implement the
full specification, including side panels, statistics and theme support.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import List, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QAction,
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from ..config.config import Config
from ..db.database import Database
from ..scheduler.scheduler import Scheduler


class ConsentDialog(QDialog):
    """Dialog asking the user to accept the responsible use terms."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Uso responsable")
        self.resize(400, 200)
        layout = QVBoxLayout(self)
        text = QLabel(
            "Debes aceptar que utilizarás esta aplicación únicamente para grabar contenido"
            " autorizado y respetarás los términos de servicio de las plataformas y las leyes"
            " locales."
        )
        text.setWordWrap(True)
        layout.addWidget(text)
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)


class MainWindow(QMainWindow):
    """Main window for the multistream recorder UI."""

    def __init__(self, config: Config, db: Database) -> None:
        super().__init__()
        self.config = config
        self.db = db
        self.scheduler = Scheduler(config=config, download_dir=config.download_dir)
        self.setWindowTitle("Multirec - Grabador de Streams")
        self.resize(800, 600)

        # Show consent dialog on startup
        accepted = self._show_consent_dialog()
        if not accepted:
            QApplication.instance().quit()
            return

        # Main UI components
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Canal", "Estado", "Archivo"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setCentralWidget(self.table)

        # Toolbar actions
        toolbar = QToolBar("Toolbar")
        self.addToolBar(toolbar)
        add_action = QAction("Agregar stream", self)
        add_action.triggered.connect(self._prompt_add_stream)
        toolbar.addAction(add_action)

        # Periodic update timer to refresh table statuses
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_table)
        self._refresh_timer.start(2000)  # refresh every 2s

        # Start scheduler in background
        self._scheduler_task = asyncio.create_task(self.scheduler.start())

    def closeEvent(self, event) -> None:
        # Cancel scheduler on window close
        asyncio.create_task(self.scheduler.shutdown())
        event.accept()

    def _show_consent_dialog(self) -> bool:
        dialog = ConsentDialog(self)
        return dialog.exec() == QDialog.Accepted

    def _prompt_add_stream(self) -> None:
        # Simple dialog to prompt for URL
        dialog = QDialog(self)
        dialog.setWindowTitle("Agregar stream")
        layout = QFormLayout(dialog)
        url_edit = QLineEdit()
        layout.addRow("URL del canal:", url_edit)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        if dialog.exec() == QDialog.Accepted:
            url = url_edit.text().strip()
            if url:
                asyncio.create_task(self.scheduler.add_recording(url=url))
                # Add row to table
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(url))
                self.table.setItem(row, 1, QTableWidgetItem("EN COLA"))
                self.table.setItem(row, 2, QTableWidgetItem(""))

    def _refresh_table(self) -> None:
        # Refresh table with scheduler status
        i = 0
        # Running tasks
        for task, rec_task in list(self.scheduler.running.items()):
            if i < self.table.rowCount():
                status_item = self.table.item(i, 1)
                file_item = self.table.item(i, 2)
                if status_item:
                    status_item.setText("GRABANDO")
                if file_item and rec_task.result and rec_task.result.file_path:
                    file_item.setText(str(rec_task.result.file_path))
            i += 1
        # Remaining queued tasks
        # For simplicity we set queued tasks as "EN COLA"
        for row in range(i, self.table.rowCount()):
            status_item = self.table.item(row, 1)
            if status_item and status_item.text() != "GRABANDO":
                status_item.setText("EN COLA")