# Optionality Refactor - Implementation Plan

## Overview

This refactor changes the app from a simple "select files and convert" flow to a multi-step wizard that:
1. Scans the Tana export to discover supertags and their field definitions
2. Lets users select which supertags to include
3. Allows per-supertag field mapping configuration
4. Provides sensible defaults for common patterns (done → status, options-from-supertag → wikilinks)

## Tana Data Structure Analysis

Based on analysis of the provided export:

### Key Structures

1. **Supertags**: Nodes with `props._docType == "tagDef"`
   - User-defined: 202 supertags
   - System (SYS_*): 18 supertags

2. **Field Definitions**: Nodes owned by `FjHKomuskX_SCHEMA` with a `name` property

3. **Node Tagging**: Via metanode relationship
   - Node has `props._metaNodeId` pointing to its metanode
   - Tuples owned by metanode contain supertag IDs as children

4. **Field Values**: Tuples that are children of a node
   - Tuple contains field definition ID + value node ID(s)

5. **"Options from Supertag" Fields**: Field definitions with a child tuple where:
   - `_sourceId == "SYS_A06"` (Source supertag config)
   - Children include the source supertag ID
   - Example: Project field → links to #project supertag instances

6. **Done Status**: Stored as `props._done` timestamp (presence = done, absence = not done)

### Discovered Field Types

From the export analysis:
- `Project` (zaD_EkMhKP) → #project
- `Cookbook` (Y_572Dtvp_QO) → #cookbook
- `Author` (tOSK7oC6Tj53) → #person
- `Workstream` (-iRCZzoaA9M8) → #workstream

## New User Flow

### Step 1: File Selection
- User selects Tana export JSON file
- App validates it's a valid Tana export
- "Next" button becomes active

### Step 2: Supertag Selection
- App scans JSON and displays all discovered supertags
- Shows count of instances for each supertag
- All supertags selected by default
- Special handling indicators:
  - #day → "Will convert to Daily Notes"
  - #week, #year → "Ignored by default" (unchecked)
  - #field-definition → "Ignored by default" (unchecked)
- User can check/uncheck supertags to include
- "Select All" / "Deselect All" buttons

### Step 3: Field Mapping Configuration
- For each selected supertag, show expandable panel
- Display detected fields with auto-configured mappings:

  **Default mappings (auto-detected):**
  - `_done` system field → `status` frontmatter (done=true → "done", done=false → "open")
  - Options-from-supertag fields → wikilink to target node's markdown file

  **User can configure:**
  - Frontmatter field name (e.g., change "Project" to "project")
  - Include/exclude specific fields
  - Override default value transformations

### Step 4: Options & Output
- Output directory selection
- Global options:
  - Download images from Firebase (default: checked)
  - Skip Week nodes (default: checked)
  - Skip Year nodes (default: checked)
- "Convert" button

### Step 5: Conversion Progress
- Same as current: progress bar, log output, cancel button

## Architecture Changes

### New Data Models (`src/core/models.py`)

```python
@dataclass
class SupertagInfo:
    """Information about a discovered supertag."""
    id: str
    name: str
    instance_count: int
    fields: List['FieldInfo']
    is_system: bool  # SYS_* prefix
    special_type: Optional[str]  # 'day', 'week', 'year', 'field-definition'

@dataclass
class FieldInfo:
    """Information about a supertag field."""
    id: str
    name: str
    field_type: str  # 'plain', 'options_from_supertag', 'system_done', etc.
    source_supertag_id: Optional[str]  # For options_from_supertag fields
    source_supertag_name: Optional[str]

@dataclass
class FieldMapping:
    """User-configured mapping for a field."""
    field_id: str
    field_name: str
    frontmatter_name: str
    include: bool
    transform: str  # 'none', 'wikilink', 'status'

@dataclass
class SupertagConfig:
    """User configuration for a supertag."""
    supertag_id: str
    include: bool
    field_mappings: List[FieldMapping]

@dataclass
class ConversionSettings:
    """Updated to include supertag configurations."""
    json_path: Path
    output_dir: Path

    # Supertag configurations
    supertag_configs: List[SupertagConfig]

    # Global options (simplified)
    download_images: bool = True
    skip_week_nodes: bool = True
    skip_year_nodes: bool = True
```

### New Scanner Module (`src/core/scanner.py`)

