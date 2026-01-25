# CLAUDE.md - Project Guide for Claude Code

This file provides context for Claude Code when working on this project.

## Project Overview

Tana to Obsidian Converter - A cross-platform desktop application that converts Tana JSON exports to Obsidian-compatible markdown files.

## Documentation

- **README.md** - User-facing documentation, installation, and usage instructions
- **PROJECT_SCAFFOLD.md** - Original architecture design and implementation plan
- **CLAUDE_CODE_INSTRUCTIONS.md** - Step-by-step prompts used to build this project (historical reference)

## Quick Reference

### Run the Application
```bash
source .venv/bin/activate
python -m src.main
```

### Run Tests
```bash
source .venv/bin/activate
pytest
```

### Build Executable
```bash
source .venv/bin/activate
python build/build.py --clean
```

## Project Structure

```
src/
├── main.py              # Entry point
├── core/
│   ├── converter.py     # Main TanaToObsidian class (1400+ lines)
│   ├── models.py        # ConversionSettings, ConversionProgress, ConversionResult
│   └── exceptions.py    # ConversionError, ConversionCancelled, FileAccessError
└── gui/
    ├── app.py           # TanaToObsidianApp (CustomTkinter main window)
    ├── components.py    # Reusable UI components (FilePickerFrame, OptionsFrame, etc.)
    └── styles.py        # Theme constants

tests/
├── test_converter.py    # 60 unit tests
└── fixtures/
    └── sample_tana_export.json

build/
├── build.py             # PyInstaller build script
└── create_icons.py      # Icon generator (creates .png, .ico, .icns)

assets/                  # Application icons
```

## Architecture

### Core Converter (`src/core/converter.py`)

The `TanaToObsidian` class accepts:
- `settings: ConversionSettings` - All configurable options
- `progress_callback: Callable[[ConversionProgress], None]` - For UI updates
- `cancel_event: threading.Event` - For cancellation support

Key methods:
- `run()` → `ConversionResult` - Main conversion process
- `report_progress()` - Sends progress updates to callback
- `check_cancelled()` - Raises `ConversionCancelled` if event is set

### GUI (`src/gui/app.py`)

Uses CustomTkinter for modern styling. Runs conversion in a background thread with progress updates via `self.after()` for thread-safe UI updates.

## Development Notes

- Python 3.11+ required
- macOS requires `brew install python-tk@3.14` for tkinter
- PyInstaller builds use `--onedir` mode on macOS, `--onefile` on Windows/Linux
- Tests use pytest with fixtures in `tests/fixtures/`

## Common Tasks

### Adding a New Option
1. Add field to `ConversionSettings` in `src/core/models.py`
2. Add checkbox to `OptionsFrame` in `src/gui/components.py`
3. Pass option in `_start_conversion()` in `src/gui/app.py`
4. Use `self.settings.new_option` in converter logic

### Adding a New Test
1. Add test data to `tests/fixtures/sample_tana_export.json` if needed
2. Add test method to appropriate class in `tests/test_converter.py`
3. Run `pytest -v` to verify

### Modifying Conversion Logic
1. Keep changes in `src/core/converter.py`
2. Preserve progress reporting with `self.report_progress()`
3. Add `self.check_cancelled()` calls in loops
4. Update tests if behavior changes
