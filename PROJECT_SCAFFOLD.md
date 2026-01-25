# Tana to Obsidian - Cross-Platform Desktop Application

## Project Overview

Convert the existing `tana_to_obsidian.py` script into a cross-platform desktop application using Python with CustomTkinter for the GUI and PyInstaller for packaging.

## Target Platforms
- Windows 10/11
- macOS 12+
- Linux (Ubuntu 22.04+, other major distros)

## Technology Stack
- **Python 3.11+**
- **CustomTkinter** - Modern-looking Tkinter wrapper for the GUI
- **PyInstaller** - For creating standalone executables
- **Threading** - For non-blocking UI during conversion

## Project Structure

```
tana-to-obsidian/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Application entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── converter.py        # Main TanaToObsidian class (refactored)
│   │   ├── models.py           # Data classes for configuration
│   │   └── exceptions.py       # Custom exceptions
│   └── gui/
│       ├── __init__.py
│       ├── app.py              # Main application window
│       ├── components.py       # Reusable UI components
│       └── styles.py           # Theme and styling constants
├── assets/
│   ├── icon.ico                # Windows icon
│   ├── icon.icns               # macOS icon
│   └── icon.png                # Linux icon / source
├── tests/
│   ├── __init__.py
│   ├── test_converter.py
│   └── fixtures/
│       └── sample_tana_export.json
├── build/
│   └── build.py                # PyInstaller build script
├── requirements.txt
├── pyproject.toml
├── README.md
└── ORIGINAL_SCRIPT.py          # The original script for reference
```

## Architecture

### Core Module (`src/core/`)

The converter logic should be refactored to:

1. **Emit progress via callbacks** instead of print statements
2. **Be configurable** via a settings dataclass
3. **Raise typed exceptions** for error handling
4. **Support cancellation** via a threading event

#### models.py

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

@dataclass
class ConversionSettings:
    """User-configurable conversion options."""
    json_path: Path
    output_dir: Path
    
    # Export options
    download_images: bool = True
    skip_readwise: bool = True
    skip_week_nodes: bool = True
    skip_year_nodes: bool = True
    skip_highlights: bool = True
    skip_field_definitions: bool = True
    
    # Field ID overrides (for users with different Tana setups)
    project_field_id: str = 'zaD_EkMhKP'
    people_involved_field_id: str = 'znaT5AHKXQkR'
    company_field_id: str = 'LNd_B370Hr'
    cookbook_field_id: str = 'Y_572Dtvp_QO'
    url_field_id: str = 'SYS_A78'

@dataclass
class ConversionProgress:
    """Progress update sent to GUI."""
    phase: str                    # e.g., "Loading", "Building indices", "Exporting daily notes"
    current: int = 0
    total: int = 0
    message: str = ""
    
@dataclass 
class ConversionResult:
    """Final result of conversion."""
    success: bool
    daily_notes_count: int = 0
    tagged_nodes_count: int = 0
    orphan_nodes_count: int = 0
    referenced_nodes_count: int = 0
    images_downloaded: int = 0
    image_errors: list = field(default_factory=list)
    files_written: int = 0
    error_message: str = ""
```

#### converter.py changes

Refactor the existing `TanaToObsidian` class:

```python
class TanaToObsidian:
    def __init__(
        self, 
        settings: ConversionSettings,
        progress_callback: Optional[Callable[[ConversionProgress], None]] = None,
        cancel_event: Optional[threading.Event] = None
    ):
        self.settings = settings
        self.progress_callback = progress_callback
        self.cancel_event = cancel_event
        # ... rest of initialization
    
    def report_progress(self, phase: str, current: int = 0, total: int = 0, message: str = ""):
        """Send progress update to GUI."""
        if self.progress_callback:
            self.progress_callback(ConversionProgress(phase, current, total, message))
    
    def check_cancelled(self):
        """Check if user requested cancellation."""
        if self.cancel_event and self.cancel_event.is_set():
            raise ConversionCancelled("Conversion cancelled by user")
    
    def run(self) -> ConversionResult:
        """Main export process with progress reporting."""
        try:
            self.report_progress("Loading", message="Loading Tana export file...")
            self.load_data()
            self.check_cancelled()
            
            self.report_progress("Indexing", message="Building indices...")
            self.build_indices()
            self.check_cancelled()
            
            # ... etc, inserting progress reports and cancellation checks
            
            return ConversionResult(
                success=True,
                daily_notes_count=daily_count,
                # ... etc
            )
        except ConversionCancelled:
            return ConversionResult(success=False, error_message="Cancelled by user")
        except Exception as e:
            return ConversionResult(success=False, error_message=str(e))
