# NPU Screenshot Renamer MVP Runtime Status UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first Python MVP skeleton for NPU Screenshot Renamer with explicit OpenVINO runtime selection and a subtle UI indicator when processing falls back from NPU to GPU or CPU.

**Architecture:** Use a small Python desktop prototype with PySide6 for the UI, OpenVINO runtime probing isolated behind a selector service, and a shared runtime status model consumed by both logs and UI. The UI must show the active inference device without interrupting the user: NPU appears as normal status, while GPU/CPU fallback appears as a low-emphasis warning badge or status row.

**Tech Stack:** Python 3.11+, PySide6, OpenVINO, pytest, watchdog, SQLite.

---

## File Structure

- `pyproject.toml`: Project metadata, dependencies, pytest configuration, console entry point.
- `src/npu_screenshot_renamer/__init__.py`: Package marker and version.
- `src/npu_screenshot_renamer/app.py`: Application bootstrap.
- `src/npu_screenshot_renamer/runtime/status.py`: Runtime device enum and immutable status object.
- `src/npu_screenshot_renamer/runtime/device_selector.py`: OpenVINO device discovery and NPU -> GPU -> CPU fallback selection.
- `src/npu_screenshot_renamer/runtime/analyzer.py`: Thin analyzer boundary that records which runtime is used for an image analysis job.
- `src/npu_screenshot_renamer/ui/main_window.py`: Main PySide6 window with settings/status placeholders and runtime status indicator.
- `src/npu_screenshot_renamer/ui/runtime_status_widget.py`: Compact widget that displays NPU/GPU/CPU/fallback state.
- `tests/runtime/test_device_selector.py`: Unit tests for fallback selection.
- `tests/runtime/test_status.py`: Unit tests for status text and severity.
- `tests/ui/test_runtime_status_widget.py`: Widget tests for subtle fallback display.

## Runtime Status UX Requirement

The UI must always make the selected runtime visible, but it should not dominate the app.

Display rules:

- NPU active: show `NPU active` with neutral styling.
- GPU fallback: show `GPU fallback` with muted amber styling and tooltip/reason text such as `NPU unavailable; using GPU`.
- CPU fallback: show `CPU fallback` with muted amber styling and tooltip/reason text such as `NPU and GPU unavailable; using CPU`.
- Rule-only fallback: show `Rule-only fallback` with muted amber styling and tooltip/reason text such as `No OpenVINO device available for selected model`.

This status should appear in the main status area and diagnostics view. It should not block processing and should not show modal dialogs.

---

### Task 1: Project Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `src/npu_screenshot_renamer/__init__.py`
- Create: `src/npu_screenshot_renamer/app.py`
- Test: `tests/test_package_import.py`

- [ ] **Step 1: Write the import smoke test**

Create `tests/test_package_import.py`:

```python
def test_package_imports():
    import npu_screenshot_renamer

    assert npu_screenshot_renamer.__version__ == "0.1.0"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
pytest tests/test_package_import.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'npu_screenshot_renamer'`.

- [ ] **Step 3: Add project metadata and package files**

Create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "npu-screenshot-renamer"
version = "0.1.0"
description = "Local Windows screenshot renamer with OpenVINO NPU-first analysis."
requires-python = ">=3.11"
dependencies = [
  "openvino>=2025.0.0",
  "PySide6>=6.7.0",
  "watchdog>=4.0.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0.0",
  "pytest-qt>=4.4.0",
]

[project.scripts]
npu-screenshot-renamer = "npu_screenshot_renamer.app:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

Create `src/npu_screenshot_renamer/__init__.py`:

```python
__version__ = "0.1.0"
```

Create `src/npu_screenshot_renamer/app.py`:

