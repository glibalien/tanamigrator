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
    DONE_CHECKBOX_FIELD_ID = 'SYS_A55'  # "Show done/not done with a checkbox"
    YES_VALUE_ID = 'SYS_V03'  # "Yes" value
    TYPE_CHOICE_FIELD_ID = 'SYS_A02'  # typeChoice - indicates data type tuple
    OPTIONS_VALUES_FIELD_ID = 'SYS_A03'  # Values tuple for options type

    # Data type IDs (found in typeChoice tuples with _sourceId: SYS_A02)
    DATA_TYPE_CHECKBOX = 'SYS_D01'  # Boolean checkbox
    DATA_TYPE_DATE = 'SYS_D03'  # Date field
    DATA_TYPE_OPTIONS_FROM_SUPERTAG = 'SYS_D05'  # Options from supertag
    DATA_TYPE_PLAIN = 'SYS_D06'  # Plain text
    DATA_TYPE_NUMBER = 'SYS_D08'  # Number
    DATA_TYPE_URL = 'SYS_D10'  # URL
    DATA_TYPE_EMAIL = 'SYS_D11'  # Email
    DATA_TYPE_OPTIONS = 'SYS_D12'  # Predefined options

    # Mapping from SYS_D* to data_type string
    DATA_TYPE_MAP = {
        'SYS_D01': 'checkbox',
        'SYS_D03': 'date',
        'SYS_D05': 'options_from_supertag',
        'SYS_D06': 'plain',
        'SYS_D08': 'number',
        'SYS_D10': 'url',
        'SYS_D11': 'email',
        'SYS_D12': 'options',
    }

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
        progress_callback: Optional[Callable[[ConversionProgress], None]] = None,
        ignore_trash: bool = True
    ):
        self.json_path = json_path
        self.progress_callback = progress_callback
        self.ignore_trash = ignore_trash
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

        # Exclude trashed supertags if ignore_trash is enabled
        if self.ignore_trash:
            supertag_doc = self.doc_map.get(tag_id)
            if supertag_doc and self._is_in_trash(supertag_doc):
                return True

        return False

    def _is_in_trash(self, doc: dict, visited: Set[str] = None) -> bool:
        """Check if a document or any of its ancestors is in the trash."""
        if visited is None:
            visited = set()

        doc_id = doc.get('id', '')
        if doc_id in visited:
            return False
        visited.add(doc_id)

        # Check if this doc is in trash (TRASH in ID or owner)
        if 'TRASH' in doc_id.upper():
            return True

        owner_id = doc.get('props', {}).get('_ownerId', '')
        if 'TRASH' in owner_id.upper():
            return True

        # Check parent
        if owner_id and owner_id in self.doc_map:
            return self._is_in_trash(self.doc_map[owner_id], visited)

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

        Done status is detected via:
        1. SYS_A77 in field definitions (like #task)
        2. SYS_A55 + SYS_V03 in metanode (like #project)
        """
        fields = []
        seen_field_ids = set()
        supertag_doc = self.doc_map.get(supertag_id)
        if not supertag_doc:
            return fields

        # Check if this supertag has "done checkbox" enabled via metanode
        if self._has_done_checkbox_via_metanode(supertag_doc):
            fields.append(FieldInfo(
                id='_done',
                name='Done',
                field_type='system_done'
            ))
            seen_field_ids.add('_done')
            seen_field_ids.add(self.DONE_FIELD_ID)  # Prevent duplicate if SYS_A77 also found

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

            # Detect data type and options for this field
            data_type, options = self._detect_field_data_type(field_def)

            # Check if this is an "options from supertag" field
            source_tag_id, source_tag_name = self._detect_options_from_supertag(field_def)

            if source_tag_id:
                fields.append(FieldInfo(
                    id=field_id,
                    name=field_name,
                    field_type='options_from_supertag',
                    data_type='options_from_supertag',
                    source_supertag_id=source_tag_id,
                    source_supertag_name=source_tag_name
                ))
            else:
                fields.append(FieldInfo(
                    id=field_id,
                    name=field_name,
                    field_type=data_type if data_type != 'plain' else 'plain',
                    data_type=data_type,
                    options=options
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

    def _detect_field_data_type(self, field_doc: dict) -> tuple:
        """Detect the data type of a field and extract options if applicable.

        Detection: Field has a child tuple where _sourceId is SYS_A02 (typeChoice).
        One of that tuple's children is the data type (SYS_D01, SYS_D12, etc.).

        For 'options' type (SYS_D12), also looks for SYS_A03 tuple to get option values.

        Returns: (data_type: str, options: List[str])
        """
        data_type = 'plain'
        options = []

        for child_id in field_doc.get('children', []):
            child = self.doc_map.get(child_id)
            if not child:
                continue

            child_props = child.get('props', {})
            source_id = child_props.get('_sourceId', '')

            # Check for typeChoice tuple (SYS_A02)
            if source_id == self.TYPE_CHOICE_FIELD_ID:
                child_children = child.get('children', [])
                for gc_id in child_children:
                    if gc_id in self.DATA_TYPE_MAP:
                        data_type = self.DATA_TYPE_MAP[gc_id]
                        break

            # Check for options values tuple (SYS_A03) - only relevant for 'options' type
            elif source_id == self.OPTIONS_VALUES_FIELD_ID:
                child_children = child.get('children', [])
                for gc_id in child_children:
                    # Skip system IDs (like SYS_T03)
                    if gc_id.startswith('SYS_'):
                        continue
                    # Get the option name
                    option_doc = self.doc_map.get(gc_id)
                    if option_doc:
                        option_name = option_doc.get('props', {}).get('name', '')
                        if option_name:
                            options.append(option_name)

        return (data_type, options)

    def _has_done_checkbox_via_metanode(self, supertag_doc: dict) -> bool:
        """Check if supertag has "done checkbox" enabled via its metanode.

        This is detected by finding a tuple in the metanode's children that contains
        both SYS_A55 ("Show done/not done with a checkbox") and SYS_V03 ("Yes").
        """
        meta_id = supertag_doc.get('props', {}).get('_metaNodeId')
        if not meta_id:
            return False

        metanode = self.doc_map.get(meta_id)
        if not metanode:
            return False

        # Look through metanode's children for the done checkbox config
        for child_id in metanode.get('children', []):
            child = self.doc_map.get(child_id)
            if not child:
                continue

            # Check if this tuple contains both SYS_A55 and SYS_V03
            child_children = child.get('children', [])
            if self.DONE_CHECKBOX_FIELD_ID in child_children and self.YES_VALUE_ID in child_children:
                return True

        return False

    def _count_instances(self, supertag_id: str) -> int:
        """Count how many nodes are tagged with this supertag.

        When ignore_trash is True, excludes nodes that are in the trash.
        """
        count = 0
        for doc in self.docs:
            meta_id = doc.get('props', {}).get('_metaNodeId')
            if meta_id and supertag_id in self.metanode_tags.get(meta_id, set()):
                # Check if node is in trash when ignore_trash is enabled
                if self.ignore_trash and self._is_in_trash(doc):
                    continue
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

    def get_library_container_ids(self) -> List[str]:
        """Find all *_STASH nodes (Library containers).

        In Tana, the "Library" is stored in nodes with IDs ending in _STASH.
        """
        return [doc['id'] for doc in self.docs if doc['id'].endswith('_STASH')]

    def get_library_node_count(self) -> int:
        """Count total nodes in all Library containers.

        Used for UI display of how many Library nodes exist.
        """
        count = 0
        for stash_id in self.get_library_container_ids():
            stash_doc = self.doc_map.get(stash_id)
            if stash_doc:
                children = stash_doc.get('children', [])
                # Only count valid, non-trash children
                for child_id in children:
                    child = self.doc_map.get(child_id)
                    if child and not self._is_in_trash(child):
                        name = child.get('props', {}).get('name', '')
                        if name:
                            count += 1
        return count
