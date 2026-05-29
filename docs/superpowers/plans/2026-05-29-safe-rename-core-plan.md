# Safe Rename Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a pure, tested filename-generation core that creates safe screenshot filenames with date prefixes, fallback names, supported extensions, existing-pattern detection, and collision-safe suffixes.

**Architecture:** Add a focused `npu_screenshot_renamer.naming` package with pure functions and small immutable input dataclasses. This slice does not touch files on disk, UI state, folder watching, history, or OpenVINO inference; future batch/watch services will call this module before performing actual filesystem rename operations.

**Tech Stack:** Python 3.11+, dataclasses, pathlib, datetime, pytest.

---

## File Structure

- `src/npu_screenshot_renamer/naming/__init__.py`: Public exports for naming helpers and dataclasses.
- `src/npu_screenshot_renamer/naming/safe_filename.py`: Pure Safe Rename Core implementation.
- `tests/naming/test_safe_filename.py`: Unit tests for timestamp choice, slug generation, fallback names, extension validation, app-pattern detection, collision handling, and final filename generation.
- `README.md`: Update current status and project structure to mention Safe Rename Core.

---

### Task 1: Naming Package And Timestamp Helpers

**Files:**
- Create: `src/npu_screenshot_renamer/naming/__init__.py`
- Create: `src/npu_screenshot_renamer/naming/safe_filename.py`
- Test: `tests/naming/test_safe_filename.py`

- [ ] **Step 1: Write failing timestamp and extension tests**

Create `tests/naming/test_safe_filename.py`:

```python
from datetime import datetime

import pytest

from npu_screenshot_renamer.naming.safe_filename import (
    FileTimestamps,
    choose_timestamp,
    date_prefix,
    is_supported_image_extension,
)


def dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def test_choose_timestamp_prefers_plausible_creation_time():
    timestamps = FileTimestamps(
        created_at=dt("2026-05-28T12:30:00"),
        modified_at=dt("2026-05-29T13:45:00"),
        now=dt("2026-05-30T09:00:00"),
    )

    assert choose_timestamp(timestamps) == dt("2026-05-28T12:30:00")


def test_choose_timestamp_uses_modified_time_when_creation_is_implausible():
    timestamps = FileTimestamps(
        created_at=dt("1999-12-31T23:59:00"),
        modified_at=dt("2026-05-29T13:45:00"),
        now=dt("2026-05-30T09:00:00"),
    )

    assert choose_timestamp(timestamps) == dt("2026-05-29T13:45:00")


def test_choose_timestamp_uses_now_when_file_times_are_missing_or_implausible():
    timestamps = FileTimestamps(
        created_at=None,
        modified_at=dt("2099-01-01T00:00:00"),
        now=dt("2026-05-30T09:00:00"),
    )

    assert choose_timestamp(timestamps) == dt("2026-05-30T09:00:00")


def test_date_prefix_formats_calendar_date():
    assert date_prefix(dt("2026-05-29T13:45:00")) == "2026-05-29"


@pytest.mark.parametrize("extension", [".png", ".jpg", ".jpeg", ".webp", ".PNG", "JPG"])
def test_supported_image_extensions_are_case_insensitive(extension):
    assert is_supported_image_extension(extension) is True


@pytest.mark.parametrize("extension", [".bmp", ".gif", ".txt", ""])
def test_unsupported_image_extensions_are_rejected(extension):
    assert is_supported_image_extension(extension) is False
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest tests/naming/test_safe_filename.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'npu_screenshot_renamer.naming'`.

- [ ] **Step 3: Implement minimal package and helpers**

Create `src/npu_screenshot_renamer/naming/__init__.py`:

```python
from npu_screenshot_renamer.naming.safe_filename import (
    FileTimestamps,
    NamingInput,
    choose_collision_safe_name,
    choose_timestamp,
    date_prefix,
    fallback_topic,
    generate_safe_filename,
    is_app_named_file,
    is_supported_image_extension,
    slugify_topic,
)

__all__ = [
    "FileTimestamps",
    "NamingInput",
    "choose_collision_safe_name",
    "choose_timestamp",
    "date_prefix",
    "fallback_topic",
    "generate_safe_filename",
    "is_app_named_file",
    "is_supported_image_extension",
    "slugify_topic",
]
```