```python
from __future__ import annotations


def main() -> int:
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run import test**

Run:

```powershell
pytest tests/test_package_import.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add pyproject.toml src/npu_screenshot_renamer/__init__.py src/npu_screenshot_renamer/app.py tests/test_package_import.py
git commit -m "chore: scaffold python mvp package"
```

---

### Task 2: Runtime Status Model

**Files:**
- Create: `src/npu_screenshot_renamer/runtime/__init__.py`
- Create: `src/npu_screenshot_renamer/runtime/status.py`
- Test: `tests/runtime/test_status.py`

- [ ] **Step 1: Write status behavior tests**

Create `tests/runtime/test_status.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
pytest tests/runtime/test_status.py -v
```

Expected: FAIL with `ModuleNotFoundError` for `npu_screenshot_renamer.runtime`.

- [ ] **Step 3: Implement status model**

Create `src/npu_screenshot_renamer/runtime/__init__.py`:

```python
from npu_screenshot_renamer.runtime.status import RuntimeDevice, RuntimeStatus

__all__ = ["RuntimeDevice", "RuntimeStatus"]
```

Create `src/npu_screenshot_renamer/runtime/status.py`:

```python
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
```

- [ ] **Step 4: Run status tests**

Run:

```powershell
pytest tests/runtime/test_status.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/npu_screenshot_renamer/runtime tests/runtime/test_status.py
git commit -m "feat: add runtime status model"
```

---

### Task 3: OpenVINO Device Selector

**Files:**
- Create: `src/npu_screenshot_renamer/runtime/device_selector.py`
- Test: `tests/runtime/test_device_selector.py`

- [ ] **Step 1: Write fallback selection tests**

Create `tests/runtime/test_device_selector.py`:

```python
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
```

- [ ] **Step 2: Run selector tests to verify they fail**

Run:

```powershell
pytest tests/runtime/test_device_selector.py -v
```

Expected: FAIL with `ModuleNotFoundError` for `device_selector`.

- [ ] **Step 3: Implement deterministic selector**

Create `src/npu_screenshot_renamer/runtime/device_selector.py`:

```python
from __future__ import annotations

from collections.abc import Iterable

from npu_screenshot_renamer.runtime.status import RuntimeDevice, RuntimeStatus


def select_runtime_status(available_devices: Iterable[str]) -> RuntimeStatus:
    normalized = {device.upper() for device in available_devices}

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
```

- [ ] **Step 4: Add OpenVINO probing function**

Append to `src/npu_screenshot_renamer/runtime/device_selector.py`:

```python
def discover_openvino_devices() -> list[str]:
    try:
        from openvino import Core
    except ImportError:
        return []

    core = Core()
    return list(core.available_devices)


def select_current_runtime_status() -> RuntimeStatus:
    return select_runtime_status(discover_openvino_devices())
```

- [ ] **Step 5: Run selector tests**

Run:

```powershell
pytest tests/runtime/test_device_selector.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add src/npu_screenshot_renamer/runtime/device_selector.py tests/runtime/test_device_selector.py
git commit -m "feat: add openvino runtime fallback selector"
```

---

### Task 4: Runtime Status Widget

**Files:**
- Create: `src/npu_screenshot_renamer/ui/__init__.py`
- Create: `src/npu_screenshot_renamer/ui/runtime_status_widget.py`
- Test: `tests/ui/test_runtime_status_widget.py`

- [ ] **Step 1: Write widget tests**

Create `tests/ui/test_runtime_status_widget.py`:

```python
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
```

- [ ] **Step 2: Run widget tests to verify they fail**

Run:

```powershell
pytest tests/ui/test_runtime_status_widget.py -v
```

Expected: FAIL with `ModuleNotFoundError` for `npu_screenshot_renamer.ui`.

- [ ] **Step 3: Implement compact runtime status widget**

Create `src/npu_screenshot_renamer/ui/__init__.py`:

```python
from npu_screenshot_renamer.ui.runtime_status_widget import RuntimeStatusWidget

__all__ = ["RuntimeStatusWidget"]
```

Create `src/npu_screenshot_renamer/ui/runtime_status_widget.py`:

```python
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
```

- [ ] **Step 4: Run widget tests**

Run:

```powershell
pytest tests/ui/test_runtime_status_widget.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/npu_screenshot_renamer/ui tests/ui/test_runtime_status_widget.py
git commit -m "feat: add subtle runtime status widget"
```

---

### Task 5: Main Window With Low-Emphasis Fallback Indicator

**Files:**
- Create: `src/npu_screenshot_renamer/ui/main_window.py`
- Modify: `src/npu_screenshot_renamer/app.py`

- [ ] **Step 1: Implement main window layout**

Create `src/npu_screenshot_renamer/ui/main_window.py`:

```python
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
```

- [ ] **Step 2: Wire application bootstrap**

Replace `src/npu_screenshot_renamer/app.py` with:

```python
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from npu_screenshot_renamer.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Manually verify fallback display**

