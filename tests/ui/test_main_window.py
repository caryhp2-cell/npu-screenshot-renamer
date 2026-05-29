from PySide6.QtWidgets import QLabel

from npu_screenshot_renamer.runtime.status import RuntimeDevice, RuntimeStatus
from npu_screenshot_renamer.ui.main_window import MainWindow
from npu_screenshot_renamer.ui.runtime_status_widget import RuntimeStatusWidget


def test_main_window_shows_low_emphasis_runtime_fallback(monkeypatch, qtbot):
    monkeypatch.setattr(
        "npu_screenshot_renamer.ui.main_window.select_current_runtime_status",
        lambda: RuntimeStatus(
            requested_device=RuntimeDevice.NPU,
            active_device=RuntimeDevice.GPU,
            reason="NPU unavailable; using GPU",
        ),
    )

    window = MainWindow()
    qtbot.addWidget(window)

    runtime_status = window.findChild(RuntimeStatusWidget, "runtimeStatus")
    assert runtime_status is not None
    assert runtime_status.text() == "GPU fallback"
    assert runtime_status.property("severity") == "muted-warning"
    assert runtime_status.toolTip() == "NPU unavailable; using GPU"

    labels = [label.text() for label in window.findChildren(QLabel)]
    assert "Runtime" in labels

    assert "muted-warning" in window.centralWidget().styleSheet()