Create `src/npu_screenshot_renamer/naming/safe_filename.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


SUPPORTED_IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp"})


@dataclass(frozen=True, slots=True)
class FileTimestamps:
    created_at: datetime | None
    modified_at: datetime | None
    now: datetime


@dataclass(frozen=True, slots=True)
class NamingInput:
    source_path: Path
    topic: str | None
    confidence: float
    timestamps: FileTimestamps
    max_topic_length: int = 80
    confidence_threshold: float = 0.50


def _is_plausible_timestamp(value: datetime | None, now: datetime) -> bool:
    return value is not None and 2000 <= value.year <= now.year + 1


def choose_timestamp(timestamps: FileTimestamps) -> datetime:
    if _is_plausible_timestamp(timestamps.created_at, timestamps.now):
        return timestamps.created_at
    if _is_plausible_timestamp(timestamps.modified_at, timestamps.now):
        return timestamps.modified_at
    return timestamps.now


def date_prefix(timestamp: datetime) -> str:
    return timestamp.strftime("%Y-%m-%d")


def is_supported_image_extension(extension: str) -> bool:
    normalized = extension.lower()
    if normalized and not normalized.startswith("."):
        normalized = f".{normalized}"
    return normalized in SUPPORTED_IMAGE_EXTENSIONS


def slugify_topic(topic: str, max_length: int = 80) -> str:
    raise NotImplementedError


def fallback_topic(timestamp: datetime) -> str:
    raise NotImplementedError


def is_app_named_file(filename: str) -> bool:
    raise NotImplementedError


def choose_collision_safe_name(desired_name: str, existing_names: set[str]) -> str:
    raise NotImplementedError


def generate_safe_filename(input: NamingInput, existing_names: set[str]) -> str:
    raise NotImplementedError
```

- [ ] **Step 4: Run timestamp tests**

Run:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest tests/naming/test_safe_filename.py -v
```

Expected: PASS for the tests written in this task.

- [ ] **Step 5: Run full test suite**

Run:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add src/npu_screenshot_renamer/naming tests/naming/test_safe_filename.py
git commit -m "feat: add naming timestamp helpers"
```

---

### Task 2: Slug And Fallback Topic Generation

**Files:**
- Modify: `src/npu_screenshot_renamer/naming/safe_filename.py`
- Modify: `tests/naming/test_safe_filename.py`

- [ ] **Step 1: Add failing slug and fallback tests**

Append to `tests/naming/test_safe_filename.py`:

```python
from npu_screenshot_renamer.naming.safe_filename import fallback_topic, slugify_topic


def test_slugify_topic_lowercases_and_hyphenates_ascii_text():
    assert (
        slugify_topic("Task Manager: NPU / Intel AI Boost!")
        == "task-manager-npu-intel-ai-boost"
    )


def test_slugify_topic_removes_windows_reserved_characters_and_repeated_separators():
    assert slugify_topic(' Browser <OpenVINO> "Docs" | NPU?? ') == "browser-openvino-docs-npu"


def test_slugify_topic_drops_non_ascii_and_returns_empty_when_no_ascii_remains():
    assert slugify_topic("設定 截圖 測試") == ""


def test_slugify_topic_truncates_without_trailing_hyphen():
    assert slugify_topic("alpha beta gamma", max_length=11) == "alpha-beta"


def test_fallback_topic_uses_selected_timestamp_time():
    assert fallback_topic(dt("2026-05-29T14:35:22")) == "screenshot_143522"
```

- [ ] **Step 2: Run slug tests to verify they fail**

Run:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest tests/naming/test_safe_filename.py -v
```

Expected: FAIL with `NotImplementedError` from `slugify_topic` or `fallback_topic`.

- [ ] **Step 3: Implement slug and fallback helpers**

Replace the placeholder `slugify_topic` and `fallback_topic` in `src/npu_screenshot_renamer/naming/safe_filename.py`:

```python
def slugify_topic(topic: str, max_length: int = 80) -> str:
    chars: list[str] = []
    previous_was_separator = False

    for char in topic.lower():
        if "a" <= char <= "z" or "0" <= char <= "9":
            chars.append(char)
            previous_was_separator = False
        elif ord(char) < 128:
            if not previous_was_separator:
                chars.append("-")
                previous_was_separator = True

    slug = "".join(chars).strip("-")
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip("-")
    return slug


def fallback_topic(timestamp: datetime) -> str:
    return f"screenshot_{timestamp:%H%M%S}"
```

- [ ] **Step 4: Run naming tests**

Run:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest tests/naming/test_safe_filename.py -v
```

Expected: PASS.

- [ ] **Step 5: Run full test suite**

Run:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add src/npu_screenshot_renamer/naming/safe_filename.py tests/naming/test_safe_filename.py
git commit -m "feat: add topic slug generation"
```

---

### Task 3: Collision Handling And Existing Pattern Detection

**Files:**
- Modify: `src/npu_screenshot_renamer/naming/safe_filename.py`
- Modify: `tests/naming/test_safe_filename.py`

- [ ] **Step 1: Add failing collision and pattern tests**

Append to `tests/naming/test_safe_filename.py`:

```python
from npu_screenshot_renamer.naming.safe_filename import (
    choose_collision_safe_name,
    is_app_named_file,
)


