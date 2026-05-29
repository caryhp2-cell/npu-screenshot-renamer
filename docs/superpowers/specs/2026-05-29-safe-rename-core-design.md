# Safe Rename Core Design Spec

Date: 2026-05-29
Status: Design approved for implementation

## 1. Purpose

Safe Rename Core is the deterministic filename-generation layer for NPU Screenshot Renamer.

It converts image metadata and analyzer output into a safe target filename without touching the filesystem. Later batch processing and folder watching will use this core before performing an actual rename.

This feature deliberately avoids real file renaming, UI changes, OCR, image loading, folder watching, history storage, and undo. Those will be separate implementation slices.

## 2. User Outcome

The user should be protected from unsafe or confusing filenames before the app starts renaming real screenshots.

The app should always be able to produce a filename that:

- Starts with `YYYY-MM-DD_`.
- Uses a readable topic slug when confidence is high enough.
- Falls back to a conservative screenshot timestamp when confidence is low.
- Preserves the original image extension.
- Never targets a filename that already exists in the destination folder.

## 3. Scope

This slice implements pure, testable logic:

- Date prefix selection.
- Topic slug sanitization.
- Fallback filename generation.
- Existing app-pattern detection.
- Collision-safe candidate selection.
- Target filename construction from an analysis result.

It does not perform `Path.rename()` or mutate files.

## 4. Inputs

The core receives:

- Original image path.
- Creation time, modified time, and current time as Python `datetime` values.
- Optional topic text from analysis.
- Analysis confidence.
- A configured confidence threshold.
- Maximum topic length or maximum filename length.
- A set or callable representing names that already exist in the target directory.

Supported extensions for this slice:

- `.png`
- `.jpg`
- `.jpeg`
- `.webp`

Extension comparison is case-insensitive. Output extensions should be lowercase.

## 5. Date Prefix Rules

Generated filenames must begin with:

```text
YYYY-MM-DD_
```

Date selection order:

1. Use creation time when it is plausible.
2. Otherwise use modified time when it is plausible.
3. Otherwise use current local time.

A timestamp is plausible when:

- It is not `None`.
- Its year is between 2000 and the current local year plus one.

The date formatter should return local calendar dates only. It should not include timezone text.

## 6. Topic Slug Rules

Topic slugs should be:

- Lowercase.
- ASCII by default.
- Hyphen-separated.
- Free of Windows-reserved filename characters.
- Stripped of leading and trailing separators.
- Compact enough for File Explorer scanning.

Allowed slug characters:

```text
a-z 0-9 -
```

Sanitization behavior:

- Convert spaces, underscores, punctuation, and repeated separators to one hyphen.
- Drop non-ASCII characters in this first version.
- Drop Windows-reserved characters: `< > : " / \ | ? *`.
- Drop control characters.
- Trim leading and trailing hyphens.
- If the resulting slug is empty, use fallback naming.

Example:

```text
"Task Manager: NPU / Intel AI Boost!" -> "task-manager-npu-intel-ai-boost"
```

## 7. Confidence And Fallback Rules

Default filename pattern when confidence is high enough:

```text
{date}_{topic}.{ext}
```

Fallback pattern when confidence is below threshold or slug sanitization produces no topic:

```text
{date}_screenshot_{HHMMSS}.{ext}
```

The fallback time uses the same timestamp selected for the date when available. If no plausible image timestamp exists, it uses current local time.

Default confidence threshold:

```text
0.50
```

The threshold should be configurable by function argument, but no UI setting is required in this slice.

## 8. Collision Handling

The core must never select a target filename that already exists.

If the desired name exists, append a numeric suffix before the extension:

```text
2026-05-29_task-manager-npu-usage.png
2026-05-29_task-manager-npu-usage_02.png
2026-05-29_task-manager-npu-usage_03.png
```

Suffix numbering starts at `_02`.

Collision checks should be case-insensitive on Windows. For this Python prototype, the collision function should normalize candidate names with `.casefold()`.

The collision resolver returns only the selected filename. Actual filesystem rename remains out of scope.

## 9. Existing Pattern Detection

The app should be able to skip files that already look renamed by this app.

This slice should provide an `is_app_named_file(filename: str) -> bool` helper.

It returns true when a filename matches:

```text
YYYY-MM-DD_<topic>.<supported-ext>
YYYY-MM-DD_<topic>_02.<supported-ext>
YYYY-MM-DD_screenshot_HHMMSS.<supported-ext>
YYYY-MM-DD_screenshot_HHMMSS_02.<supported-ext>
```

The topic portion must contain only lowercase ASCII letters, digits, hyphens, or the fallback screenshot pattern. The helper should reject unsupported extensions.

## 10. Proposed Module Boundaries

Create a new naming package:

```text
src/npu_screenshot_renamer/naming/
  __init__.py
  safe_filename.py
```

`safe_filename.py` owns pure filename logic.

Suggested public API:

```python
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


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


def choose_timestamp(timestamps: FileTimestamps) -> datetime: ...
def date_prefix(timestamp: datetime) -> str: ...
def slugify_topic(topic: str, max_length: int = 80) -> str: ...
def fallback_topic(timestamp: datetime) -> str: ...
def is_supported_image_extension(extension: str) -> bool: ...
def is_app_named_file(filename: str) -> bool: ...
def choose_collision_safe_name(desired_name: str, existing_names: set[str]) -> str: ...
def generate_safe_filename(input: NamingInput, existing_names: set[str]) -> str: ...
```

This API stays independent from the analyzer module for now. Later code can map `AnalysisResult.summary` or future `topic_slug` values into `NamingInput.topic`.

## 11. Error Behavior

The core should raise `ValueError` when asked to generate a filename for an unsupported extension.

It should not raise for:

- Missing topic.
- Empty topic after sanitization.
- Low confidence.
- Missing creation time.
- Missing modified time.

Those cases should use fallback naming.

## 12. Testing Requirements

Unit tests should cover:

- Creation time is preferred when plausible.
- Modified time is used when creation time is implausible.
- Current time is used when both image timestamps are missing or implausible.
- Date prefix format.
- Slug sanitization.
- Non-ASCII topic text falls back when it becomes empty.
- Confidence below threshold uses fallback naming.
- Unsupported extension raises `ValueError`.
- Collision suffix generation starts at `_02`.
- Collision matching is case-insensitive.
- Existing-pattern detection accepts app-generated names.
- Existing-pattern detection rejects unsupported or malformed names.

Integration with UI, filesystem rename, watcher, and history is intentionally deferred.

## 13. Acceptance Criteria

This slice is complete when:

1. The naming module exists with the public API above or a smaller equivalent API that covers the same behavior.
2. Tests prove generated filenames always include `YYYY-MM-DD_`.
3. Tests prove collision handling never returns an existing name.
4. Tests prove fallback naming is deterministic from selected timestamp.
5. Tests pass with the existing test suite.
6. README is updated with a short note that Safe Rename Core is implemented but actual file renaming is still future work.