Run:

```powershell
python -m npu_screenshot_renamer.app
```

Expected:

- App opens.
- Bottom status row shows `Runtime`.
- If OpenVINO reports NPU, badge says `NPU active`.
- If NPU is unavailable and GPU is available, badge says `GPU fallback`.
- If only CPU is available, badge says `CPU fallback`.
- The fallback badge is visible but low-emphasis: no dialog, no blocking, no large warning banner.

- [ ] **Step 4: Commit**

```powershell
git add src/npu_screenshot_renamer/app.py src/npu_screenshot_renamer/ui/main_window.py
git commit -m "feat: show runtime fallback status in ui"
```

---

### Task 6: Analyzer Boundary Records Runtime Used

**Files:**
- Create: `src/npu_screenshot_renamer/runtime/analyzer.py`
- Test: `tests/runtime/test_analyzer.py`

- [ ] **Step 1: Write analyzer status test**

Create `tests/runtime/test_analyzer.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
pytest tests/runtime/test_analyzer.py -v
```

Expected: FAIL with `ModuleNotFoundError` for `analyzer`.

- [ ] **Step 3: Implement analyzer boundary**

Create `src/npu_screenshot_renamer/runtime/analyzer.py`:

```python
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
```

- [ ] **Step 4: Run analyzer test**

Run:

```powershell
pytest tests/runtime/test_analyzer.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/npu_screenshot_renamer/runtime/analyzer.py tests/runtime/test_analyzer.py
git commit -m "feat: record runtime used during analysis"
```

---

### Task 7: Verification And Documentation Update

**Files:**
- Modify: `docs/superpowers/specs/2026-05-29-npu-screenshot-renamer-design.md`

- [ ] **Step 1: Run focused tests**

Run:

```powershell
pytest tests/runtime tests/ui tests/test_package_import.py -v
```

Expected: PASS.

- [ ] **Step 2: Update design spec UI requirement**

In `docs/superpowers/specs/2026-05-29-npu-screenshot-renamer-design.md`, add this bullet under `## 9. User Interface` after the required screens list:

```markdown
Runtime status should be visible but low-emphasis. When NPU is active, the UI may show a neutral `NPU active` indicator. When inference falls back to GPU, CPU, or rule-only naming, the UI should show a subtle status badge or diagnostics row such as `GPU fallback` or `CPU fallback`, including a short reason in tooltip or diagnostics text. This indicator must not block automatic renaming.
```

- [ ] **Step 3: Manually verify app startup**

Run:

```powershell
python -m npu_screenshot_renamer.app
```

Expected:

- Window opens.
- Runtime status badge is visible.
- Fallback state is understandable without being visually loud.

- [ ] **Step 4: Commit**

```powershell
git add docs/superpowers/specs/2026-05-29-npu-screenshot-renamer-design.md
git commit -m "docs: specify subtle runtime fallback indicator"
```

---

## Self-Review

Spec coverage:

- NPU-first fallback path is covered by Task 3.
- UI visibility for GPU/CPU fallback is covered by Tasks 4, 5, and 7.
- Runtime used is preserved for future history/logging by Task 6.
- Batch rename, folder watching, collision-safe rename, SQLite history, undo, OCR, and final OpenVINO model integration remain outside this first plan and should become separate plans after the runtime/UI spine is in place.

Placeholder scan:

- No `TBD`, `TODO`, or vague edge-case steps are used.
- Each code-writing step includes concrete file contents or exact text to add.

Type consistency:

- `RuntimeDevice`, `RuntimeStatus`, `RuntimeStatusWidget`, `select_runtime_status`, and `AnalysisResult` are defined before later tasks use them.
