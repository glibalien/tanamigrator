"""Main application window."""

import customtkinter as ctk
import threading
from pathlib import Path
from tkinter import messagebox
from typing import Optional

from src.core.converter import TanaToObsidian
from src.core.models import ConversionSettings, ConversionProgress, ConversionResult

from .styles import (
    WINDOW_TITLE,
    WINDOW_GEOMETRY,
    WINDOW_MIN_SIZE,
    PAD_X,
    PAD_Y,
)
from .components import (
    FilePickerFrame,
    OptionsFrame,
    ProgressFrame,
    LogFrame,
    ActionButtonsFrame,
)


class TanaToObsidianApp(ctk.CTk):
    """Main application window for Tana to Obsidian converter."""

    def __init__(self):
        super().__init__()

        # Window configuration
        self.title(WINDOW_TITLE)
        self.geometry(WINDOW_GEOMETRY)
        self.minsize(*WINDOW_MIN_SIZE)

        # State
        self.json_path: Optional[Path] = None
        self.output_dir: Optional[Path] = None
        self.conversion_thread: Optional[threading.Thread] = None
        self.cancel_event = threading.Event()

        # Build UI
        self._create_widgets()
        self._setup_layout()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self):
        """Create all UI widgets."""
        # File selection section
        self.file_frame = ctk.CTkFrame(self)

        self.json_picker = FilePickerFrame(
            self.file_frame,
            label_text="Tana Export JSON:",
            is_directory=False,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            on_change=self._on_json_selected
        )

        self.output_picker = FilePickerFrame(
            self.file_frame,
            label_text="Output Directory:",
            is_directory=True,
            on_change=self._on_output_selected
        )

        # Options section
        self.options_frame = OptionsFrame(self)

        # Progress section
        self.progress_frame = ProgressFrame(self)

        # Log section
        self.log_frame = LogFrame(self, height=160)

        # Action buttons
        self.action_frame = ActionButtonsFrame(
            self,
            on_convert=self._start_conversion,
            on_cancel=self._cancel_conversion
        )

    def _setup_layout(self):
        """Arrange widgets in the window."""
        # File selection
        self.file_frame.pack(fill="x", padx=PAD_X, pady=(PAD_Y + 5, PAD_Y))
        self.json_picker.pack(fill="x", pady=2)
        self.output_picker.pack(fill="x", pady=2)

        # Options
        self.options_frame.pack(fill="x", padx=PAD_X, pady=PAD_Y)

        # Progress
        self.progress_frame.pack(fill="x", padx=PAD_X, pady=PAD_Y)

        # Action buttons (pack before log so they're always visible)
        self.action_frame.pack(side="bottom", fill="x", padx=PAD_X, pady=(PAD_Y, PAD_Y + 5))

        # Log (expands to fill remaining space)
        self.log_frame.pack(fill="both", expand=True, padx=PAD_X, pady=PAD_Y)

    def _on_json_selected(self, path: Path):
        """Handle JSON file selection."""
        self.json_path = path
        self._log(f"Selected JSON: {path}")

        # Auto-suggest output directory if not set
        if not self.output_dir:
            suggested_output = path.parent / "ObsidianOutput"
            self.output_picker.set_path(suggested_output)
            self.output_dir = suggested_output
            self._log(f"Suggested output: {suggested_output}")

    def _on_output_selected(self, path: Path):
        """Handle output directory selection."""
        self.output_dir = path
        self._log(f"Selected output: {path}")

    def _start_conversion(self):
        """Start the conversion process."""
        # Validate inputs
        self.json_path = self.json_picker.get_path()
        self.output_dir = self.output_picker.get_path()

        if not self.json_path:
            messagebox.showerror("Error", "Please select a Tana export JSON file.")
            return

        if not self.output_dir:
            messagebox.showerror("Error", "Please select an output directory.")
            return

        if not self.json_path.exists():
            messagebox.showerror("Error", f"JSON file not found:\n{self.json_path}")
            return

        # Update UI state
        self.action_frame.set_converting(True)
        self.cancel_event.clear()
        self.log_frame.clear()
        self.progress_frame.reset()

        self._log(f"Starting conversion...")
        self._log(f"Input: {self.json_path}")
        self._log(f"Output: {self.output_dir}")

        # Build settings from UI
        options = self.options_frame.get_options()
        settings = ConversionSettings(
            json_path=self.json_path,
            output_dir=self.output_dir,
            download_images=options["download_images"],
            skip_readwise=options["skip_readwise"],
            skip_highlights=options["skip_highlights"],
            skip_week_nodes=options["skip_week_nodes"],
            skip_year_nodes=options["skip_year_nodes"],
            skip_field_definitions=options["skip_field_definitions"],
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
            # Update status label
            if progress.message:
                status_text = f"{progress.phase}: {progress.message}"
            else:
                status_text = progress.phase
            self.progress_frame.set_status(status_text)

            # Update progress bar
            if progress.total > 0:
                self.progress_frame.set_progress(progress.current / progress.total)

            # Log the progress
            self._log(f"[{progress.phase}] {progress.message}")

        # Schedule UI update on main thread
        self.after(0, update)

    def _on_complete(self, result: ConversionResult):
        """Handle conversion complete."""
        self.action_frame.set_converting(False)

        if result.success:
            self.progress_frame.set_progress(1.0)
            self.progress_frame.set_status("Conversion complete!")

            self._log("")
            self._log("=" * 40)
            self._log("CONVERSION COMPLETE")
            self._log("=" * 40)
            self._log(f"Daily notes exported: {result.daily_notes_count}")
            self._log(f"Blank daily notes skipped: {result.blank_daily_notes_skipped}")
            self._log(f"Tagged nodes: {result.tagged_nodes_count}")
            self._log(f"Orphan nodes: {result.orphan_nodes_count}")
            self._log(f"Referenced nodes: {result.referenced_nodes_count}")
            self._log(f"Images downloaded: {result.images_downloaded}")
            if result.image_errors:
                self._log(f"Image download errors: {len(result.image_errors)}")
            self._log(f"Files written: {result.files_written}")
            self._log(f"  - Single files: {result.single_files}")
            self._log(f"  - Merged files: {result.merged_files}")
            self._log("")
            self._log(f"Output directory: {self.output_dir}")

            messagebox.showinfo(
                "Success",
                f"Conversion complete!\n\n"
                f"Files written: {result.files_written}\n"
                f"Daily notes: {result.daily_notes_count}\n"
                f"Images downloaded: {result.images_downloaded}\n\n"
                f"Output: {self.output_dir}"
            )
        else:
            self.progress_frame.set_progress(0)
            self.progress_frame.set_status("Conversion failed")

            self._log("")
            self._log("=" * 40)
            self._log("CONVERSION FAILED")
            self._log("=" * 40)
            self._log(f"Error: {result.error_message}")

            messagebox.showerror(
                "Error",
                f"Conversion failed:\n\n{result.error_message}"
            )

    def _cancel_conversion(self):
        """Cancel the running conversion."""
        self.cancel_event.set()
        self._log("Cancellation requested...")
        self.progress_frame.set_status("Cancelling...")

    def _log(self, message: str):
        """Add a message to the log."""
        self.log_frame.log(message)

    def _on_close(self):
        """Handle window close."""
        if self.conversion_thread and self.conversion_thread.is_alive():
            if messagebox.askyesno(
                "Confirm Exit",
                "A conversion is in progress. Are you sure you want to exit?"
            ):
                self.cancel_event.set()
                self.destroy()
        else:
            self.destroy()