```

### GUI Module (`src/gui/`)

#### app.py - Main Application Window

```python
import customtkinter as ctk
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

from src.core.converter import TanaToObsidian
from src.core.models import ConversionSettings, ConversionProgress, ConversionResult

class TanaToObsidianApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Tana to Obsidian Converter")
        self.geometry("700x600")
        self.minsize(600, 500)
        
        # State
        self.json_path: Path = None
        self.output_dir: Path = None
        self.conversion_thread: threading.Thread = None
        self.cancel_event = threading.Event()
        
        self._create_widgets()
        self._setup_layout()
    
    def _create_widgets(self):
        # File selection frame
        self.file_frame = ctk.CTkFrame(self)
        
        # JSON file picker
        self.json_label = ctk.CTkLabel(self.file_frame, text="Tana Export JSON:")
        self.json_entry = ctk.CTkEntry(self.file_frame, width=400, state="readonly")
        self.json_button = ctk.CTkButton(
            self.file_frame, text="Browse...", width=100,
            command=self._browse_json
        )
        
        # Output directory picker
        self.output_label = ctk.CTkLabel(self.file_frame, text="Output Directory:")
        self.output_entry = ctk.CTkEntry(self.file_frame, width=400, state="readonly")
        self.output_button = ctk.CTkButton(
            self.file_frame, text="Browse...", width=100,
            command=self._browse_output
        )
        
        # Options frame
        self.options_frame = ctk.CTkFrame(self)
        self.options_label = ctk.CTkLabel(self.options_frame, text="Options", font=("", 14, "bold"))
        
        self.download_images_var = ctk.BooleanVar(value=True)
        self.download_images_cb = ctk.CTkCheckBox(
            self.options_frame, text="Download images from Firebase",
            variable=self.download_images_var
        )
        
        self.skip_readwise_var = ctk.BooleanVar(value=True)
        self.skip_readwise_cb = ctk.CTkCheckBox(
            self.options_frame, text="Skip Readwise nodes",
            variable=self.skip_readwise_var
        )
        
        self.skip_highlights_var = ctk.BooleanVar(value=True)
        self.skip_highlights_cb = ctk.CTkCheckBox(
            self.options_frame, text="Skip Highlight nodes",
            variable=self.skip_highlights_var
        )
        
        # Progress frame
        self.progress_frame = ctk.CTkFrame(self)
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="Ready")
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=500)
        self.progress_bar.set(0)
        
        # Log output
        self.log_text = ctk.CTkTextbox(self, width=650, height=200)
        
        # Action buttons
        self.button_frame = ctk.CTkFrame(self)
        self.convert_button = ctk.CTkButton(
            self.button_frame, text="Convert", width=150,
            command=self._start_conversion
        )
        self.cancel_button = ctk.CTkButton(
            self.button_frame, text="Cancel", width=150,
            command=self._cancel_conversion, state="disabled"
        )
    
    def _browse_json(self):
        path = filedialog.askopenfilename(
            title="Select Tana Export JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if path:
            self.json_path = Path(path)
            self.json_entry.configure(state="normal")
            self.json_entry.delete(0, "end")
            self.json_entry.insert(0, str(self.json_path))
            self.json_entry.configure(state="readonly")
    
    def _browse_output(self):
        path = filedialog.askdirectory(title="Select Output Directory")
        if path:
            self.output_dir = Path(path)
            self.output_entry.configure(state="normal")
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, str(self.output_dir))
            self.output_entry.configure(state="readonly")
    
    def _start_conversion(self):
        if not self.json_path or not self.output_dir:
            messagebox.showerror("Error", "Please select both input file and output directory")
            return
        
        # Update UI state
        self.convert_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.cancel_event.clear()
        self.log_text.delete("1.0", "end")
        
        # Build settings
        settings = ConversionSettings(
            json_path=self.json_path,
            output_dir=self.output_dir,
            download_images=self.download_images_var.get(),
            skip_readwise=self.skip_readwise_var.get(),
            skip_highlights=self.skip_highlights_var.get(),
        )
        
        # Start conversion in background thread
        self.conversion_thread = threading.Thread(
            target=self._run_conversion,
            args=(settings,),
            daemon=True
        )
        self.conversion_thread.start()
    
    def _run_conversion(self, settings: ConversionSettings):
        """Run conversion in background thread."""
        converter = TanaToObsidian(
            settings=settings,
            progress_callback=self._on_progress,
            cancel_event=self.cancel_event
        )
        result = converter.run()
        
        # Update UI on main thread
        self.after(0, lambda: self._on_complete(result))
    
    def _on_progress(self, progress: ConversionProgress):
        """Handle progress update from converter (called from background thread)."""
        def update():
            self.progress_label.configure(text=f"{progress.phase}: {progress.message}")
            if progress.total > 0:
                self.progress_bar.set(progress.current / progress.total)
            self._log(f"[{progress.phase}] {progress.message}")
        
        self.after(0, update)
    
    def _on_complete(self, result: ConversionResult):
        """Handle conversion complete."""
        self.convert_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        self.progress_bar.set(1 if result.success else 0)
        
        if result.success:
            self.progress_label.configure(text="Conversion complete!")
            self._log(f"\n=== Conversion Complete ===")
            self._log(f"Daily notes: {result.daily_notes_count}")
            self._log(f"Tagged nodes: {result.tagged_nodes_count}")
            self._log(f"Orphan nodes: {result.orphan_nodes_count}")
            self._log(f"Referenced nodes: {result.referenced_nodes_count}")
            self._log(f"Images downloaded: {result.images_downloaded}")
            self._log(f"Files written: {result.files_written}")
            messagebox.showinfo("Success", f"Conversion complete!\n\n{result.files_written} files written to:\n{self.output_dir}")
        else:
            self.progress_label.configure(text="Conversion failed")
            self._log(f"\n=== Error ===\n{result.error_message}")
            messagebox.showerror("Error", f"Conversion failed:\n{result.error_message}")
    
    def _cancel_conversion(self):
        self.cancel_event.set()
        self._log("Cancellation requested...")
    
    def _log(self, message: str):
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
    
    def _setup_layout(self):
        # Use grid layout
        self.file_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        self.json_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.json_entry.grid(row=0, column=1, padx=10, pady=5)
        self.json_button.grid(row=0, column=2, padx=10, pady=5)
        
        self.output_label.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.output_entry.grid(row=1, column=1, padx=10, pady=5)
        self.output_button.grid(row=1, column=2, padx=10, pady=5)
        
        self.options_frame.pack(fill="x", padx=20, pady=10)
        self.options_label.pack(anchor="w", padx=10, pady=(10, 5))
        self.download_images_cb.pack(anchor="w", padx=20, pady=2)
        self.skip_readwise_cb.pack(anchor="w", padx=20, pady=2)
        self.skip_highlights_cb.pack(anchor="w", padx=20, pady=2)
        
        self.progress_frame.pack(fill="x", padx=20, pady=10)
        self.progress_label.pack(anchor="w", padx=10, pady=5)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        
        self.log_text.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.button_frame.pack(fill="x", padx=20, pady=(10, 20))
        self.convert_button.pack(side="left", padx=10)
        self.cancel_button.pack(side="left", padx=10)
