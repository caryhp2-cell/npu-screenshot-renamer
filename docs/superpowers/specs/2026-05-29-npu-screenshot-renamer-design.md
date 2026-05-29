# NPU Screenshot Renamer Design Spec

Date: 2026-05-29
Status: Design only, not implemented

## 1. Purpose

NPU Screenshot Renamer is a Windows desktop/background app that automatically renames screenshots and image files in user-defined folders.

The app has two primary jobs:

1. Rename existing image files already present in a selected screenshot folder.
2. Watch the folder for new screenshots and rename them automatically without asking for confirmation.

The app should use the local Intel NPU as much as practical for image understanding, while remaining reliable if a model or driver path falls back to CPU.

## 2. Target User

The target user is a normal Windows user who captures many screenshots and later wants to find them by meaningful filename.

The user does not want to manually confirm each rename. The app should make a reasonable decision, record what it did, and provide a way to undo.

## 3. Target Hardware And OS

Initial target machine:

- CPU: Intel Core Ultra 7 256V
- NPU: Intel AI Boost
- OS: Windows 11 IoT Enterprise LTSC, version 24H2, build 26100

The app should not depend on Copilot+ PC shell features. The primary AI runtime should be Intel OpenVINO with an NPU-first inference path.

## 4. Non-Goals

The first version will not:

- Provide cloud AI naming.
- Require Copilot+ PC-only Windows features.
- Implement a large local chat model as the main naming engine.
- Rename non-image documents such as Word, Excel, ZIP, or source code files.
- Modify image content.
- Upload files or screenshots to any external service.

## 5. Supported Inputs

The first version should support:

- `.png`
- `.jpg`
- `.jpeg`
- `.webp`

Optional later support:

- `.bmp`
- `.heic`
- `.tiff`
- PDF screenshots or scanned documents

## 6. Core Behaviors

### 6.1 Folder Configuration

The user can configure one or more watched folders.

Each watched folder has these settings:

- Folder path
- Whether to process existing files
- Whether to watch for new files
- Whether to include subfolders
- Naming pattern
- Maximum filename length
- Whether undo history is enabled

For the first version, supporting one watched folder is acceptable if the data model allows multiple folders later.

### 6.2 Batch Rename Existing Files

When the user enables batch processing, the app scans the configured folder for supported image files.

The app should skip files that appear to already follow the app's naming pattern unless the user explicitly requests reprocessing in a later version.

For each image:

1. Wait until the file is readable and stable.
2. Extract metadata such as creation time, modified time, extension, dimensions, and file size.
3. Analyze the image content.
4. Generate a safe filename.
5. Rename the file without overwriting existing files.
6. Record the operation in history.

### 6.3 Watch New Screenshots

When watching is enabled, the app monitors the configured folder for newly created supported image files.

For each new file:

1. Debounce file system events.
2. Wait until the file size and modified time are stable.
3. Analyze the image.
4. Rename automatically.
5. Record the operation in history.

The app should not show a confirmation dialog before renaming.

### 6.4 Required Date Prefix

Every generated filename must include a date prefix:

```text
YYYY-MM-DD_
```

Example:

```text
2026-05-29_task-manager-npu-intel-ai-boost.png
```

Date selection order:

1. Image creation time, if available and plausible.
2. Image modified time, if creation time is unavailable or implausible.
3. Current local date as a fallback.

The date must use local system time.

### 6.5 Filename Generation

Default filename pattern:

```text
{date}_{topic}.ext
```

The topic should be:

- Lowercase
- English ASCII by default
- Hyphen-separated
- Short enough to scan in File Explorer
- Based on visible screenshot content when possible

Examples:

```text
2026-05-29_windows-system-info-core-ultra-256v.png
2026-05-29_task-manager-npu-usage.png
2026-05-29_openvino-npu-driver-settings.png
2026-05-29_browser-openvino-documentation.png
```

If analysis confidence is low, use a conservative fallback:

```text
2026-05-29_screenshot_143522.png
```

### 6.6 Collision Handling

The app must never overwrite an existing file.

