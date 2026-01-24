"""Reusable UI components."""

import customtkinter as ctk
from pathlib import Path
from tkinter import filedialog
from typing import Callable, Optional

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


class OptionsFrame(ctk.CTkFrame):
    """A frame containing configuration checkboxes."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # Header
        self.header = ctk.CTkLabel(self, text="Options", font=("", 14, "bold"))
        self.header.pack(anchor="w", padx=15, pady=(12, 8))

        # Create checkbox variables
        self.download_images_var = ctk.BooleanVar(value=True)
        self.skip_readwise_var = ctk.BooleanVar(value=True)
        self.skip_highlights_var = ctk.BooleanVar(value=True)
        self.skip_week_nodes_var = ctk.BooleanVar(value=True)
        self.skip_year_nodes_var = ctk.BooleanVar(value=True)
        self.skip_field_definitions_var = ctk.BooleanVar(value=True)

        # Create checkboxes
        self._create_checkbox("Download images from Firebase", self.download_images_var)
        self._create_checkbox("Skip Readwise nodes", self.skip_readwise_var)
        self._create_checkbox("Skip Highlight nodes", self.skip_highlights_var)
        self._create_checkbox("Skip Week nodes", self.skip_week_nodes_var)
        self._create_checkbox("Skip Year nodes", self.skip_year_nodes_var)
        self._create_checkbox("Skip Field Definition nodes", self.skip_field_definitions_var)

    def _create_checkbox(self, text: str, variable: ctk.BooleanVar):
        """Create and pack a checkbox."""
        cb = ctk.CTkCheckBox(self, text=text, variable=variable)
        cb.pack(anchor="w", padx=25, pady=3)
        return cb

    def get_options(self) -> dict:
        """Return all option values as a dictionary."""
        return {
            "download_images": self.download_images_var.get(),
            "skip_readwise": self.skip_readwise_var.get(),
            "skip_highlights": self.skip_highlights_var.get(),
            "skip_week_nodes": self.skip_week_nodes_var.get(),
            "skip_year_nodes": self.skip_year_nodes_var.get(),
            "skip_field_definitions": self.skip_field_definitions_var.get(),
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


class ActionButtonsFrame(ctk.CTkFrame):
    """A frame containing the Convert and Cancel buttons."""

    def __init__(
        self,
        parent,
        on_convert: Callable,
        on_cancel: Callable,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        # Convert button
        self.convert_button = ctk.CTkButton(
            self,
            text="Convert",
            width=150,
            command=on_convert
        )
        self.convert_button.pack(side="left", padx=(15, 10), pady=12)

        # Cancel button
        self.cancel_button = ctk.CTkButton(
            self,
            text="Cancel",
            width=150,
            command=on_cancel,
            state="disabled"
        )
        self.cancel_button.pack(side="left", padx=10, pady=12)

    def set_converting(self, is_converting: bool):
        """Update button states based on conversion status."""
        if is_converting:
            self.convert_button.configure(state="disabled")
            self.cancel_button.configure(state="normal")
        else:
            self.convert_button.configure(state="normal")
            self.cancel_button.configure(state="disabled")
