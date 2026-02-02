# CLAUDE.md - Project Guide for Claude Code

This file provides context for Claude Code when working on this project.

## Project Overview

Tana to Obsidian Converter - A cross-platform desktop application that converts Tana JSON exports to Obsidian-compatible markdown files. Features a wizard-based interface with automatic supertag discovery, dynamic field mapping, and configurable output folders.

## Documentation

- **README.md** - User-facing documentation, installation, and usage instructions

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
│   ├── converter.py     # Main TanaToObsidian class - conversion logic
│   ├── scanner.py       # TanaExportScanner - supertag/field discovery
│   ├── models.py        # Data classes (see below)
│   └── exceptions.py    # ConversionError, ConversionCancelled, FileAccessError
└── gui/
    ├── app.py           # TanaToObsidianApp - 3-step wizard interface
    ├── components.py    # UI components (FilePickerFrame, SupertagSelectionFrame, etc.)
    └── styles.py        # Theme constants

tests/
├── test_converter.py    # 57 unit tests
└── fixtures/
    └── sample_tana_export.json

build/
├── build.py             # PyInstaller build script
└── create_icons.py      # Icon generator (creates .png, .ico, .icns)

assets/                  # Application icons
pyproject.toml           # Project configuration and dependencies
requirements.txt         # Runtime dependencies
.github/                 # GitHub Actions workflows
```

## Architecture

### Scanner (`src/core/scanner.py`)

The `TanaExportScanner` class discovers supertags and their fields from the Tana export:
- Scans for `tagDef` documents to find supertags
- Detects field types via `SYS_A02` (typeChoice) tuples
- Identifies field data types: checkbox, date, options, number, url, email, plain
- Extracts option values for "options" type fields
- Filters out system/internal supertags and trashed items
- Runs in background thread with progress callback

Key classes returned:
- `SupertagInfo` - id, name, instance_count, fields, is_system, special_type
- `FieldInfo` - id, name, field_type, data_type, source_supertag_id/name, options

### Converter (`src/core/converter.py`)

The `TanaToObsidian` class accepts:
- `settings: ConversionSettings` - All configurable options including supertag_configs
- `progress_callback: Callable[[ConversionProgress], None]` - For UI updates
- `cancel_event: threading.Event` - For cancellation support

Key methods:
- `run()` → `ConversionResult` - Main conversion process (5 phases)
- `get_field_value(node_id, field_id)` - Extract field value for a node
- `get_field_values_with_metadata(node_id, field_id)` - Get values with supertag info
- `get_all_field_values(node_id)` - Get all configured field values with transforms
- `create_frontmatter()` - Generate YAML frontmatter with dynamic fields
- `_get_node_output_folder(doc)` - Determine output folder based on supertag config
- `_doc_has_any_supertag(doc)` - Check if node has any supertag (for library node filtering)

Conversion phases:
1. Daily notes export (to configured folder)
2. Tagged nodes collection from daily notes
3. Orphan tagged nodes (not under daily notes)
4. Write merged files (same-named nodes merged)
5. Referenced untagged nodes (if enabled)

### Models (`src/core/models.py`)

Key data classes:
- `FieldInfo` - Discovered field with type information
- `SupertagInfo` - Discovered supertag with fields
- `FieldMapping` - User config for field → frontmatter mapping
- `SupertagConfig` - User config for supertag conversion (includes output_folder)
- `ConversionSettings` - All conversion options (includes attachments_folder, untagged_library_folder)
- `ConversionProgress` / `ConversionResult` - Progress and result reporting

### GUI (`src/gui/app.py`)

3-step wizard interface using CustomTkinter:
1. **Select File** - Choose JSON export, option to ignore trash, background scanning with progress
2. **Select Supertags** - Check supertags to include, shows instance counts, library nodes option, incremental loading
3. **Configure and Convert** - Output directory, folder configuration per supertag, attachments folder, scrollable content, progress log

Key features:
- Background thread for JSON scanning
- Incremental supertag list loading (batches of 10)
- Background thread for conversion
- Progress updates via `self.after()`
- Cancel support

### Components (`src/gui/components.py`)

- `FilePickerFrame` - File/folder selection with browse button
- `StepIndicator` - Shows current wizard step
- `SupertagSelectionFrame` - Scrollable supertag checkboxes with incremental loading
- `GlobalOptionsFrame` - Download images checkbox
- `ProgressFrame` - Progress bar and status
- `LogFrame` - Scrollable log text
- `WizardNavigationFrame` - Back/Next/Convert/Cancel buttons
- `ActionButtonsFrame` - Action buttons for conversion step
- `FolderConfigFrame` - Configure output folders for each supertag

## Development Notes

- Python 3.11+ required
- macOS requires `brew install python-tk@3.11` (or matching Python version) for tkinter
- PyInstaller builds use `--onedir` mode on macOS, `--onefile` on Windows/Linux
- Tests use pytest with fixtures in `tests/fixtures/`

## Common Tasks

### Adding a New Field Type
1. Add constant to `TanaExportScanner` in `scanner.py` (e.g., `DATA_TYPE_NEW = 'SYS_DXX'`)
2. Add mapping in `DATA_TYPE_MAP`
3. Handle in `_detect_field_data_type()` if special logic needed
4. Handle in `get_field_value()` in converter if special extraction needed

### Adding a New Option
1. Add field to `ConversionSettings` in `src/core/models.py`
2. Add UI element to appropriate component in `src/gui/components.py`
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

### Adding a New Output Folder Option
1. Add field to `ConversionSettings` in `src/core/models.py`
2. Add entry field to `FolderConfigFrame` in `src/gui/components.py`
3. Add getter method in `FolderConfigFrame`
4. Pass to `ConversionSettings` in `_start_conversion()` in `src/gui/app.py`
5. Use in converter (e.g., `self.settings.new_folder`)


---

## Development Workflow

When adding features or making non-trivial changes, follow this process:

### 1. Planning Phase

Before writing code, enter planning mode:
- Describe the feature requirements and constraints
- Identify affected files and potential side effects
- Create a GitHub issue with:
  - Clear description of the feature
  - Implementation approach
  - Success criteria (specific, testable)
  - Testing/validation steps

Example issue template:
```markdown
## Description
[What and why]

