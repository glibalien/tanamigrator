"""Main application window with wizard-based interface."""

import customtkinter as ctk
import threading
from pathlib import Path
from tkinter import messagebox
from typing import Optional, List, Dict

from src.core.converter import TanaToObsidian
from src.core.scanner import TanaExportScanner
from src.core.models import (
    ConversionSettings,
    ConversionProgress,
    ConversionResult,
    SupertagInfo,
    SupertagConfig,
    create_default_supertag_config,
)

from .styles import (
    WINDOW_TITLE,
    WINDOW_GEOMETRY,
    WINDOW_MIN_SIZE,
    PAD_X,
    PAD_Y,
)
from .components import (
    FilePickerFrame,
    StepIndicator,
    SupertagSelectionFrame,
    GlobalOptionsFrame,
    ProgressFrame,
    LogFrame,
    WizardNavigationFrame,
)


class TanaToObsidianApp(ctk.CTk):
    """Main application window with wizard-based conversion flow."""

    STEPS = ["Select File", "Select Supertags", "Convert"]

    def __init__(self):
        super().__init__()

        # Window configuration
        self.title(WINDOW_TITLE)
        self.geometry(WINDOW_GEOMETRY)
        self.minsize(*WINDOW_MIN_SIZE)

        # Wizard state
        self.current_step = 0
        self.json_path: Optional[Path] = None
        self.output_dir: Optional[Path] = None
        self.supertag_infos: List[SupertagInfo] = []
        self.supertag_configs: Dict[str, SupertagConfig] = {}

        # Conversion state
        self.conversion_thread: Optional[threading.Thread] = None
        self.cancel_event = threading.Event()
        self.is_converting = False

        # Build UI
        self._create_widgets()
        self._setup_layout()
        self._show_step(0)

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self):
        """Create all UI widgets."""
        # Step indicator at top
        self.step_indicator = StepIndicator(self, steps=self.STEPS)

        # Content frames for each step (will be shown/hidden)
        self.step_frames = []

        # Step 1: File selection
        self.step1_frame = ctk.CTkFrame(self)
        self._create_step1_content()
        self.step_frames.append(self.step1_frame)

        # Step 2: Supertag selection
        self.step2_frame = ctk.CTkFrame(self)
        self._create_step2_content()
        self.step_frames.append(self.step2_frame)

        # Step 3: Options and conversion
        self.step3_frame = ctk.CTkFrame(self)
        self._create_step3_content()
        self.step_frames.append(self.step3_frame)

        # Navigation buttons (always visible at bottom)
        self.nav_frame = WizardNavigationFrame(
            self,
            on_back=self._go_back,
            on_next=self._go_next,
            on_convert=self._start_conversion,
            on_cancel=self._cancel_conversion,
        )

    def _create_step1_content(self):
        """Create content for Step 1: File Selection."""
        # Title
        ctk.CTkLabel(
            self.step1_frame,
            text="Select Tana Export File",
            font=("", 18, "bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            self.step1_frame,
            text="Choose your Tana JSON export file to begin the conversion process.",
            font=("", 12),
            text_color="gray"
        ).pack(anchor="w", padx=20, pady=(0, 20))

        # File picker
        self.json_picker = FilePickerFrame(
            self.step1_frame,
            label_text="Tana Export JSON:",
            is_directory=False,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            on_change=self._on_json_selected
        )
        self.json_picker.pack(fill="x", padx=10, pady=10)

        # Status area
        self.step1_status = ctk.CTkLabel(
            self.step1_frame,
            text="",
            font=("", 12),
            text_color="gray"
        )
        self.step1_status.pack(anchor="w", padx=20, pady=20)

    def _create_step2_content(self):
        """Create content for Step 2: Supertag Selection."""
        # Title
        ctk.CTkLabel(
            self.step2_frame,
            text="Select Supertags to Convert",
            font=("", 18, "bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            self.step2_frame,
            text="Choose which supertags to include in the conversion. Field mappings are auto-configured.",
            font=("", 12),
            text_color="gray"
        ).pack(anchor="w", padx=20, pady=(0, 10))

        # Supertag selection list
        self.supertag_selection = SupertagSelectionFrame(self.step2_frame)
        self.supertag_selection.pack(fill="both", expand=True, padx=10, pady=10)

    def _create_step3_content(self):
        """Create content for Step 3: Options and Conversion."""
        # Title
        ctk.CTkLabel(
            self.step3_frame,
            text="Configure and Convert",
            font=("", 18, "bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))

        # Output directory picker
        self.output_picker = FilePickerFrame(
            self.step3_frame,
            label_text="Output Directory:",
            is_directory=True,
            on_change=self._on_output_selected
        )
        self.output_picker.pack(fill="x", padx=10, pady=10)

        # Options
        self.options_frame = GlobalOptionsFrame(self.step3_frame)
        self.options_frame.pack(fill="x", padx=10, pady=10)

        # Progress
        self.progress_frame = ProgressFrame(self.step3_frame)
        self.progress_frame.pack(fill="x", padx=10, pady=10)

        # Log
        self.log_frame = LogFrame(self.step3_frame, height=150)
        self.log_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def _setup_layout(self):
        """Arrange widgets in the window."""
        # Step indicator at top
        self.step_indicator.pack(fill="x", padx=PAD_X, pady=(PAD_Y, 0))

        # Navigation at bottom (pack first so it's always visible)
        self.nav_frame.pack(side="bottom", fill="x", padx=PAD_X, pady=(PAD_Y, PAD_Y + 5))

        # Step frames fill the middle
        for frame in self.step_frames:
            frame.pack(fill="both", expand=True, padx=PAD_X, pady=PAD_Y)
            frame.pack_forget()  # Hide initially

    def _show_step(self, step: int):
        """Show the specified step and hide others."""
        self.current_step = step

        # Update step indicator
        self.step_indicator.set_step(step)

        # Show/hide step frames
        for i, frame in enumerate(self.step_frames):
            if i == step:
                frame.pack(fill="both", expand=True, padx=PAD_X, pady=PAD_Y)
            else:
                frame.pack_forget()

        # Update navigation buttons
        self.nav_frame.set_step(step, len(self.STEPS), self.is_converting)

    def _on_json_selected(self, path: Path):
        """Handle JSON file selection."""
        self.json_path = path
        self.step1_status.configure(text=f"Selected: {path.name}")

        # Auto-suggest output directory
        if not self.output_dir:
            suggested_output = path.parent / "ObsidianOutput"
            self.output_picker.set_path(suggested_output)
            self.output_dir = suggested_output

    def _on_output_selected(self, path: Path):
        """Handle output directory selection."""
        self.output_dir = path

    def _go_back(self):
        """Navigate to previous step."""
        if self.current_step > 0:
            self._show_step(self.current_step - 1)

    def _go_next(self):
        """Navigate to next step."""
        # Validate current step before proceeding
        if self.current_step == 0:
            if not self._validate_step1():
                return
            # Scan the file before moving to step 2
            self._scan_export()

        elif self.current_step == 1:
            if not self._validate_step2():
                return

        if self.current_step < len(self.STEPS) - 1:
            self._show_step(self.current_step + 1)

    def _validate_step1(self) -> bool:
        """Validate Step 1: File selection."""
        self.json_path = self.json_picker.get_path()

        if not self.json_path:
            messagebox.showerror("Error", "Please select a Tana export JSON file.")
            return False

        if not self.json_path.exists():
            messagebox.showerror("Error", f"File not found:\n{self.json_path}")
            return False

        return True

    def _validate_step2(self) -> bool:
        """Validate Step 2: Supertag selection."""
        selected = self.supertag_selection.get_selected_ids()

        if not selected:
            messagebox.showerror("Error", "Please select at least one supertag to convert.")
            return False

        # Build supertag configs based on selection
        self._build_supertag_configs(selected)
        return True

    def _scan_export(self):
        """Scan the Tana export to discover supertags."""
        self.step1_status.configure(text="Scanning export file...")
        self.update()

        try:
            scanner = TanaExportScanner(
                self.json_path,
                progress_callback=lambda p: self.after(0, lambda: self.step1_status.configure(
                    text=f"Scanning: {p.message}"
                ))
            )
            self.supertag_infos = scanner.scan()

            # Populate the supertag selection list
            self.supertag_selection.set_supertags(self.supertag_infos)

            self.step1_status.configure(
                text=f"Found {len(self.supertag_infos)} supertags. Click Next to continue."
            )

        except Exception as e:
            messagebox.showerror("Scan Error", f"Failed to scan export:\n{str(e)}")
            self.step1_status.configure(text=f"Scan failed: {str(e)}")

    def _build_supertag_configs(self, selected_ids: List[str]):
        """Build SupertagConfig objects for selected supertags."""
        self.supertag_configs.clear()

        # Build a lookup for supertag infos
        info_by_id = {info.id: info for info in self.supertag_infos}

        for tag_id in selected_ids:
            info = info_by_id.get(tag_id)
            if info:
                # Create default config with auto-generated field mappings
                config = create_default_supertag_config(info)
                config.include = True  # Override since user selected it
                self.supertag_configs[tag_id] = config

    def _start_conversion(self):
        """Start the conversion process."""
        # Validate output directory
        self.output_dir = self.output_picker.get_path()

        if not self.output_dir:
            messagebox.showerror("Error", "Please select an output directory.")
            return

        # Update UI state
        self.is_converting = True
        self.nav_frame.set_step(self.current_step, len(self.STEPS), True)
        self.cancel_event.clear()
        self.log_frame.clear()
        self.progress_frame.reset()

        self._log("Starting conversion...")
        self._log(f"Input: {self.json_path}")
        self._log(f"Output: {self.output_dir}")
        self._log(f"Supertags selected: {len(self.supertag_configs)}")

        # Build settings
        options = self.options_frame.get_options()
        settings = ConversionSettings(
            json_path=self.json_path,
            output_dir=self.output_dir,
            supertag_configs=list(self.supertag_configs.values()),
            download_images=options["download_images"],
            skip_week_nodes=options["skip_week_nodes"],
            skip_year_nodes=options["skip_year_nodes"],
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
        self.is_converting = False
        self.nav_frame.set_step(self.current_step, len(self.STEPS), False)

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
