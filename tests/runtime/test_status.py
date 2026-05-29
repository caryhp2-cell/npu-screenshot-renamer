from npu_screenshot_renamer.runtime.status import RuntimeDevice, RuntimeStatus


def test_npu_status_is_neutral():
    status = RuntimeStatus(
        requested_device=RuntimeDevice.NPU,
        active_device=RuntimeDevice.NPU,
        reason="NPU device selected",
    )

    assert status.is_fallback is False
    assert status.label == "NPU active"
    assert status.severity == "neutral"


def test_gpu_fallback_status_is_muted_warning():
    status = RuntimeStatus(
        requested_device=RuntimeDevice.NPU,
        active_device=RuntimeDevice.GPU,
        reason="NPU unavailable; using GPU",
    )

    assert status.is_fallback is True
    assert status.label == "GPU fallback"
    assert status.severity == "muted-warning"


def test_cpu_fallback_status_explains_reason():
    status = RuntimeStatus(
        requested_device=RuntimeDevice.NPU,
        active_device=RuntimeDevice.CPU,
        reason="NPU and GPU unavailable; using CPU",
    )

    assert status.is_fallback is True
    assert status.label == "CPU fallback"
    assert status.tooltip == "NPU and GPU unavailable; using CPU"


def test_rule_only_fallback_status():
    status = RuntimeStatus(
        requested_device=RuntimeDevice.NPU,
        active_device=RuntimeDevice.RULE_ONLY,
        reason="No OpenVINO device available for selected model",
    )

    assert status.is_fallback is True
    assert status.label == "Rule-only fallback"
    assert status.severity == "muted-warning"