```

#### main.py - Entry Point

```python
import customtkinter as ctk
from src.gui.app import TanaToObsidianApp

def main():
    # Set appearance mode and theme
    ctk.set_appearance_mode("system")  # "light", "dark", or "system"
    ctk.set_default_color_theme("blue")
    
    app = TanaToObsidianApp()
    app.mainloop()

if __name__ == "__main__":
    main()
```

### Build Configuration

#### requirements.txt

```
customtkinter>=5.2.0
pyinstaller>=6.0.0
```

#### pyproject.toml

```toml
[project]
name = "tana-to-obsidian"
version = "1.0.0"
description = "Convert Tana exports to Obsidian markdown"
requires-python = ">=3.11"
dependencies = [
    "customtkinter>=5.2.0",
]

[project.optional-dependencies]
dev = [
    "pyinstaller>=6.0.0",
    "pytest>=7.0.0",
]

[project.scripts]
tana-to-obsidian = "src.main:main"

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"
```

#### build/build.py

```python
#!/usr/bin/env python3
"""Build script for creating standalone executables."""

import platform
import subprocess
import sys
from pathlib import Path

def build():
    system = platform.system().lower()
    project_root = Path(__file__).parent.parent
    
    # Base PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "TanaToObsidian",
        "--add-data", f"assets{':' if system != 'windows' else ';'}assets",
    ]
    
    # Platform-specific options
    if system == "windows":
        cmd.extend(["--icon", "assets/icon.ico"])
    elif system == "darwin":
        cmd.extend(["--icon", "assets/icon.icns"])
    else:
        cmd.extend(["--icon", "assets/icon.png"])
    
    # Entry point
    cmd.append("src/main.py")
    
    print(f"Building for {system}...")
    print(f"Command: {' '.join(cmd)}")
    
    subprocess.run(cmd, cwd=project_root, check=True)
    
    print(f"\nBuild complete! Executable in: {project_root}/dist/")

