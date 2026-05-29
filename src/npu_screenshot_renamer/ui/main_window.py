from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from npu_screenshot_renamer.runtime.device_selector import select_current_runtime_status
from npu_screenshot_renamer.ui.runtime_status_widget import RuntimeStatusWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("NPU Screenshot Renamer")
        self.resize(760, 420)

        self.runtime_status = RuntimeStatusWidget()
        self.runtime_status.set_status(select_current_runtime_status())

        folder_input = QLineEdit()
        folder_input.setPlaceholderText("Screenshot folder")

        browse_button = QPushButton("Browse")
        batch_checkbox = QCheckBox("Process existing files")
        watch_checkbox = QCheckBox("Watch new screenshots")

        folder_row = QHBoxLayout()
        folder_row.addWidget(folder_input, 1)
        folder_row.addWidget(browse_button)

        status_row = QHBoxLayout()
        status_row.addWidget(QLabel("Runtime"))
        status_row.addWidget(self.runtime_status)
        status_row.addStretch(1)

        layout = QVBoxLayout()
        layout.addLayout(folder_row)
        layout.addWidget(batch_checkbox)
        layout.addWidget(watch_checkbox)
        layout.addStretch(1)
        layout.addLayout(status_row)

        root = QWidget()
        root.setLayout(layout)
        root.setStyleSheet(
            """
            QLabel#runtimeStatus {
                border: 1px solid #d0d5dd;
                border-radius: 6px;
                padding: 3px 8px;
                color: #344054;
                background: #f9fafb;
            }
            QLabel#runtimeStatus[severity="muted-warning"] {
                border-color: #e4c767;
                color: #7a5d00;
                background: #fff8db;
            }
            """
        )

        self.setCentralWidget(root)
