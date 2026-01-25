"""Scanner for Tana export files.

Discovers supertags, their field definitions, and field types
to enable dynamic configuration of the conversion process.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Callable

from .models import SupertagInfo, FieldInfo, ConversionProgress


class TanaExportScanner:
    """Scans Tana export to discover supertags and field definitions."""

    # System field IDs for detecting field types
    SOURCE_SUPERTAG_FIELD_ID = 'SYS_A05'  # Indicates "options from supertag"
    DONE_FIELD_ID = 'SYS_A77'  # Done field

    # System/internal supertags to exclude from selection
    EXCLUDED_TAG_NAMES = {
        'meta information',
        'row defaults',
        'tagr app',
        'supertag',
        'field-definition',
        'field definition',
    }

    def __init__(
        self,
        json_path: Path,
        progress_callback: Optional[Callable[[ConversionProgress], None]] = None
    ):
        self.json_path = json_path
        self.progress_callback = progress_callback
        self.docs: List[dict] = []
        self.doc_map: Dict[str, dict] = {}
        self.supertags: Dict[str, str] = {}  # id -> name
        self.metanode_tags: Dict[str, Set[str]] = {}  # metanode_id -> set of tag_ids

    def report_progress(self, phase: str, current: int = 0, total: int = 0, message: str = ""):
        """Send progress update."""
        if self.progress_callback:
            self.progress_callback(ConversionProgress(phase, current, total, message))

    def scan(self) -> List[SupertagInfo]:
        """Scan the export and return discovered supertags with their fields.

        Returns supertags sorted by:
        1. Special types first (day at top for daily notes)
        2. Then by instance count (descending)
        3. System supertags at the end
        """
        self.report_progress("Scanning", message="Loading export file...")
        self._load_data()

        self.report_progress("Scanning", message="Discovering supertags...")
        self._discover_supertags()
        self._build_metanode_tags()

        self.report_progress("Scanning", message="Analyzing fields...")
        supertag_infos = []

        # Filter out excluded supertags
        filtered_supertags = {
            tag_id: tag_name
            for tag_id, tag_name in self.supertags.items()
            if not self._should_exclude_supertag(tag_id, tag_name)
        }

        total = len(filtered_supertags)
        for idx, (tag_id, tag_name) in enumerate(filtered_supertags.items()):
            self.report_progress("Scanning", current=idx + 1, total=total,
                               message=f"Analyzing #{tag_name}...")

            # Get field definitions for this supertag
            # Note: Done status is detected via SYS_A77 in _discover_fields,
            # not by checking if instances have _done (which causes false positives
            # when a node has multiple supertags like #task and #company)
            fields = self._discover_fields(tag_id)

            # Count instances
            instance_count = self._count_instances(tag_id)

            # Determine special type
            special_type = self._get_special_type(tag_name)

            # Check if system supertag
            is_system = tag_id.startswith('SYS_')

            supertag_infos.append(SupertagInfo(
                id=tag_id,
                name=tag_name,
                instance_count=instance_count,
                fields=fields,
                is_system=is_system,
                special_type=special_type
            ))

        # Sort: special types first, then by instance count, system tags last
        def sort_key(info: SupertagInfo):
            # Priority for special types (lower = higher priority)
            special_priority = {
                'day': 0,
                'week': 1,
                'year': 2,
                'field-definition': 3,
            }
            sp = special_priority.get(info.special_type, 10)

            # System tags go to the end
            sys_penalty = 1000 if info.is_system else 0

            # Higher instance count = lower sort value (appears first)
            return (sp, sys_penalty, -info.instance_count, info.name.lower())

        supertag_infos.sort(key=sort_key)

        self.report_progress("Scanning", message=f"Found {len(supertag_infos)} supertags")
        return supertag_infos

    def _load_data(self):
        """Load and parse the Tana JSON file."""
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.docs = data.get('docs', [])
        self.doc_map = {d['id']: d for d in self.docs}
        self.report_progress("Scanning", message=f"Loaded {len(self.docs)} documents")

    def _discover_supertags(self):
        """Find all supertag definitions."""
        for doc in self.docs:
            if doc.get('props', {}).get('_docType') == 'tagDef':
                tag_name = doc.get('props', {}).get('name', '')
                # Clean up merged tag names
                if '(merged into' in tag_name:
                    tag_name = tag_name.split('(merged into')[0].strip()
                if tag_name:  # Only include tags with names
                    self.supertags[doc['id']] = tag_name

    def _should_exclude_supertag(self, tag_id: str, tag_name: str) -> bool:
        """Check if a supertag should be excluded from the selection list."""
        # Exclude system supertags
        if tag_id.startswith('SYS_'):
            return True

        # Exclude by name
        name_lower = tag_name.lower()
        if name_lower in self.EXCLUDED_TAG_NAMES:
            return True

        # Exclude "(base type)" supertags
        if '(base type)' in name_lower:
            return True

        return False

    def _build_metanode_tags(self):
        """Build mapping of metanode -> supertag IDs via tuples."""
        for doc in self.docs:
            if doc.get('props', {}).get('_docType') == 'tuple':
                children = doc.get('children', [])
                owner_id = doc.get('props', {}).get('_ownerId')
                if owner_id:
                    if owner_id not in self.metanode_tags:
                        self.metanode_tags[owner_id] = set()
                    for cid in children:
                        if cid in self.supertags:
                            self.metanode_tags[owner_id].add(cid)

    def _discover_fields(self, supertag_id: str) -> List[FieldInfo]:
        """Find all fields defined for a supertag.

        Fields are discovered by looking at the supertag's tuple children.
        Each tuple typically contains:
        - A field definition node (owned by FjHKomuskX_SCHEMA or system)
        - Configuration/default value nodes

        For each field definition, we check its children for "options from supertag"
        config (indicated by SYS_A05 in children).
        """
        fields = []
        seen_field_ids = set()
        supertag_doc = self.doc_map.get(supertag_id)
        if not supertag_doc:
            return fields

        # Look at supertag's children (should be tuples)
        for child_id in supertag_doc.get('children', []):
            child = self.doc_map.get(child_id)
            if not child:
                continue

            child_props = child.get('props', {})

            # Only process tuples
            if child_props.get('_docType') != 'tuple':
                continue

            # Look at tuple's children to find field definition
            tuple_children = child.get('children', [])
            field_def = self._find_field_definition_in_tuple(tuple_children)

            if not field_def:
                continue

            field_id = field_def['id']
            field_name = field_def.get('props', {}).get('name', '')

            if not field_name or field_id in seen_field_ids:
                continue

            seen_field_ids.add(field_id)

            # Check if this is a "Done" system field
            if field_id == self.DONE_FIELD_ID:
                fields.append(FieldInfo(
                    id='_done',
                    name='Done',
                    field_type='system_done'
                ))
                continue

            # Check if this is an "options from supertag" field
            source_tag_id, source_tag_name = self._detect_options_from_supertag(field_def)

            if source_tag_id:
                fields.append(FieldInfo(
                    id=field_id,
                    name=field_name,
                    field_type='options_from_supertag',
                    source_supertag_id=source_tag_id,
                    source_supertag_name=source_tag_name
                ))
            else:
                fields.append(FieldInfo(
                    id=field_id,
                    name=field_name,
                    field_type='plain'
                ))

        return fields

    def _find_field_definition_in_tuple(self, tuple_children: List[str]) -> Optional[dict]:
        """Find the field definition node among tuple children.

        Field definitions are typically:
        - Owned by FjHKomuskX_SCHEMA (shared fields)
        - Owned by the tuple itself (inline fields)
        - System fields (SYS_*)

        We look for nodes with a 'name' property that aren't just config values.
        """
        for child_id in tuple_children:
            child = self.doc_map.get(child_id)
            if not child:
                continue

            props = child.get('props', {})
            name = props.get('name', '')
            owner = props.get('_ownerId', '')

            # Skip nodes without names
            if not name:
                continue

            # Field definitions are owned by SCHEMA or are system fields
            if owner == 'FjHKomuskX_SCHEMA' or child_id.startswith('SYS_'):
                return child

            # Also check if it's a field definition by having its own children
            # (field defs have config children, values typically don't)
            if child.get('children'):
                return child

        return None

    def _detect_options_from_supertag(self, field_doc: dict) -> tuple:
        """Check if field is 'options from supertag' and return (source_tag_id, source_tag_name).

        Detection: Field has a child tuple where one of the children is SYS_A05
        (Source supertag field). The other child of that tuple is the source supertag ID.
        """
        for child_id in field_doc.get('children', []):
            child = self.doc_map.get(child_id)
            if not child:
                continue

            # Check if this is a tuple with SYS_A05
            child_children = child.get('children', [])
            if self.SOURCE_SUPERTAG_FIELD_ID in child_children:
                # Find the source supertag (the other child that's a supertag)
                for gc_id in child_children:
                    if gc_id != self.SOURCE_SUPERTAG_FIELD_ID and gc_id in self.supertags:
                        return (gc_id, self.supertags[gc_id])

        return (None, None)

    def _count_instances(self, supertag_id: str) -> int:
        """Count how many nodes are tagged with this supertag."""
        count = 0
        for metanode_id, tag_ids in self.metanode_tags.items():
            if supertag_id in tag_ids:
                count += 1
        return count

    def _get_special_type(self, tag_name: str) -> Optional[str]:
        """Determine if this is a special supertag that needs custom handling."""
        name_lower = tag_name.lower()

        if name_lower == 'day':
            return 'day'
        elif name_lower == 'week':
            return 'week'
        elif name_lower == 'year':
            return 'year'
        elif name_lower in ('field-definition', 'field definition'):
            return 'field-definition'

        return None

    def get_supertag_instances(self, supertag_id: str) -> List[dict]:
        """Get all nodes tagged with a specific supertag.

        Useful for previewing what will be converted.
        """
        instances = []
        for doc in self.docs:
            meta_id = doc.get('props', {}).get('_metaNodeId')
            if meta_id and supertag_id in self.metanode_tags.get(meta_id, set()):
                instances.append(doc)
        return instances
