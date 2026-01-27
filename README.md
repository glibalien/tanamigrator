# Tana Migrator

A cross-platform desktop application that converts Tana exports to markdown files (Obsidian-friendly).

## Features

- **Wizard-based interface** - Simple 3-step process: Select File → Select Supertags → Convert
- **Automatic supertag discovery** - Scans your export to find all supertags and their fields
- **Dynamic field mapping** - Field values automatically extracted to YAML frontmatter
- **Configurable output folders** - Customize where each supertag's files are saved
- **Smart wikilinks** - Field values with supertags automatically become `[[wikilinks]]`
- References converted to `[[Obsidian links]]`
- Images downloaded from Firebase and embedded as `![[attachments]]`
- Cross-platform: Windows, macOS, Linux

## Installation

### Option 1: Download Pre-built Executable

Download the latest release for your platform from the [Releases](../../releases) page.

### Option 2: Run from Source

Requires Python 3.11+

```bash
# Clone the repository
git clone https://github.com/iamactionbarry/tanamigrator.git
cd tanamigrator

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m src.main
```

## Usage

1. **Export from Tana**: In Tana, go to Workspace Settings → Export Workspace as JSON
2. **Launch the converter**: Run the application
3. **Step 1 - Select File**:
   - Choose your Tana export JSON file
   - Optionally ignore items in Tana trash
   - Click Next to scan the export (progress bar shows scanning status)
4. **Step 2 - Select Supertags**:
   - Review discovered supertags and their instance counts
   - Check/uncheck supertags to include in conversion
   - Optionally include referenced nodes without supertags
   - Field mappings are auto-configured based on field types
5. **Step 3 - Configure and Convert**:
   - Choose output directory
   - **Configure output folders** for each supertag (e.g., Daily Notes, Tasks, Projects)
   - Set attachments folder for images
   - Set folder for untagged nodes (if enabled)
   - Configure options (download images)
   - Click Convert and watch the progress
6. **Open in Obsidian**: Point Obsidian to your output directory

## Conversion Details

### What Gets Converted

| Tana | Obsidian |
|------|----------|
| Daily notes (`#day`) | Configurable folder (default: root) |
| Nodes with supertags | Configurable folders with YAML frontmatter |
| Inline references | `[[wikilinks]]` |
| Date references | `[[YYYY-MM-DD]]` |
| Firebase images | `![[Attachments/image.png]]` (folder configurable) |
| Referenced nodes w/o supertags | Configurable folder |

### Output Folder Configuration

In Step 3, you can specify a subfolder for each selected supertag:
- **#day** → "Daily Notes" (suggested default)
- **#task** → "Tasks" (suggested default)
- **All other supertags** → User-configurable subfolders
- **Attachments** → Where images are saved
- **Untagged Nodes** → Where referenced nodes without supertags are saved

Leave a folder blank to save files in the root output directory.

### YAML Frontmatter

Tagged nodes include frontmatter with:
- `tags`: Supertag names
- `Date`: Link to daily note (for nodes associated with a day)
- **Dynamic fields**: Any field values from your supertags are automatically included
  - Reference fields (options from supertag) → `[[wikilinks]]`
  - Field values that have supertags → automatically `[[wikilinks]]`
  - Checkbox fields → `true`/`false`
  - Options fields → selected option value
  - Text, URL, date, number fields → plain values

### Untagged Nodes

When "Include nodes without supertags if they are referenced by an exported node" is enabled:
- Referenced nodes without supertags get their own markdown files
- Nodes WITH supertags are only exported if that supertag is selected
- Wikilinks to unselected supertag nodes remain as links (but no file is created)

### Skipped Content

The following are automatically excluded from the supertag selection:
- System supertags (IDs starting with `SYS_`)
- Meta information, row defaults, and field definition supertags
- Supertags in the Tana trash (when "Ignore items in Tana trash" is checked)

You control which supertags to convert via the selection wizard in Step 2.

## Building from Source

### Prerequisites

- Python 3.11+
- pip

### Build Steps

```bash
# Install build dependencies
pip install -r requirements.txt
pip install pyinstaller

# Generate icons (optional, already included)
python build/create_icons.py

# Build executable
python build/build.py
```

The executable will be in the `dist/` directory.

### Platform-Specific Notes

**macOS**:
- The app may need to be allowed in System Preferences → Security & Privacy
- First launch: Right-click → Open

**Windows**:
- Windows Defender may flag the executable; allow it to run
- No installation required, just run the `.exe`

**Linux**:
- Make executable: `chmod +x TanaToObsidian`
- Requires Tk libraries: `sudo apt install python3-tk`

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest

# Run tests
pytest
```

### Project Structure

```
tanamigrator/
├── src/
│   ├── main.py              # Entry point
│   ├── core/
│   │   ├── converter.py     # Main conversion logic
│   │   ├── scanner.py       # Supertag/field discovery
│   │   ├── models.py        # Data classes
│   │   └── exceptions.py    # Custom exceptions
│   └── gui/
│       ├── app.py           # Main window (wizard interface)
│       ├── components.py    # UI components
│       └── styles.py        # Theme constants
├── tests/
│   ├── test_converter.py    # Unit tests
│   └── fixtures/            # Test data
├── build/
│   ├── build.py             # PyInstaller script
│   └── create_icons.py      # Icon generator
└── assets/
    ├── icon.png             # Linux icon
    ├── icon.ico             # Windows icon
    └── icon.icns            # macOS icon
```

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for the modern UI
- [Tana](https://tana.inc) for the knowledge management tool
- [Obsidian](https://obsidian.md) for the target platform