def test_collision_safe_name_returns_desired_name_when_available():
    assert choose_collision_safe_name("2026-05-29_task-manager.png", set()) == (
        "2026-05-29_task-manager.png"
    )


def test_collision_safe_name_appends_suffix_starting_at_02():
    existing = {
        "2026-05-29_task-manager.png",
        "2026-05-29_task-manager_02.png",
    }

    assert choose_collision_safe_name("2026-05-29_task-manager.png", existing) == (
        "2026-05-29_task-manager_03.png"
    )


def test_collision_safe_name_matches_existing_names_case_insensitively():
    existing = {"2026-05-29_TASK-MANAGER.PNG"}

    assert choose_collision_safe_name("2026-05-29_task-manager.png", existing) == (
        "2026-05-29_task-manager_02.png"
    )


@pytest.mark.parametrize(
    "filename",
    [
        "2026-05-29_task-manager-npu.png",
        "2026-05-29_task-manager-npu_02.png",
        "2026-05-29_screenshot_143522.png",
        "2026-05-29_screenshot_143522_02.webp",
    ],
)
def test_is_app_named_file_accepts_supported_app_patterns(filename):
    assert is_app_named_file(filename) is True


@pytest.mark.parametrize(
    "filename",
    [
        "2026-05-29_Task-Manager.png",
        "2026-05-29_task_manager.png",
        "2026-05-29_task-manager.gif",
        "screenshot_143522.png",
        "2026-05-29_screenshot_1435.png",
        "2026-05-29_.png",
    ],
)
def test_is_app_named_file_rejects_malformed_or_unsupported_names(filename):
    assert is_app_named_file(filename) is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest tests/naming/test_safe_filename.py -v
```

Expected: FAIL with `NotImplementedError` from `choose_collision_safe_name` or `is_app_named_file`.

- [ ] **Step 3: Implement collision and pattern helpers**

Add imports at the top of `src/npu_screenshot_renamer/naming/safe_filename.py`:

```python
import re
```

Add module constant after `SUPPORTED_IMAGE_EXTENSIONS`:

```python
APP_NAMED_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}_"
    r"(?:(?:[a-z0-9]+(?:-[a-z0-9]+)*)|(?:screenshot_\d{6}))"
    r"(?:_\d{2})?"
    r"\.(?:png|jpg|jpeg|webp)$"
)
```

Replace placeholder `is_app_named_file` and `choose_collision_safe_name`:

```python
def is_app_named_file(filename: str) -> bool:
    return APP_NAMED_PATTERN.fullmatch(filename) is not None


def choose_collision_safe_name(desired_name: str, existing_names: set[str]) -> str:
    existing_normalized = {name.casefold() for name in existing_names}
    if desired_name.casefold() not in existing_normalized:
        return desired_name

    stem, extension = Path(desired_name).stem, Path(desired_name).suffix
    suffix = 2
    while True:
        candidate = f"{stem}_{suffix:02d}{extension}"
        if candidate.casefold() not in existing_normalized:
            return candidate
        suffix += 1
```

- [ ] **Step 4: Run naming tests**

Run:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest tests/naming/test_safe_filename.py -v
```

Expected: PASS.

- [ ] **Step 5: Run full test suite**

Run:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add src/npu_screenshot_renamer/naming/safe_filename.py tests/naming/test_safe_filename.py
git commit -m "feat: add collision safe filename helpers"
```

---

### Task 4: Safe Filename Generation And README Update

**Files:**
- Modify: `src/npu_screenshot_renamer/naming/safe_filename.py`
- Modify: `tests/naming/test_safe_filename.py`
- Modify: `README.md`

- [ ] **Step 1: Add failing final generation tests**

Append to `tests/naming/test_safe_filename.py`:

```python
from pathlib import Path

from npu_screenshot_renamer.naming.safe_filename import NamingInput, generate_safe_filename


def test_generate_safe_filename_uses_slug_when_confidence_is_high_enough():
    naming_input = NamingInput(
        source_path=Path("Screenshot.PNG"),
        topic="Task Manager NPU Usage",
        confidence=0.91,
        timestamps=FileTimestamps(
            created_at=dt("2026-05-29T14:35:22"),
            modified_at=None,
            now=dt("2026-05-30T09:00:00"),
        ),
    )

    assert generate_safe_filename(naming_input, set()) == "2026-05-29_task-manager-npu-usage.png"