If the target filename already exists, append a numeric suffix:

```text
2026-05-29_task-manager-npu-usage.png
2026-05-29_task-manager-npu-usage_02.png
2026-05-29_task-manager-npu-usage_03.png
```

### 6.7 Undo History

Every successful rename should be written to a local history store.

Each history record includes:

- Timestamp of rename
- Original full path
- New full path
- Original filename
- New filename
- File size
- Extension
- Content hash if available
- Analysis summary
- Confidence score
- Model/runtime used

The app should provide an undo action that restores selected renamed files if the current file still exists and no collision prevents restoration.

## 7. AI And NPU Design

### 7.1 Runtime Strategy

The first implementation should use OpenVINO as the main inference runtime.

Inference priority:

1. OpenVINO NPU
2. OpenVINO GPU
3. OpenVINO CPU
4. Rule-only fallback

The app should expose runtime status in logs so the user can confirm whether NPU is being used.

### 7.2 Recommended Model Roles

The app should use small, practical models rather than a large local LLM in the first version.

Recommended model roles:

- OCR or text detection/recognition for visible text in screenshots.
- Image embedding or classification for identifying screenshot type.
- Optional lightweight object/layout detection for UI-heavy screenshots.

The naming engine should combine model outputs with deterministic rules.

### 7.3 Naming Engine

The naming engine receives:

- OCR text snippets
- Image classification labels
- Window/app hints if available
- File metadata
- Runtime confidence values

It returns:

- Topic slug
- Confidence score
- Short explanation for history/logging

The naming engine should prefer recognizable terms from the screenshot:

- Application names, such as `task-manager`, `settings`, `browser`, `excel`
- Key visible entities, such as `openvino`, `npu`, `intel-ai-boost`
- Page or dialog purpose, such as `system-info`, `driver-settings`, `performance`

### 7.4 NPU Usage Expectations

The NPU will be used only for model operations that OpenVINO can compile for the NPU device.

File watching, file I/O, image decoding, filename safety, history storage, and collision handling are normal CPU tasks.

The app should not pretend that every operation runs on NPU. It should report actual runtime decisions.

## 8. Architecture

### 8.1 Components

The app is divided into these components:

- App Shell: Tray app or lightweight desktop UI for settings, status, history, and undo.
- Folder Watcher: Detects new files and queues processing jobs.
- Batch Scanner: Finds existing files that need renaming.
- File Stabilizer: Waits until new files are fully written.
- Image Loader: Reads image dimensions, metadata, and normalized pixels.
- AI Analyzer: Runs OCR/classification/embedding through OpenVINO.
- Naming Engine: Converts analysis into a safe filename.
- Rename Service: Performs collision-safe rename operations.
- History Store: Records rename operations and supports undo.
- Runtime Diagnostics: Logs whether NPU, GPU, or CPU was used.

### 8.2 Data Flow

```text
Folder event or batch scan
  -> File stabilizer
  -> Image loader
  -> AI analyzer
  -> Naming engine
  -> Rename service
  -> History store
  -> UI/log update
```

### 8.3 Storage

The app should store configuration and history locally.

Recommended storage:

- `settings.json` for user settings
- SQLite for rename history

SQLite is preferred for history because undo, filtering, and audit queries are easier and more reliable than a plain log file.

## 9. User Interface

The first UI should be practical and compact.

Required screens:

- Settings: folder path, batch processing, watcher toggle, naming options.
- Queue/Status: pending, processing, completed, failed.
- History: original name, new name, timestamp, confidence, runtime.
- Undo: restore selected rename operations.
- Diagnostics: OpenVINO version, available devices, active inference device.

Runtime status should be visible but low-emphasis. When NPU is active, the UI may show a neutral `NPU active` indicator. When inference falls back to GPU, CPU, or rule-only naming, the UI should show a subtle status badge or diagnostics row such as `GPU fallback` or `CPU fallback`, including a short reason in tooltip or diagnostics text. This indicator must not block automatic renaming.

The app may start as a tray app with a simple settings window.

## 10. Safety And Error Handling

The app must handle:

