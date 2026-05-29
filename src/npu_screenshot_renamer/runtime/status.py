from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RuntimeDevice(StrEnum):
    NPU = "NPU"
    GPU = "GPU"
    CPU = "CPU"
    RULE_ONLY = "RULE_ONLY"


@dataclass(frozen=True, slots=True)
class RuntimeStatus:
    requested_device: RuntimeDevice
    active_device: RuntimeDevice
    reason: str

    @property
    def is_fallback(self) -> bool:
        return self.active_device != self.requested_device

    @property
    def label(self) -> str:
        if self.active_device == RuntimeDevice.NPU and not self.is_fallback:
            return "NPU active"
        if self.active_device == RuntimeDevice.RULE_ONLY:
            return "Rule-only fallback"
        return f"{self.active_device.value} fallback"

    @property
    def severity(self) -> str:
        return "muted-warning" if self.is_fallback else "neutral"

    @property
    def tooltip(self) -> str:
        return self.reason
