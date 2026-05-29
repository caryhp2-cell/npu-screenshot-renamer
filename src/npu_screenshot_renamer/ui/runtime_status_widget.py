from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

from npu_screenshot_renamer.runtime.status import RuntimeDevice, RuntimeStatus


class RuntimeStatusWidget(QLabel):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("runtimeStatus")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumWidth(108)
        self.set_status(
            RuntimeStatus(
                requested_device=RuntimeDevice.NPU,
                active_device=RuntimeDevice.RULE_ONLY,
                reason="Runtime not checked yet",
            )
        )

    def set_status(self, status: RuntimeStatus) -> None:
        self.setText(status.label)
        self.setToolTip(status.tooltip)
        self.setProperty("severity", status.severity)
        self.style().unpolish(self)
        self.style().polish(self)