if __name__ == "__main__":
    build()
```

## Implementation Tasks

### Phase 1: Project Setup
1. Create the directory structure
2. Set up pyproject.toml and requirements.txt
3. Copy the original script as ORIGINAL_SCRIPT.py for reference

### Phase 2: Core Refactoring
1. Create models.py with dataclasses
2. Create exceptions.py with custom exceptions
3. Refactor converter.py:
   - Accept ConversionSettings instead of hardcoded paths
   - Add progress_callback parameter
   - Add cancel_event parameter
   - Replace all print() calls with report_progress()
   - Add check_cancelled() calls at key points
   - Return ConversionResult instead of printing summary
   - Use settings for configurable field IDs

### Phase 3: GUI Implementation
1. Create the main application window (app.py)
2. Implement file/folder pickers
3. Implement options checkboxes
4. Implement progress bar and log output
5. Implement threading for background conversion
6. Handle cancellation gracefully

### Phase 4: Testing
1. Create sample Tana export fixture
2. Write unit tests for converter logic
3. Manual testing on Windows, macOS, Linux

### Phase 5: Packaging
1. Create icons for each platform
2. Configure PyInstaller build script
3. Build and test executables on each platform
4. Create release artifacts

## Key Refactoring Points in Original Script

The original script has these areas that need modification:

1. **Lines 24-68**: `__init__` - Accept ConversionSettings, callbacks, cancel_event
2. **Lines 69-77**: `load_data` - Add progress reporting
3. **Lines 79-268**: `build_indices` - Add progress reporting, use settings for field IDs
4. **Lines 1553-1728**: `run` - Major refactor for progress reporting, cancellation, return result
5. **Lines 1731-1738**: Remove hardcoded paths, this becomes the GUI's responsibility

## Notes

- Keep the existing conversion logic intact as much as possible
- The converter should work identically whether called from GUI or CLI
- All print statements become progress callbacks
- The GUI should remain responsive during conversion (threading)
- Users should be able to cancel long-running conversions
- Error handling should be graceful with user-friendly messages

---

## Optionality Refactor (v2.0)

See `OPTIONALITY_REFACTOR_PLAN.md` for full implementation details.

### Summary of Changes

The app evolves from a simple file-selection flow to a multi-step wizard:

1. **File Selection** → User provides Tana export JSON
2. **Supertag Selection** → App scans JSON, user selects which supertags to include
3. **Field Mapping** → User configures per-supertag field → frontmatter mappings
4. **Options & Output** → Output directory + global options
5. **Conversion** → Progress tracking with cancel support

### New Project Structure

```
src/
├── main.py
├── core/
│   ├── converter.py     # Updated for dynamic field mapping
│   ├── scanner.py       # NEW: Scans export for supertags/fields
│   ├── models.py        # Updated with new dataclasses
│   └── exceptions.py
└── gui/
    ├── app.py           # Updated for wizard flow
    ├── components.py    # New wizard components
    └── styles.py
```

### Key New Data Models

```python
@dataclass
class SupertagInfo:
    id: str
    name: str
    instance_count: int
    fields: List[FieldInfo]
    is_system: bool
    special_type: Optional[str]  # 'day', 'week', 'year'

@dataclass
class FieldInfo:
    id: str
    name: str
    field_type: str  # 'plain', 'options_from_supertag', 'system_done'
    source_supertag_id: Optional[str]
    source_supertag_name: Optional[str]

@dataclass
class FieldMapping:
    field_id: str
    frontmatter_name: str
    include: bool
    transform: str  # 'none', 'wikilink', 'status'

@dataclass
class SupertagConfig:
    supertag_id: str
    include: bool
    field_mappings: List[FieldMapping]
```

### Default Behaviors

- **Done field**: Maps to `status` frontmatter ("done"/"open")
- **Options-from-supertag fields**: Generate `[[wikilinks]]` to target markdown
- **#day nodes**: Convert to Daily Notes
- **#week, #year**: Skipped by default
- **#field-definition**: Always skipped

### Removed Options

- Skip Readwise nodes (removed from UI)
- Skip Highlight nodes (removed from UI)
- Skip Field Definition nodes (handled automatically)
- Hardcoded field IDs in ConversionSettings