```python
class TanaExportScanner:
    """Scans Tana export to discover supertags and field definitions."""

    def __init__(self, json_path: Path):
        self.json_path = json_path

    def scan(self) -> List[SupertagInfo]:
        """
        Scan the export and return discovered supertags with their fields.

        Returns supertags sorted by:
        1. Special types first (day, week, year)
        2. Then by instance count (descending)
        """
        pass

    def _discover_supertags(self) -> Dict[str, SupertagInfo]:
        """Find all supertag definitions."""
        pass

    def _discover_fields(self, supertag_id: str) -> List[FieldInfo]:
        """Find all fields defined for a supertag."""
        pass

    def _detect_options_from_supertag(self, field_doc: dict) -> Optional[str]:
        """Check if field is 'options from supertag' and return source tag ID."""
        pass

    def _count_instances(self, supertag_id: str) -> int:
        """Count how many nodes are tagged with this supertag."""
        pass
```

### Updated Converter (`src/core/converter.py`)

Changes needed:
1. Remove hardcoded field IDs (project_field_id, etc.)
2. Use `SupertagConfig` list to determine what to export
3. Apply field mappings when generating frontmatter
4. Generate wikilinks for options-from-supertag fields

### New GUI Components (`src/gui/`)

#### New wizard-style flow in `app.py`:

```python
class TanaToObsidianApp(ctk.CTk):
    def __init__(self):
        # ...
        self.current_step = 1  # 1=file, 2=supertags, 3=fields, 4=options, 5=convert
        self.scanner_result: List[SupertagInfo] = []
        self.supertag_configs: Dict[str, SupertagConfig] = {}
```

#### New components in `components.py`:

1. **StepIndicator**: Shows current step (1-5) with labels
2. **SupertagSelectionFrame**: Scrollable list of supertags with checkboxes
3. **FieldMappingFrame**: Expandable panels for per-supertag field configuration
4. **WizardNavigationFrame**: Back/Next/Convert buttons

## Implementation Phases

### Phase 1: Core Scanner
1. Create `scanner.py` with `TanaExportScanner` class
2. Implement supertag discovery
3. Implement field discovery including options-from-supertag detection
4. Implement instance counting
5. Add unit tests for scanner

### Phase 2: Data Models
1. Add new dataclasses to `models.py`
2. Update `ConversionSettings`
3. Add default mapping generation logic

### Phase 3: GUI Refactor
1. Create step indicator component
2. Create supertag selection component
3. Create field mapping component
4. Implement wizard navigation flow
5. Update window sizing for new layout

### Phase 4: Converter Updates
1. Remove hardcoded field IDs
2. Implement dynamic field mapping
3. Generate wikilinks for supertag references
4. Update frontmatter generation with configured field names

### Phase 5: Testing & Polish
1. End-to-end testing with real export
2. Edge case handling
3. UI polish and feedback

## File Changes Summary

### New Files
- `src/core/scanner.py` - Export scanning logic
- `tests/test_scanner.py` - Scanner unit tests

### Modified Files
- `src/core/models.py` - New dataclasses
- `src/core/converter.py` - Dynamic field mapping
- `src/gui/app.py` - Wizard flow
- `src/gui/components.py` - New UI components
- `src/gui/styles.py` - Updated sizing

### Removed Functionality
- Skip Readwise nodes option (removed from UI)
- Skip Highlight nodes option (removed from UI)
- Skip Field Definition nodes option (handled automatically)
- Hardcoded field IDs in settings

## Default Behaviors

### Auto-selected supertags
All supertags except:
- #week (skip_week_nodes default)
- #year (skip_year_nodes default)
- #field-definition (always ignored)

### Auto-configured field mappings

1. **Done field** (system `_done` property):
   - Frontmatter: `status`
   - Transform: `done` if timestamp present, `open` if absent

2. **Options-from-supertag fields**:
   - Frontmatter: lowercase field name
   - Transform: `[[wikilink]]` to target node's markdown file

3. **Other fields**:
   - Frontmatter: lowercase field name
   - Transform: plain text value

### Special supertag handling

- **#day**: Convert to daily notes (Daily Notes/YYYY-MM-DD.md)
- **#week**: Skip by default (configurable)
- **#year**: Skip by default (configurable)
- **#field-definition**: Always skip (not configurable)
- **#readwise, #highlight**: No special handling, treated as normal supertags