## Implementation Approach
[How - files to modify, new functions, etc.]

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Testing
- [ ] Test case 1
- [ ] Test case 2
```

### 2. Implementation Phase

```bash
# Create feature branch
git checkout -b feature/description

# Do the work...

# Validate against success criteria
# Run tests if applicable

# Self-review before marking complete
```

**Before considering implementation complete, verify:**
- [ ] Meets all success criteria from the issue
- [ ] Separation of concerns (no god functions)
- [ ] DRY - no duplicated logic
- [ ] Clean, idiomatic Python
- [ ] Functions are focused and under ~50 lines
- [ ] Error handling is appropriate
- [ ] Logging is useful but not excessive

If criteria are not met, continue iterating in the feature branch.

### 3. Merge Phase

Only after all criteria are met:

```bash
git checkout main
git merge feature/description
git push
# Close the GitHub issue
```

**Never commit directly to main for non-trivial changes.**

---

## Coding Standards

### Structure
- **No god functions**: Break large functions into smaller, focused ones
- **DRY**: Extract repeated logic into helper functions
- **Single responsibility**: Each function does one thing well
- **Max function length**: ~50 lines (guideline, not hard rule)

### Style
- **Clear naming**: Functions and variables should be self-documenting
- **Type hints**: Use them for function signatures
- **Docstrings**: Required for any function that isn't immediately obvious
- **Imports**: Standard library → third-party → local (separated by blank lines)

### Error Handling
- Fail gracefully with useful error messages
- Don't swallow exceptions silently
- Log errors appropriately

### Example

```python
# Good
def get_vault_notes(vault_path: Path, excluded_dirs: set[str]) -> set[str]:
    """Return set of note names (without .md extension) from vault."""
    notes = set()
    for md_file in vault_path.rglob("*.md"):
        if any(excluded in md_file.parts for excluded in excluded_dirs):
            continue
        notes.add(md_file.stem)
    return notes

# Bad
def process(p):  # unclear name, no types, no docstring
    n = set()
    for f in p.rglob("*.md"):
        if '.venv' in str(f) or '.chroma_db' in str(f) or '.trash' in str(f):  # duplicated logic
            continue
        n.add(f.stem)
    return n
```

