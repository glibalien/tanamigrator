#!/usr/bin/env python3
"""Build script for creating standalone executables."""

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def get_version() -> str:
    """Extract version from pyproject.toml."""
    project_root = Path(__file__).parent.parent
    pyproject = project_root / "pyproject.toml"

    if pyproject.exists():
        content = pyproject.read_text()
        for line in content.split('\n'):
            if line.startswith('version'):
                return line.split('"')[1]
    return "1.0.0"


def build(clean: bool = False, onedir: bool = None):
    """Build the application for the current platform."""
    system = platform.system().lower()
    project_root = Path(__file__).parent.parent
    version = get_version()

    if clean:
        print("Cleaning build artifacts...")
        for dir_name in ['build/TanaToObsidian', 'dist']:
            dir_path = project_root / dir_name
            if dir_path.exists():
                shutil.rmtree(dir_path)
        spec_file = project_root / "TanaToObsidian.spec"
        if spec_file.exists():
            spec_file.unlink()

    if onedir is None:
        onedir = (system == "darwin")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "TanaToObsidian",
        "--windowed",
        "--noconfirm",
    ]

    if onedir:
        cmd.append("--onedir")
    else:
        cmd.append("--onefile")

    assets_dir = project_root / "assets"
    if assets_dir.exists():
        separator = ";" if system == "windows" else ":"
        cmd.extend(["--add-data", f"assets{separator}assets"])

    icon_path = None
    if system == "windows":
        icon_path = assets_dir / "icon.ico"
    elif system == "darwin":
        icon_path = assets_dir / "icon.icns"
        cmd.extend(["--osx-bundle-identifier", "com.tana-to-obsidian.converter"])
    else:
        icon_path = assets_dir / "icon.png"

    if icon_path and icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])

    cmd.extend([
        "--hidden-import", "customtkinter",
        "--hidden-import", "PIL",
        "--hidden-import", "PIL._tkinter_finder",
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.filedialog",
        "--hidden-import", "tkinter.messagebox",
        "--collect-all", "customtkinter",
    ])

    cmd.append(str(project_root / "src" / "main.py"))

    print("=" * 60)
    print(f"Tana to Obsidian Converter - Build Script")
    print("=" * 60)
    print(f"Version: {version}")
    print(f"Platform: {system}")
    print(f"Mode: {'onedir' if onedir else 'onefile'}")
    print()

    result = subprocess.run(cmd, cwd=project_root)

    if result.returncode == 0:
        dist_dir = project_root / "dist"
        print()
        print("BUILD SUCCESSFUL")
        print(f"Output: {dist_dir}")
        return 0
    else:
        print("BUILD FAILED")
        return 1


def main():
    parser = argparse.ArgumentParser(description="Build Tana to Obsidian Converter")
    parser.add_argument("--clean", action="store_true", help="Clean before building")
    parser.add_argument("--onefile", action="store_true", help="Single file mode")
    parser.add_argument("--onedir", action="store_true", help="Directory mode")
    args = parser.parse_args()

    onedir = None
    if args.onefile:
        onedir = False
    elif args.onedir:
        onedir = True

    sys.exit(build(clean=args.clean, onedir=onedir))


if __name__ == "__main__":
    main()