- File still being written.
- File locked by screenshot software.
- Unsupported or corrupted image.
- OpenVINO model compile failure.
- NPU driver unavailable.
- Duplicate target filenames.
- Insufficient filesystem permissions.
- Very long paths or filenames.
- Files deleted before processing completes.

Error behavior:

- Do not delete files.
- Do not overwrite files.
- Do not repeatedly retry forever.
- Record the failure reason.
- Fall back to conservative naming when AI analysis fails.

## 11. Privacy

The app processes screenshots locally by default.

The first version must not upload screenshots, OCR text, filenames, or analysis results to external services.

If a future cloud naming option is added, it must be opt-in and clearly labeled.

## 12. Observability

Logs should include:

- File discovered
- File stabilized
- Analysis started/completed
- Runtime used: NPU, GPU, CPU, or fallback
- Generated filename
- Rename success/failure
- Undo success/failure

The app should make it easy to verify NPU usage in Task Manager by running batch processing on multiple images.

## 13. Testing Strategy

### 13.1 Unit Tests

Cover:

- Date prefix generation
- Filename slug sanitization
- Collision suffix generation
- Existing-pattern detection
- Fallback filename generation
- History record creation

### 13.2 Integration Tests

Cover:

- Batch rename in a temporary folder
- Watcher rename for newly created files
- Locked file retry behavior
- Undo restore behavior
- Duplicate filename collision behavior

### 13.3 Runtime Tests

Cover:

- OpenVINO device discovery
- NPU compile success for selected models
- CPU fallback when NPU compile fails
- Diagnostic logging of selected device

### 13.4 Manual Acceptance Tests

Acceptance test 1: Existing files

1. Put several screenshots in the watched folder.
2. Enable batch processing.
3. Confirm files are renamed with `YYYY-MM-DD_` prefix.
4. Confirm no file is overwritten.
5. Confirm history records are created.

Acceptance test 2: New screenshot

1. Enable folder watching.
2. Save a new screenshot into the folder.
3. Confirm the app waits for write completion.
4. Confirm the file is renamed automatically without confirmation.

Acceptance test 3: NPU diagnostics

1. Run batch processing on enough images to observe inference.
2. Confirm diagnostics show OpenVINO NPU when supported.
3. Confirm Task Manager NPU utilization changes during inference.

Acceptance test 4: Undo

1. Rename several files.
2. Select them in history.
3. Run undo.
4. Confirm original filenames are restored when safe.

## 14. MVP Scope

The MVP should include:

- One configurable watched folder
- Batch rename existing image files
- Automatic rename for new image files
- Required `YYYY-MM-DD_` prefix
- Collision-safe rename
- Local history
- Undo
- OpenVINO runtime diagnostics
- NPU-first analyzer with CPU fallback

The MVP may use a simple tray app or desktop window. A polished visual design is not required for the first build.

## 15. Future Enhancements

Potential later features:

- Multiple watched folders
- Per-folder naming rules
- Chinese filename mode
- Better OCR model
- Screenshot source app detection
- File Explorer context menu
- Preview-only dry run mode
- Export/import settings
- Cloud AI naming as an explicit opt-in option
- PDF and document support

## 16. Open Decisions

These decisions should be resolved before implementation:

1. Desktop stack: .NET/WPF, Python/PySide, or Tauri.
2. Exact OpenVINO model set for OCR and image classification.
3. Whether topic slugs should be English-only in v1 or allow Chinese.
4. Whether undo history should be kept forever or automatically pruned.
5. Whether batch processing should skip files that already start with any date prefix or only the app's exact pattern.

## 17. Recommended Implementation Direction

Recommended first implementation:

- Python prototype for fast OpenVINO experimentation.
- PySide6 or a minimal tray UI for settings and history.
- Watchdog for folder monitoring.
- SQLite for history.
- OpenVINO for NPU-first inference.

After the model path and naming quality are proven, the app can either remain Python-based or be rebuilt as a more native Windows app.

This path is recommended because the largest uncertainty is not the UI. The largest uncertainty is reliable NPU inference and useful automatic naming quality.
