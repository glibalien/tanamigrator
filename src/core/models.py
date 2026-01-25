"""Data classes for configuration and results."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict


@dataclass
class FieldInfo:
    """Information about a supertag field discovered during scanning."""
    id: str
    name: str
    field_type: str  # 'plain', 'options_from_supertag', 'system_done'
    data_type: str = 'plain'  # 'checkbox', 'options', 'date', 'number', 'url', 'plain'
    source_supertag_id: Optional[str] = None  # For options_from_supertag fields
    source_supertag_name: Optional[str] = None
    options: List[str] = field(default_factory=list)  # Available options for 'options' data_type


@dataclass
class SupertagInfo:
    """Information about a discovered supertag."""
    id: str
    name: str
    instance_count: int = 0
    fields: List[FieldInfo] = field(default_factory=list)
    is_system: bool = False  # SYS_* prefix
    special_type: Optional[str] = None  # 'day', 'week', 'year', 'field-definition'


@dataclass
class FieldMapping:
    """User-configured mapping for a field to frontmatter."""
    field_id: str
    field_name: str
    frontmatter_name: str
    include: bool = True
    transform: str = 'none'  # 'none', 'wikilink', 'status'


@dataclass
class SupertagConfig:
    """User configuration for how to handle a supertag during conversion."""
    supertag_id: str
    supertag_name: str
    include: bool = True
    field_mappings: List[FieldMapping] = field(default_factory=list)
    output_folder: str = ""  # Subfolder for this supertag's output (empty = root)


@dataclass
class ConversionSettings:
    """User-configurable conversion options."""
    json_path: Path
    output_dir: Path

    # Supertag configurations (new in v2)
    supertag_configs: List[SupertagConfig] = field(default_factory=list)

    # Global options
    download_images: bool = True
    include_library_nodes: bool = True  # Include referenced nodes without supertags
    attachments_folder: str = "Attachments"  # Subfolder for images/attachments
    untagged_library_folder: str = ""  # Subfolder for untagged library nodes (empty = root)


@dataclass
class ConversionProgress:
    """Progress update sent to GUI."""
    phase: str  # e.g., "Loading", "Building indices", "Exporting daily notes"
    current: int = 0
    total: int = 0
    message: str = ""


@dataclass
class ConversionResult:
    """Final result of conversion."""
    success: bool
    daily_notes_count: int = 0
    blank_daily_notes_skipped: int = 0
    tagged_nodes_count: int = 0
    orphan_nodes_count: int = 0
    referenced_nodes_count: int = 0
    images_downloaded: int = 0
    image_errors: List[tuple] = field(default_factory=list)
    files_written: int = 0
    single_files: int = 0
    merged_files: int = 0
    error_message: str = ""


def create_default_field_mappings(supertag_info: SupertagInfo) -> List[FieldMapping]:
    """Create default field mappings for a supertag based on discovered fields.

    Default behaviors:
    - options_from_supertag fields: transform to wikilink
    - system_done field: transform to status (done/open)
    - plain fields: no transform, use lowercase field name
    """
    mappings = []

    for field_info in supertag_info.fields:
        if field_info.field_type == 'options_from_supertag':
            # Options from supertag -> wikilink to target node
            mappings.append(FieldMapping(
                field_id=field_info.id,
                field_name=field_info.name,
                frontmatter_name=field_info.name.lower().replace(' ', '_'),
                include=True,
                transform='wikilink'
            ))
        elif field_info.field_type == 'system_done':
            # Done field -> status frontmatter
            mappings.append(FieldMapping(
                field_id=field_info.id,
                field_name=field_info.name,
                frontmatter_name='status',
                include=True,
                transform='status'
            ))
        else:
            # Plain field -> lowercase name, no transform
            mappings.append(FieldMapping(
                field_id=field_info.id,
                field_name=field_info.name,
                frontmatter_name=field_info.name.lower().replace(' ', '_'),
                include=True,
                transform='none'
            ))

    return mappings


def create_default_supertag_config(supertag_info: SupertagInfo) -> SupertagConfig:
    """Create default configuration for a supertag.

    Default behaviors:
    - Include all supertags except week, year, field-definition
    - Auto-generate field mappings based on field types
    """
    # Determine if this supertag should be included by default
    include = True
    if supertag_info.special_type in ('week', 'year', 'field-definition'):
        include = False

    return SupertagConfig(
        supertag_id=supertag_info.id,
        supertag_name=supertag_info.name,
        include=include,
        field_mappings=create_default_field_mappings(supertag_info)
    )
