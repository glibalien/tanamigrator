"""Data classes for configuration and results."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class ConversionSettings:
    """User-configurable conversion options."""
    json_path: Path
    output_dir: Path

    # Export options
    download_images: bool = True
    skip_readwise: bool = True
    skip_week_nodes: bool = True
    skip_year_nodes: bool = True
    skip_highlights: bool = True
    skip_field_definitions: bool = True

    # Field ID overrides (for users with different Tana setups)
    project_field_id: str = 'zaD_EkMhKP'
    people_involved_field_id: str = 'znaT5AHKXQkR'
    company_field_id: str = 'LNd_B370Hr'
    cookbook_field_id: str = 'Y_572Dtvp_QO'
    url_field_id: str = 'SYS_A78'


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
