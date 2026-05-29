# NPU Screenshot Renamer

NPU Screenshot Renamer is a Windows-first desktop app prototype for automatically renaming screenshots and image files with meaningful filenames.

The long-term goal is to watch user-selected screenshot folders, analyze local image content, generate safe filenames with a required date prefix, and keep a local undo history. The project is designed around an OpenVINO NPU-first runtime path, with clear fallback to GPU, CPU, or rule-only naming when NPU inference is unavailable.

## Current Status

This repository currently contains the first MVP skeleton. It does not yet rename files or run real OCR/classification models.

Implemented so far:

- Python package scaffold.
- OpenVINO device discovery.
- Runtime selection order: `NPU -> GPU -> CPU -> Rule-only`.
- Support for qualified OpenVINO device names such as `GPU.0`.
- Resilient fallback if OpenVINO import or device discovery fails.
- Compact PySide6 main window.
- Low-emphasis runtime status badge:
  - `NPU active`
  - `GPU fallback`
  - `CPU fallback`
  - `Rule-only fallback`
- Placeholder analyzer result that records which runtime status was used.
- Unit and UI tests for the runtime model, selector, widget, main window, and app bootstrap.

Planned but not implemented yet:

- Folder selection behavior.
- Batch rename of existing screenshots.
- Watch mode for new screenshots.
- Filename generation and collision handling.
- SQLite history and undo.
- Real OCR/image analysis through OpenVINO.

## Requirements

- Windows 11 is the initial target platform.
- Python 3.11 or newer.
- Git.
- Optional but recommended: Intel NPU-capable machine with OpenVINO NPU runtime support.

The app can still run without NPU support. It will show a fallback status in the UI.

## Clone The Repository

```powershell
git clone https://github.com/caryhp2-cell/npu-screenshot-renamer.git
cd npu-screenshot-renamer
```

## Create A Virtual Environment

```powershell
py -3.11 -m venv .venv
```

If `py -3.11` is not available, use:

```powershell
python -m venv .venv
```

Activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Upgrade packaging tools:

```powershell
python -m pip install --upgrade pip setuptools wheel
```

## Install The Project

Install the app and development dependencies:

```powershell
pip install -e ".[dev]"
```

If PySide6 installation fails on Windows with a long-path error, enable Windows long paths and try again. In an elevated PowerShell:

```powershell
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

Then open a new terminal and rerun:

```powershell
pip install -e ".[dev]"
```

## Run Tests

For headless Qt test runs, set `QT_QPA_PLATFORM` to `offscreen`:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest -q
```

Expected result:

```text
16 passed
```

Run focused runtime tests:

```powershell
python -m pytest tests/runtime -v
```

Run focused UI tests:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest tests/ui -v
```

## Start The App

After installing with `pip install -e ".[dev]"`, start the app with the console script:

```powershell
npu-screenshot-renamer
```

You can also run the module:

```powershell
python -m npu_screenshot_renamer.app
```

If you have not installed the package and are running directly from the checkout, add `src` to `PYTHONPATH`:

```powershell
$env:PYTHONPATH = "src"
python -m npu_screenshot_renamer.app
```

## Verify Runtime Fallback Status

When the app opens, look at the bottom `Runtime` row.

Expected behavior:

- If OpenVINO reports an NPU device, the badge shows `NPU active`.
- If no NPU is available but GPU is available, the badge shows `GPU fallback`.
- If only CPU is available, the badge shows `CPU fallback`.
- If OpenVINO is unavailable or device discovery fails, the badge shows `Rule-only fallback`.

Hover the badge to see the short reason, such as:

```text
NPU unavailable; using GPU
```

The fallback indicator is intentionally subtle. It should inform the user without blocking automatic processing or showing a warning dialog.

## Project Structure

```text
src/npu_screenshot_renamer/
  app.py                       Qt app bootstrap
  runtime/
    analyzer.py                Placeholder analyzer result boundary
    device_selector.py         OpenVINO discovery and runtime fallback selection
    status.py                  Runtime status model and display labels
  ui/
    main_window.py             Compact PySide6 main window
    runtime_status_widget.py   Runtime status badge widget

tests/
  runtime/                     Runtime model, selector, analyzer tests
  ui/                          PySide6 widget and main window tests
```

## Development Workflow

1. Activate the virtual environment:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

2. Pull the latest changes:

   ```powershell
   git pull
   ```

3. Run the tests before editing:

   ```powershell
   $env:QT_QPA_PLATFORM = "offscreen"
   python -m pytest -q
   ```

4. Make a focused change.

5. Run the relevant focused tests.

6. Run the full test suite:

   ```powershell
   python -m pytest -q
   ```

7. Commit:

   ```powershell
   git status --short
   git add <changed-files>
   git commit -m "short description"
   ```

8. Push:

   ```powershell
   git push
   ```

## Design Notes

The detailed design spec lives at:

```text
docs/superpowers/specs/2026-05-29-npu-screenshot-renamer-design.md
```

The first implementation plan lives at:

```text
docs/superpowers/plans/2026-05-29-mvp-runtime-status-ui-plan.md
```

The current architecture intentionally separates runtime status, device selection, UI display, and future image analysis. That keeps the visible fallback behavior reliable even before the real screenshot naming engine is implemented.
