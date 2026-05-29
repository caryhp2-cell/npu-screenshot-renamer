from npu_screenshot_renamer.runtime.status import RuntimeDevice, RuntimeStatus
from npu_screenshot_renamer.ui.runtime_status_widget import RuntimeStatusWidget


def test_widget_shows_neutral_npu_status(qtbot):
    widget = RuntimeStatusWidget()
    qtbot.addWidget(widget)

    widget.set_status(
        RuntimeStatus(
            requested_device=RuntimeDevice.NPU,
            active_device=RuntimeDevice.NPU,
            reason="NPU device selected",
        )
    )

    assert widget.text() == "NPU active"
    assert widget.property("severity") == "neutral"


def test_widget_shows_subtle_gpu_fallback_status(qtbot):
    widget = RuntimeStatusWidget()
    qtbot.addWidget(widget)

    widget.set_status(
        RuntimeStatus(
            requested_device=RuntimeDevice.NPU,
            active_device=RuntimeDevice.GPU,
            reason="NPU unavailable; using GPU",
        )
    )

    assert widget.text() == "GPU fallback"
    assert widget.toolTip() == "NPU unavailable; using GPU"
    assert widget.property("severity") == "muted-warning"
