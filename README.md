# Tana to Obsidian Converter

A cross-platform desktop application that converts Tana exports to Obsidian-compatible markdown files.

## Features

- **Wizard-based interface** - Simple 3-step process: Select File → Select Supertags → Convert
- **Automatic supertag discovery** - Scans your export to find all supertags and their fields
- **Dynamic field mapping** - Field values automatically extracted to YAML frontmatter
- Daily notes exported to `Daily Notes/YYYY-MM-DD.md`
- Tagged nodes become separate markdown files with YAML frontmatter
- Tasks are placed in a dedicated `Tasks/` folder
- References converted to `[[Obsidian links]]`
- Images downloaded from Firebase and embedded as `![[attachments]]`
- Progress tracking with cancel support
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

1. **Export from Tana**: In Tana, go to Settings → Export → Download JSON
2. **Launch the converter**: Run the application
3. **Step 1 - Select File**:
   - Choose your Tana export JSON file
   - Optionally ignore items in Tana trash
   - Click Next to scan the export
4. **Step 2 - Select Supertags**:
   - Review discovered supertags and their instance counts
   - Check/uncheck supertags to include in conversion
   - Field mappings are auto-configured based on field types
5. **Step 3 - Configure and Convert**:
   - Choose output directory
   - Configure options (download images, include library nodes)
   - Click Convert and watch the progress
6. **Open in Obsidian**: Point Obsidian to your output directory

## Conversion Details

### What Gets Converted

| Tana | Obsidian |
|------|----------|
| Daily notes (`journalPart`) | `Daily Notes/YYYY-MM-DD.md` |
| Nodes with `#task` tag | `Tasks/<name>.md` |
| Nodes with other supertags | `<name>.md` with YAML tags |
| Inline references | `[[wikilinks]]` |
| Date references | `[[YYYY-MM-DD]]` |
| Firebase images | `![[Attachments/image.png]]` |
| Bold/italic | `**bold**` / `*italic*` |

### YAML Frontmatter

Tagged nodes include frontmatter with:
- `tags`: Supertag names
- `Date`: Link to daily note (for nodes associated with a day)
- `status`: Task status (open/done) for nodes with done checkbox enabled
- `completedDate`: When task was completed
- **Dynamic fields**: Any field values from your supertags are automatically included
  - Reference fields (options from supertag) → `[[wikilinks]]`
  - Checkbox fields → `true`/`false`
  - Options fields → selected option value
  - Text, URL, date, number fields → plain values

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
