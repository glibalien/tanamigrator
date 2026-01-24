#!/usr/bin/env python3
"""Application entry point for Tana to Obsidian Converter."""

import customtkinter as ctk
from src.gui.app import TanaToObsidianApp


def main():
    """Initialize and run the application."""
    # Set appearance mode and theme
    ctk.set_appearance_mode("system")  # "light", "dark", or "system"
    ctk.set_default_color_theme("blue")

    # Create and run the application
    app = TanaToObsidianApp()
    app.mainloop()


if __name__ == "__main__":
    main()
