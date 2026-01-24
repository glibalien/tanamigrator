# Claude Code Instructions

Use this file to guide Claude Code through implementing the Tana to Obsidian desktop application.

## Quick Start Prompt

Copy and paste this into Claude Code to get started:

```
I want to convert a Python script into a cross-platform desktop application. 

Please read PROJECT_SCAFFOLD.md for the full architecture and requirements, and ORIGINAL_SCRIPT.py for the existing code that needs to be refactored.

Start by:
1. Creating the directory structure
2. Setting up pyproject.toml and requirements.txt
3. Creating the core module with models.py and exceptions.py
4. Refactoring the converter (this is the main work - see PROJECT_SCAFFOLD.md for details)

The key changes to the converter:
- Accept a ConversionSettings dataclass instead of hardcoded paths
- Add progress_callback and cancel_event parameters
- Replace all print() calls with progress reporting
- Return a ConversionResult instead of printing a summary
```

## Phase-by-Phase Prompts

### Phase 1: Project Setup

```
Create the project directory structure for tana-to-obsidian:

src/
  __init__.py
  main.py
  core/
    __init__.py
    converter.py
    models.py
    exceptions.py
  gui/
    __init__.py
    app.py
    components.py
    styles.py
assets/
tests/
  __init__.py
build/

Also create pyproject.toml and requirements.txt per PROJECT_SCAFFOLD.md
```

### Phase 2: Core Models

```
Create src/core/models.py with:
- ConversionSettings dataclass (all the configurable options)
- ConversionProgress dataclass (for progress updates)
- ConversionResult dataclass (final conversion results)

And src/core/exceptions.py with:
- ConversionError (base exception)
- ConversionCancelled 
- InvalidInputError
```

### Phase 3: Converter Refactoring

```
Refactor ORIGINAL_SCRIPT.py into src/core/converter.py:

1. Modify __init__ to accept:
   - settings: ConversionSettings
   - progress_callback: Optional[Callable[[ConversionProgress], None]]
   - cancel_event: Optional[threading.Event]

2. Add helper methods:
   - report_progress(phase, current, total, message)
   - check_cancelled()

3. Replace ALL print() calls with report_progress() calls

4. Modify run() to:
   - Call check_cancelled() at key points (after each phase, in loops)
   - Return ConversionResult instead of printing summary
   - Catch exceptions and return error result

5. Use self.settings instead of hardcoded values for:
   - json_path, output_dir
   - field IDs (project_field_id, etc.)
   - skip options (skip_readwise, skip_highlights, etc.)

Keep all the actual conversion logic identical - we're just adding the callback/settings layer.
```

### Phase 4: GUI Implementation

```
Create src/gui/app.py with the TanaToObsidianApp class:

- File picker for JSON input
- Folder picker for output directory  
- Checkboxes for options (download images, skip readwise, etc.)
- Progress bar
- Log/output text area
- Convert and Cancel buttons

Use CustomTkinter for modern styling.
Run conversion in a background thread.
Handle progress updates via self.after() to update UI from main thread.
```

### Phase 5: Entry Point and Testing

```
1. Create src/main.py as the entry point that:
   - Sets up CustomTkinter appearance
   - Creates and runs TanaToObsidianApp

2. Test it locally with:
   python -m src.main

3. Create build/build.py for PyInstaller packaging
```

## Debugging Prompts

If something isn't working:

```
The converter is failing with [error]. Check ORIGINAL_SCRIPT.py to see how the original handled this case, and make sure the refactored version preserves that logic.
```

```
The GUI freezes during conversion. Make sure:
1. The conversion runs in a threading.Thread with daemon=True
2. Progress updates use self.after(0, callback) to run on main thread
3. The cancel_event is checked regularly in the converter
```

```
The executable won't build. Check that:
1. All imports are explicit (no relative imports that break)
2. Assets are included via --add-data
3. Hidden imports are specified if needed
```

## Testing the Application

```
Test the application:

1. Run directly: python -m src.main
2. Test with a sample Tana export JSON
3. Verify:
   - File pickers work
   - Options are respected
   - Progress updates in real-time
   - Cancellation works
   - Error handling shows user-friendly messages
   - Output files are correct

Then build executable:
python build/build.py

Test the built executable on the current platform.
```
