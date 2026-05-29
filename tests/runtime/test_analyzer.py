from pathlib import Path

from npu_screenshot_renamer.runtime.analyzer import AnalysisResult, analyze_image_with_status
from npu_screenshot_renamer.runtime.status import RuntimeDevice, RuntimeStatus


def test_analysis_result_records_runtime_status():
    status = RuntimeStatus(
        requested_device=RuntimeDevice.NPU,
        active_device=RuntimeDevice.CPU,
        reason="NPU and GPU unavailable; using CPU",
    )

    result = analyze_image_with_status(Path("sample.png"), status)

    assert isinstance(result, AnalysisResult)
    assert result.runtime_status.active_device == RuntimeDevice.CPU
    assert result.summary == "Rule-based placeholder analysis for sample.png"
    assert result.confidence == 0.0
