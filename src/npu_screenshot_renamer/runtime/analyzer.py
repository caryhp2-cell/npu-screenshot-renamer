from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from npu_screenshot_renamer.runtime.status import RuntimeStatus


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    image_path: Path
    summary: str
    confidence: float
    runtime_status: RuntimeStatus


def analyze_image_with_status(image_path: Path, runtime_status: RuntimeStatus) -> AnalysisResult:
    return AnalysisResult(
        image_path=image_path,
        summary=f"Rule-based placeholder analysis for {image_path.name}",
        confidence=0.0,
        runtime_status=runtime_status,
    )
