from __future__ import annotations

from collections.abc import Iterable

from npu_screenshot_renamer.runtime.status import RuntimeDevice, RuntimeStatus


def select_runtime_status(available_devices: Iterable[str]) -> RuntimeStatus:
    normalized = {device.upper().split(".", maxsplit=1)[0] for device in available_devices}

    if "NPU" in normalized:
        return RuntimeStatus(
            requested_device=RuntimeDevice.NPU,
            active_device=RuntimeDevice.NPU,
            reason="NPU device selected",
        )

    if "GPU" in normalized:
        return RuntimeStatus(
            requested_device=RuntimeDevice.NPU,
            active_device=RuntimeDevice.GPU,
            reason="NPU unavailable; using GPU",
        )

    if "CPU" in normalized:
        return RuntimeStatus(
            requested_device=RuntimeDevice.NPU,
            active_device=RuntimeDevice.CPU,
            reason="NPU and GPU unavailable; using CPU",
        )

    return RuntimeStatus(
        requested_device=RuntimeDevice.NPU,
        active_device=RuntimeDevice.RULE_ONLY,
        reason="No OpenVINO device available for selected model",
    )


def discover_openvino_devices() -> list[str]:
    try:
        from openvino import Core
    except ImportError:
        return []

    core = Core()
    return list(core.available_devices)


def select_current_runtime_status() -> RuntimeStatus:
    return select_runtime_status(discover_openvino_devices())