def test_generate_safe_filename_uses_fallback_when_confidence_is_low():
    naming_input = NamingInput(
        source_path=Path("Screenshot.webp"),
        topic="Task Manager NPU Usage",
        confidence=0.49,
        timestamps=FileTimestamps(
            created_at=dt("2026-05-29T14:35:22"),
            modified_at=None,
            now=dt("2026-05-30T09:00:00"),
        ),
    )

    assert generate_safe_filename(naming_input, set()) == "2026-05-29_screenshot_143522.webp"


def test_generate_safe_filename_uses_fallback_when_slug_is_empty():
    naming_input = NamingInput(
        source_path=Path("Screenshot.jpg"),
        topic="設定 截圖",
        confidence=0.95,
        timestamps=FileTimestamps(
            created_at=dt("2026-05-29T14:35:22"),
            modified_at=None,
            now=dt("2026-05-30T09:00:00"),
        ),
    )

    assert generate_safe_filename(naming_input, set()) == "2026-05-29_screenshot_143522.jpg"


def test_generate_safe_filename_applies_collision_suffix():
    naming_input = NamingInput(
        source_path=Path("Screenshot.png"),
        topic="Task Manager",
        confidence=0.95,
        timestamps=FileTimestamps(
            created_at=dt("2026-05-29T14:35:22"),
            modified_at=None,
            now=dt("2026-05-30T09:00:00"),
        ),
    )
    existing = {"2026-05-29_task-manager.png"}

    assert generate_safe_filename(naming_input, existing) == "2026-05-29_task-manager_02.png"


def test_generate_safe_filename_rejects_unsupported_extension():
    naming_input = NamingInput(
        source_path=Path("Screenshot.gif"),
        topic="Task Manager",
        confidence=0.95,
        timestamps=FileTimestamps(
            created_at=dt("2026-05-29T14:35:22"),
            modified_at=None,
            now=dt("2026-05-30T09:00:00"),
        ),
    )

    with pytest.raises(ValueError, match="Unsupported image extension"):
        generate_safe_filename(naming_input, set())
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest tests/naming/test_safe_filename.py -v
```

Expected: FAIL with `NotImplementedError` from `generate_safe_filename`.

- [ ] **Step 3: Implement final filename generator**

Replace placeholder `generate_safe_filename`:

```python
def generate_safe_filename(input: NamingInput, existing_names: set[str]) -> str:
    extension = input.source_path.suffix.lower()
    if not is_supported_image_extension(extension):
        raise ValueError(f"Unsupported image extension: {input.source_path.suffix}")

    selected_timestamp = choose_timestamp(input.timestamps)
    prefix = date_prefix(selected_timestamp)
    topic_slug = ""

    if input.topic is not None and input.confidence >= input.confidence_threshold:
        topic_slug = slugify_topic(input.topic, input.max_topic_length)

    if not topic_slug:
        topic_slug = fallback_topic(selected_timestamp)

    desired_name = f"{prefix}_{topic_slug}{extension}"
    return choose_collision_safe_name(desired_name, existing_names)
```

- [ ] **Step 4: Update README**

In `README.md`, add Safe Rename Core to the implemented list:

```markdown
- Safe Rename Core for date prefixes, safe topic slugs, fallback names, supported extensions, app-pattern detection, and collision-safe suffixes.
```

In the planned list, keep actual renaming as future work:

```markdown
- Actual filesystem rename service that applies Safe Rename Core outputs.
```

Add `naming/` to the project structure:

```text
  naming/
    safe_filename.py           Pure safe filename generation helpers
```

- [ ] **Step 5: Run naming tests**

Run:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest tests/naming/test_safe_filename.py -v
```

Expected: PASS.

- [ ] **Step 6: Run full test suite**

Run:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add src/npu_screenshot_renamer/naming tests/naming/test_safe_filename.py README.md
git commit -m "feat: generate safe screenshot filenames"
```

---

## Self-Review

Spec coverage:

- Date prefix selection is covered by Task 1.
- Supported extension handling is covered by Task 1 and Task 4.
- Topic slug sanitization and fallback topic generation are covered by Task 2.
- Collision suffix generation and case-insensitive matching are covered by Task 3.
- Existing app-pattern detection is covered by Task 3.
- Final safe filename generation and unsupported extension errors are covered by Task 4.
- README update is covered by Task 4.

Placeholder scan:

- No `TBD`, `TODO`, or vague implementation steps remain.
- Each production-code step contains concrete code.

Type consistency:

- `FileTimestamps`, `NamingInput`, `choose_timestamp`, `date_prefix`, `slugify_topic`, `fallback_topic`, `is_supported_image_extension`, `is_app_named_file`, `choose_collision_safe_name`, and `generate_safe_filename` are defined before later tasks use them.

Intentional deferrals:

- Actual filesystem renaming, batch scanning, folder watching, SQLite history, undo, and AI topic extraction are not part of this plan.
