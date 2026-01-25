"""Reusable UI components for the wizard-based interface."""

import customtkinter as ctk
from pathlib import Path
from tkinter import filedialog
from typing import Callable, Optional, List, Dict

from .styles import ENTRY_WIDTH, BUTTON_WIDTH, PAD_X, PAD_Y


class FilePickerFrame(ctk.CTkFrame):
    """A frame containing a label, entry, and browse button for file/folder selection."""

    def __init__(
        self,
        parent,
        label_text: str,
        is_directory: bool = False,
        filetypes: list = None,
        on_change: Optional[Callable[[Path], None]] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.is_directory = is_directory
        self.filetypes = filetypes or [("All files", "*.*")]
        self.on_change = on_change
        self.selected_path: Optional[Path] = None

        # Configure grid
        self.grid_columnconfigure(1, weight=1)

        # Label
        self.label = ctk.CTkLabel(self, text=label_text, width=140, anchor="w")
        self.label.grid(row=0, column=0, padx=(10, 5), pady=8, sticky="w")

        # Entry (read-only)
        self.entry = ctk.CTkEntry(self, width=ENTRY_WIDTH, state="readonly")
        self.entry.grid(row=0, column=1, padx=5, pady=8, sticky="ew")

        # Browse button
        self.button = ctk.CTkButton(
            self,
            text="Browse...",
            width=BUTTON_WIDTH,
            command=self._browse
        )
        self.button.grid(row=0, column=2, padx=(5, 10), pady=8)

    def _browse(self):
        """Open file/folder dialog and update the entry."""
        if self.is_directory:
            path = filedialog.askdirectory(title=f"Select {self.label.cget('text')}")
        else:
            path = filedialog.askopenfilename(
                title=f"Select {self.label.cget('text')}",
                filetypes=self.filetypes
            )

        if path:
            self.selected_path = Path(path)
            self.entry.configure(state="normal")
            self.entry.delete(0, "end")
            self.entry.insert(0, str(self.selected_path))
            self.entry.configure(state="readonly")

            if self.on_change:
                self.on_change(self.selected_path)

    def get_path(self) -> Optional[Path]:
        """Return the selected path or None."""
        return self.selected_path

    def set_path(self, path: Path):
        """Programmatically set the path."""
        self.selected_path = path
        self.entry.configure(state="normal")
        self.entry.delete(0, "end")
        self.entry.insert(0, str(path))
        self.entry.configure(state="readonly")


class StepIndicator(ctk.CTkFrame):
    """Shows current step in the wizard."""

    def __init__(self, parent, steps: List[str], **kwargs):
        super().__init__(parent, **kwargs)

        self.steps = steps
        self.current_step = 0
        self.step_labels = []

        for i, step_name in enumerate(steps):
            label = ctk.CTkLabel(
                self,
                text=f"{i + 1}. {step_name}",
                font=("", 12),
                text_color="gray"
            )
            label.pack(side="left", padx=15, pady=8)
            self.step_labels.append(label)

        self._update_display()

    def set_step(self, step: int):
        """Set the current step (0-indexed)."""
        self.current_step = step
        self._update_display()

    def _update_display(self):
        """Update label styles based on current step."""
        for i, label in enumerate(self.step_labels):
            if i < self.current_step:
                # Completed step
                label.configure(text_color="green")
            elif i == self.current_step:
                # Current step
                label.configure(text_color=("gray10", "gray90"), font=("", 12, "bold"))
            else:
                # Future step
                label.configure(text_color="gray", font=("", 12))


class SupertagSelectionFrame(ctk.CTkFrame):
    """Scrollable frame for selecting supertags to include."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # Header with select all/none buttons
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(
            header_frame,
            text="Select Supertags to Convert",
            font=("", 14, "bold")
        ).pack(side="left")

        ctk.CTkButton(
            header_frame,
            text="Select All",
            width=80,
            command=self._select_all
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            header_frame,
            text="Select None",
            width=80,
            command=self._select_none
        ).pack(side="right", padx=5)

        # Scrollable area
        self.scrollable = ctk.CTkScrollableFrame(self, height=350)
        self.scrollable.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        self.checkboxes: Dict[str, ctk.CTkCheckBox] = {}
        self.variables: Dict[str, ctk.BooleanVar] = {}

    def set_supertags(self, supertags: List['SupertagInfo']):
        """Populate the list with supertags."""
        # Clear existing
        for widget in self.scrollable.winfo_children():
            widget.destroy()
        self.checkboxes.clear()
        self.variables.clear()

        # Add supertags
        for info in supertags:
            # Determine default selection
            default_selected = info.special_type not in ('week', 'year', 'field-definition')

            var = ctk.BooleanVar(value=default_selected)
            self.variables[info.id] = var

            # Build display text
            display_text = f"#{info.name}"
            if info.instance_count > 0:
                display_text += f"  ({info.instance_count})"

            # Add special type indicator
            if info.special_type == 'day':
                display_text += "  [Daily Notes]"
            elif info.special_type == 'week':
                display_text += "  [Week - skipped by default]"
            elif info.special_type == 'year':
                display_text += "  [Year - skipped by default]"
            elif info.special_type == 'field-definition':
                display_text += "  [Field Definition - skipped]"

            # Create row frame for checkbox + field info
            row_frame = ctk.CTkFrame(self.scrollable, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)

            cb = ctk.CTkCheckBox(
                row_frame,
                text=display_text,
                variable=var,
                font=("", 12)
            )
            cb.pack(side="left", anchor="w")

            # Show field count if any
            if info.fields:
                field_types = []
                for f in info.fields:
                    if f.field_type == 'options_from_supertag':
                        field_types.append(f"links to #{f.source_supertag_name}")
                    elif f.field_type == 'system_done':
                        field_types.append("done status")

                if field_types:
                    field_text = f"  [{', '.join(field_types)}]"
                    ctk.CTkLabel(
                        row_frame,
                        text=field_text,
                        font=("", 11),
                        text_color="gray"
                    ).pack(side="left", padx=(5, 0))

            self.checkboxes[info.id] = cb

            # Disable field-definition checkbox
            if info.special_type == 'field-definition':
                cb.configure(state="disabled")
                var.set(False)

    def get_selected_ids(self) -> List[str]:
        """Return list of selected supertag IDs."""
        return [tag_id for tag_id, var in self.variables.items() if var.get()]

    def _select_all(self):
        """Select all supertags except field-definition."""
        for tag_id, var in self.variables.items():
            cb = self.checkboxes.get(tag_id)
            if cb and cb.cget("state") != "disabled":
                var.set(True)

    def _select_none(self):
        """Deselect all supertags."""
        for var in self.variables.values():
            var.set(False)


class GlobalOptionsFrame(ctk.CTkFrame):
    """Simplified options frame with only the essential options."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # Header
        self.header = ctk.CTkLabel(self, text="Options", font=("", 14, "bold"))
        self.header.pack(anchor="w", padx=15, pady=(12, 8))

        # Create checkbox variables
        self.download_images_var = ctk.BooleanVar(value=True)
        self.include_library_nodes_var = ctk.BooleanVar(value=True)

        # Create checkboxes
        self._create_checkbox("Download images from Firebase", self.download_images_var)
        self._create_checkbox("Include Library nodes without supertags", self.include_library_nodes_var)

    def _create_checkbox(self, text: str, variable: ctk.BooleanVar):
        """Create and pack a checkbox."""
        cb = ctk.CTkCheckBox(self, text=text, variable=variable)
        cb.pack(anchor="w", padx=25, pady=3)
        return cb

    def get_options(self) -> dict:
        """Return all option values as a dictionary."""
        return {
            "download_images": self.download_images_var.get(),
            "include_library_nodes": self.include_library_nodes_var.get(),
        }


class ProgressFrame(ctk.CTkFrame):
    """A frame containing progress label and progress bar."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # Status label
        self.status_label = ctk.CTkLabel(self, text="Ready", anchor="w")
        self.status_label.pack(fill="x", padx=15, pady=(12, 5))

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self, width=550)
        self.progress_bar.pack(fill="x", padx=15, pady=(0, 12))
        self.progress_bar.set(0)

    def set_status(self, text: str):
        """Update the status label."""
        self.status_label.configure(text=text)

    def set_progress(self, value: float):
        """Set progress bar value (0.0 to 1.0)."""
        self.progress_bar.set(max(0.0, min(1.0, value)))

    def reset(self):
        """Reset to initial state."""
        self.status_label.configure(text="Ready")
        self.progress_bar.set(0)


class LogFrame(ctk.CTkFrame):
    """A frame containing a scrollable log text area."""

    def __init__(self, parent, height: int = 180, **kwargs):
        super().__init__(parent, **kwargs)

        # Header
        self.header = ctk.CTkLabel(self, text="Log", font=("", 14, "bold"))
        self.header.pack(anchor="w", padx=15, pady=(12, 5))

        # Text box
        self.textbox = ctk.CTkTextbox(self, height=height, state="disabled")
        self.textbox.pack(fill="both", expand=True, padx=15, pady=(0, 12))

    def log(self, message: str):
        """Append a message to the log."""
        self.textbox.configure(state="normal")
        self.textbox.insert("end", message + "\n")
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def clear(self):
        """Clear the log."""
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")


class WizardNavigationFrame(ctk.CTkFrame):
    """Navigation buttons for the wizard (Back, Next, Convert)."""

    def __init__(
        self,
        parent,
        on_back: Callable,
        on_next: Callable,
        on_convert: Callable,
        on_cancel: Callable,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.on_back = on_back
        self.on_next = on_next
        self.on_convert = on_convert
        self.on_cancel = on_cancel

        # Back button
        self.back_button = ctk.CTkButton(
            self,
            text="< Back",
            width=100,
            command=on_back
        )
        self.back_button.pack(side="left", padx=(15, 10), pady=12)

        # Cancel button (for conversion step)
        self.cancel_button = ctk.CTkButton(
            self,
            text="Cancel",
            width=100,
            command=on_cancel,
            state="disabled"
        )
        self.cancel_button.pack(side="left", padx=10, pady=12)

        # Convert button (shown on final step)
        self.convert_button = ctk.CTkButton(
            self,
            text="Convert",
            width=120,
            command=on_convert,
            fg_color="green",
            hover_color="darkgreen"
        )
        self.convert_button.pack(side="right", padx=(10, 15), pady=12)

        # Next button
        self.next_button = ctk.CTkButton(
            self,
            text="Next >",
            width=100,
            command=on_next
        )
        self.next_button.pack(side="right", padx=10, pady=12)

    def set_step(self, step: int, total_steps: int, is_converting: bool = False):
        """Update button states based on current step."""
        # Back button
        if step == 0 or is_converting:
            self.back_button.configure(state="disabled")
        else:
            self.back_button.configure(state="normal")

        # Next button
        if step >= total_steps - 1 or is_converting:
            self.next_button.pack_forget()
        else:
            self.next_button.pack(side="right", padx=10, pady=12)
            self.next_button.configure(state="normal")

        # Convert button
        if step == total_steps - 1 and not is_converting:
            self.convert_button.pack(side="right", padx=(10, 15), pady=12)
            self.convert_button.configure(state="normal")
        elif is_converting:
            self.convert_button.pack(side="right", padx=(10, 15), pady=12)
            self.convert_button.configure(state="disabled")
        else:
            self.convert_button.pack_forget()

        # Cancel button
        if is_converting:
            self.cancel_button.configure(state="normal")
        else:
            self.cancel_button.configure(state="disabled")


# Legacy compatibility - keep old OptionsFrame for backward compatibility
class OptionsFrame(ctk.CTkFrame):
    """Legacy options frame - replaced by GlobalOptionsFrame in wizard."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.header = ctk.CTkLabel(self, text="Options", font=("", 14, "bold"))
        self.header.pack(anchor="w", padx=15, pady=(12, 8))

        self.download_images_var = ctk.BooleanVar(value=True)
        self.skip_readwise_var = ctk.BooleanVar(value=True)
        self.skip_highlights_var = ctk.BooleanVar(value=True)
        self.skip_week_nodes_var = ctk.BooleanVar(value=True)
        self.skip_year_nodes_var = ctk.BooleanVar(value=True)
        self.skip_field_definitions_var = ctk.BooleanVar(value=True)

        self._create_checkbox("Download images from Firebase", self.download_images_var)
        self._create_checkbox("Skip Readwise nodes", self.skip_readwise_var)
        self._create_checkbox("Skip Highlight nodes", self.skip_highlights_var)
        self._create_checkbox("Skip Week nodes", self.skip_week_nodes_var)
        self._create_checkbox("Skip Year nodes", self.skip_year_nodes_var)
        self._create_checkbox("Skip Field Definition nodes", self.skip_field_definitions_var)

    def _create_checkbox(self, text: str, variable: ctk.BooleanVar):
        cb = ctk.CTkCheckBox(self, text=text, variable=variable)
        cb.pack(anchor="w", padx=25, pady=3)
        return cb

    def get_options(self) -> dict:
        return {
            "download_images": self.download_images_var.get(),
            "skip_readwise": self.skip_readwise_var.get(),
            "skip_highlights": self.skip_highlights_var.get(),
            "skip_week_nodes": self.skip_week_nodes_var.get(),
            "skip_year_nodes": self.skip_year_nodes_var.get(),
            "skip_field_definitions": self.skip_field_definitions_var.get(),
        }


class ActionButtonsFrame(ctk.CTkFrame):
    """Legacy action buttons - for backward compatibility."""

    def __init__(
        self,
        parent,
        on_convert: Callable,
        on_cancel: Callable,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.convert_button = ctk.CTkButton(
            self,
            text="Convert",
            width=150,
            command=on_convert
        )
        self.convert_button.pack(side="left", padx=(15, 10), pady=12)

        self.cancel_button = ctk.CTkButton(
            self,
            text="Cancel",
            width=150,
            command=on_cancel,
            state="disabled"
        )
        self.cancel_button.pack(side="left", padx=10, pady=12)

    def set_converting(self, is_converting: bool):
        if is_converting:
            self.convert_button.configure(state="disabled")
            self.cancel_button.configure(state="normal")
        else:
            self.convert_button.configure(state="normal")
            self.cancel_button.configure(state="disabled")
