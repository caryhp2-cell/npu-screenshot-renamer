from npu_screenshot_renamer.runtime.device_selector import select_runtime_status
from npu_screenshot_renamer.runtime.status import RuntimeDevice


def test_selects_npu_when_available():
    status = select_runtime_status(["CPU", "GPU", "NPU"])

    assert status.active_device == RuntimeDevice.NPU
    assert status.reason == "NPU device selected"


def test_falls_back_to_gpu_when_npu_missing():
    status = select_runtime_status(["CPU", "GPU"])

    assert status.active_device == RuntimeDevice.GPU
    assert status.reason == "NPU unavailable; using GPU"


def test_falls_back_to_cpu_when_only_cpu_available():
    status = select_runtime_status(["CPU"])

    assert status.active_device == RuntimeDevice.CPU
    assert status.reason == "NPU and GPU unavailable; using CPU"


def test_falls_back_to_rule_only_when_no_supported_device_available():
    status = select_runtime_status([])

    assert status.active_device == RuntimeDevice.RULE_ONLY
    assert status.reason == "No OpenVINO device available for selected model"
