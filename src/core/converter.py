"""
Tana to Obsidian Migration Converter

Converts a Tana library JSON export to Obsidian markdown files.
- Daily notes -> Daily Notes/YYYY-MM-DD.md
- Nodes with supertags -> separate markdown files with tag frontmatter
- Untagged nodes -> inline bullet lists within their parent
- References -> [[Obsidian links]] with alias support
"""

import json
import os
import re
import html
import hashlib
import threading
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from typing import Callable, Optional
from urllib.parse import unquote, urlparse

from .models import ConversionSettings, ConversionProgress, ConversionResult, FieldInfo
from .exceptions import ConversionCancelled, FileAccessError


class TanaToObsidian:
    def __init__(
        self,
        settings: ConversionSettings,
        progress_callback: Optional[Callable[[ConversionProgress], None]] = None,
        cancel_event: Optional[threading.Event] = None
    ):
        self.settings = settings
        self.progress_callback = progress_callback
        self.cancel_event = cancel_event

        # Initialize from settings
        self.json_path = settings.json_path
        self.output_dir = Path(settings.output_dir)

        # Internal state
        self.docs = []
        self.doc_map = {}
        self.supertags = {}  # tag_id -> tag_name
        self.metanode_tags = {}  # metanode_id -> set of tag_ids
        self.node_names = {}  # node_id -> clean name (for reference resolution)
        self.day_tag_id = None
        self.meeting_tag_id = None
        self.note_tag_id = None
        self.project_tag_id = None
        self.person_tag_id = None
        self.one_on_one_tag_id = None  # 1:1 tag (maps to meeting)
        self.recipe_tag_id = None
        self.exported_files = {}  # node_id -> filename (without .md)
        self.used_filenames = {}  # filename -> node_id (to track duplicates)
        self.referenced_nodes = set()  # node IDs referenced in content via [[links]]
        self.pending_merges = {}  # base_filename -> list of (date, doc, folder)

        # Image handling
        self.attachments_dir = self.output_dir / settings.attachments_folder
        self.downloaded_images = {}  # url -> local filename
        self.image_download_errors = []  # track failed downloads
        self.image_urls = {}  # node_id -> firebase_url
        self.image_metadata_urls = {}  # node_id -> firebase_url

        # Selected supertags filter and folder mappings (from wizard selection)
        self.selected_supertag_ids = set()
        self.supertag_folders = {}  # supertag_id -> folder path (relative to output_dir)
        if settings.supertag_configs:
            for config in settings.supertag_configs:
                if config.include:
                    self.selected_supertag_ids.add(config.supertag_id)
                    # Store folder path (empty string means root)
                    self.supertag_folders[config.supertag_id] = config.output_folder

        # General field value index for dynamic frontmatter
        # node_id -> {field_id: [value_node_ids]}
        self.node_field_values = {}

        # Build field_id -> field_info lookup from supertag_configs
        self.field_info_map = {}  # field_id -> FieldInfo (from supertag_configs)
        self._build_field_info_map()

    def _build_field_info_map(self):
        """Build a lookup from field_id to FieldInfo from supertag_configs."""
        for config in self.settings.supertag_configs:
            if not config.include:
                continue
            for mapping in config.field_mappings:
                if mapping.include:
                    # We need to find the FieldInfo - it's not directly available in FieldMapping
                    # Store mapping info for now, we'll enhance this when we have scanner data
                    self.field_info_map[mapping.field_id] = {
                        'field_id': mapping.field_id,
                        'field_name': mapping.field_name,
                        'frontmatter_name': mapping.frontmatter_name,
                        'transform': mapping.transform,
                    }

    def _get_node_output_folder(self, doc: dict) -> Path:
        """Get the output folder for a node based on its supertags.

        Returns the folder path (relative to output_dir) based on configured supertag folders.
        If the node has multiple supertags with folders, uses the first one found.
        If no folder is configured, returns the root output_dir.
        """
        meta_id = doc.get('props', {}).get('_metaNodeId')
        if meta_id and meta_id in self.metanode_tags:
            for tag_id in self.metanode_tags[meta_id]:
                if tag_id in self.supertag_folders:
                    folder_name = self.supertag_folders[tag_id]
                    if folder_name:
                        return self.output_dir / folder_name
        return self.output_dir

    def _doc_has_any_supertag(self, doc: dict) -> bool:
        """Check if a document has any supertag (regardless of selection).

        Used to determine if a node should be treated as a tagged entity.
        Unlike has_supertag(), this checks for ANY supertag, not just selected ones.
        """
        meta_id = doc.get('props', {}).get('_metaNodeId')
        if not meta_id or meta_id not in self.metanode_tags:
            return False

        # Check if it has any non-system supertag
        for tag_id in self.metanode_tags[meta_id]:
            if tag_id in self.supertags:
                tag_name = self.supertags[tag_id]
                if tag_name and not tag_name.startswith('('):
                    return True
        return False

    def _value_has_supertag(self, value_id: str) -> bool:
        """Check if a value node has any supertag.

        Used to determine if a field value should be formatted as a wikilink.
        """
        if value_id.startswith('SYS_'):
            return False

        doc = self.doc_map.get(value_id)
        if not doc:
            return False

        return self._doc_has_any_supertag(doc)

    def get_field_values_with_metadata(self, node_id: str, field_id: str) -> list:
        """Get field values with metadata about each value.

        Returns list of dicts with 'value' and 'has_supertag' keys.
        Returns empty list if no values.
        For checkboxes, returns [{'value': True/False, 'has_supertag': False}].
        """
        if node_id not in self.node_field_values:
            return []

        node_fields = self.node_field_values[node_id]
        if field_id not in node_fields:
            return []

        value_ids = node_fields[field_id]
        if not value_ids:
            return []

        results = []
        for value_id in value_ids:
            # Check for checkbox values
            if value_id == 'SYS_V03':
                return [{'value': True, 'has_supertag': False}]
            elif value_id == 'SYS_V04':
                return [{'value': False, 'has_supertag': False}]

            # Get value from doc
            value_doc = self.doc_map.get(value_id)
            if value_doc:
                value_name = value_doc.get('props', {}).get('name', '')
                if value_name:
                    # Clean the value to handle inline references (dates, nodes, etc.)
                    clean_value = self.clean_node_name(value_name)
                    if clean_value:
                        has_supertag = self._value_has_supertag(value_id)
                        results.append({'value': clean_value, 'has_supertag': has_supertag})

        return results

    def get_field_value(self, node_id: str, field_id: str):
        """Get the value(s) for a specific field on a node.

        Returns the resolved value(s) based on field type:
        - For reference fields: returns the node name(s)
        - For text/option fields: returns the value text
        - For checkbox fields: returns True/False based on SYS_V03 presence

        Returns: single value or list of values, or None if not set
        """
        values_meta = self.get_field_values_with_metadata(node_id, field_id)
        if not values_meta:
            return None

        # Extract just the values
        if len(values_meta) == 1:
            return values_meta[0]['value']
        else:
            return [m['value'] for m in values_meta]

    def get_all_field_values(self, node_id: str) -> dict:
        """Get all configured field values for a node.

        Returns dict with frontmatter_name as key and formatted value.
        Only includes fields that have values set.

        Values that have supertags are automatically formatted as wikilinks,
        regardless of the field's transform setting.
        """
        result = {}

        if node_id not in self.node_field_values:
            return result

        for field_id, mapping_info in self.field_info_map.items():
            values_meta = self.get_field_values_with_metadata(node_id, field_id)
            if not values_meta:
                continue

            frontmatter_name = mapping_info['frontmatter_name']
            transform = mapping_info['transform']

            # Check if this is a boolean (checkbox) field
            if len(values_meta) == 1 and isinstance(values_meta[0]['value'], bool):
                bool_val = values_meta[0]['value']
                if transform == 'status':
                    result[frontmatter_name] = 'done' if bool_val else 'open'
                else:
                    result[frontmatter_name] = bool_val
                continue

            # Format each value - auto-wikilink if value has a supertag
            formatted_values = []
            for meta in values_meta:
                val = meta['value']
                has_tag = meta['has_supertag']

                # Apply wikilink if value has supertag OR if transform is wikilink
                if has_tag or transform == 'wikilink':
                    formatted_values.append(f'[[{val}]]')
                else:
                    formatted_values.append(val)

            # Return single value or list
            if len(formatted_values) == 1:
                result[frontmatter_name] = formatted_values[0]
            else:
                result[frontmatter_name] = formatted_values

        return result

    def report_progress(self, phase: str, current: int = 0, total: int = 0, message: str = ""):
        """Send progress update to GUI."""
        if self.progress_callback:
            self.progress_callback(ConversionProgress(phase, current, total, message))

    def check_cancelled(self):
        """Check if user requested cancellation."""
        if self.cancel_event and self.cancel_event.is_set():
            raise ConversionCancelled("Conversion cancelled by user")

    def load_data(self):
        """Load and parse the Tana JSON file."""
        self.report_progress("Loading", message=f"Loading {self.json_path}...")

        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileAccessError(f"JSON file not found: {self.json_path}")
        except json.JSONDecodeError as e:
            raise FileAccessError(f"Invalid JSON file: {e}")

        self.docs = data.get('docs', [])
        self.doc_map = {d['id']: d for d in self.docs}
        self.report_progress("Loading", message=f"Loaded {len(self.docs)} documents")

    def build_indices(self):
        """Build lookup indices for supertags, metanodes, etc."""
        self.report_progress("Indexing", message="Building indices...")

        # Build supertag index
        for doc in self.docs:
            if doc.get('props', {}).get('_docType') == 'tagDef':
                tag_name = doc.get('props', {}).get('name', '')
                # Clean up merged tag names
                if '(merged into' in tag_name:
                    tag_name = tag_name.split('(merged into')[0].strip()
                self.supertags[doc['id']] = tag_name

                # Track special tags
                if tag_name.lower() == 'day':
                    self.day_tag_id = doc['id']
                elif tag_name.lower() == 'meeting' and not tag_name.startswith('(') and 'base type' not in tag_name.lower():
                    # Prefer the non-system meeting tag
                    if not self.meeting_tag_id or not doc['id'].startswith('SYS_'):
                        self.meeting_tag_id = doc['id']
                elif tag_name == '1:1':
                    self.one_on_one_tag_id = doc['id']
                elif tag_name.lower() == 'note':
                    self.note_tag_id = doc['id']
                elif tag_name.lower() == 'project':
                    self.project_tag_id = doc['id']
                elif tag_name.lower() == 'person':
                    self.person_tag_id = doc['id']
                elif tag_name.lower() == 'recipe':
                    self.recipe_tag_id = doc['id']

        self.report_progress("Indexing", message=f"Found {len(self.supertags)} supertags")
        self.check_cancelled()

        # Build metanode -> tags mapping via tuples
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

        self.report_progress("Indexing", message=f"Built metanode->tags map with {len(self.metanode_tags)} entries")
        self.check_cancelled()

        # Build general field value index for configured fields
        # This indexes all field values for nodes, keyed by field_id
        configured_field_ids = set(self.field_info_map.keys())
        if configured_field_ids:
            for doc in self.docs:
                if doc.get('props', {}).get('_docType') == 'tuple':
                    children = doc.get('children', [])
                    owner_id = doc.get('props', {}).get('_ownerId')
                    if not owner_id or len(children) < 2:
                        continue

                    # Check if any child is a configured field
                    for field_id in configured_field_ids:
                        if field_id in children:
                            # Get value node IDs (everything except the field ID and system nodes)
                            value_ids = [c for c in children if c != field_id and not c.startswith('SYS_')]
                            if value_ids:
                                if owner_id not in self.node_field_values:
                                    self.node_field_values[owner_id] = {}
                                if field_id not in self.node_field_values[owner_id]:
                                    self.node_field_values[owner_id][field_id] = []
                                self.node_field_values[owner_id][field_id].extend(value_ids)

            self.report_progress("Indexing", message=f"Indexed field values for {len(self.node_field_values)} nodes")
            self.check_cancelled()

        # Build image URL index - map node IDs to their Firebase URLs
        for doc in self.docs:
            name = doc.get('props', {}).get('name', '')
            if 'firebasestorage.googleapis.com' in str(name):
                # Check if it's an image URL
                if any(ext in name.lower() for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg']):
                    self.image_urls[doc['id']] = html.unescape(name.replace('&amp;', '&'))

        self.report_progress("Indexing", message=f"Found {len(self.image_urls)} image URLs")
        self.check_cancelled()

        # Build image metadata -> URL mapping for nodes with _imageWidth
        for doc in self.docs:
            props = doc.get('props', {})
            if props.get('_imageWidth'):
                meta_id = props.get('_metaNodeId')
                if meta_id and meta_id in self.doc_map:
                    meta = self.doc_map[meta_id]
                    # Find tuple children that contain a Firebase URL
                    for child_id in meta.get('children', []):
                        if child_id in self.doc_map:
                            child = self.doc_map[child_id]
                            if child.get('props', {}).get('_docType') == 'tuple':
                                # Check tuple's children for Firebase URL
                                for tc_id in child.get('children', []):
                                    if tc_id in self.image_urls:
                                        self.image_metadata_urls[doc['id']] = self.image_urls[tc_id]
                                        break
                        if doc['id'] in self.image_metadata_urls:
                            break

        self.report_progress("Indexing", message=f"Mapped {len(self.image_metadata_urls)} image metadata nodes")
        self.check_cancelled()

        # Build node names index for reference resolution
        for doc in self.docs:
            name = doc.get('props', {}).get('name', '')
            if name:
                clean_name = self.clean_node_name(name)
                self.node_names[doc['id']] = clean_name

        self.report_progress("Indexing", message="Indexing complete")

    def extract_filename_from_url(self, url: str) -> str:
        """Extract a clean filename from an image URL."""
        # Decode URL encoding
        url = unquote(url)

        # Parse URL and get path
        parsed = urlparse(url.split('?')[0])  # Remove query params
        path = parsed.path

        # Get the last segment
        filename = path.split('/')[-1]

        # For Firebase URLs, the filename often has UUID prefixes
        parts = filename.split('-')

        # Look for the part that starts with letters (not UUID) or ends with extension
        for i, part in enumerate(parts):
            if re.match(r'^[A-Za-z]', part) and not re.match(r'^[0-9A-Fa-f]+$', part):
                filename = '-'.join(parts[i:])
                break
            if re.search(r'\.(png|jpg|jpeg|gif|webp|svg)$', part, re.IGNORECASE):
                filename = '-'.join(parts[i:])
                break

        # Clean up the filename
        filename = re.sub(r'[<>:"/\\|?*]', '-', filename)
        filename = re.sub(r'-+', '-', filename)
        filename = filename.strip('-. ')

        # Truncate if too long
        max_len = 100
        if len(filename) > max_len:
            name, ext = os.path.splitext(filename)
            filename = name[:max_len - len(ext)] + ext

        return filename if filename else 'image.png'

    def download_image(self, url: str) -> str:
        """Download an image from URL and return the local filename.

        Returns None if download fails or images are disabled.
        """
        # Check if image downloading is enabled
        if not self.settings.download_images:
            return None

        # Check if already downloaded
        if url in self.downloaded_images:
            return self.downloaded_images[url]

        # Extract filename
        filename = self.extract_filename_from_url(url)

        # Handle duplicate filenames by adding hash suffix
        base_name, ext = os.path.splitext(filename)
        local_path = self.attachments_dir / filename

        if local_path.exists():
            # Add hash of URL to make unique
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            filename = f"{base_name}-{url_hash}{ext}"
            local_path = self.attachments_dir / filename

        # Create attachments directory if needed
        self.attachments_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Download the image
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; TanaExporter/1.0)'}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                with open(local_path, 'wb') as f:
                    f.write(response.read())

            self.downloaded_images[url] = filename
            return filename

        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
            self.image_download_errors.append((url, str(e)))
            return None

    def is_image_url(self, url: str) -> bool:
        """Check if a URL points to an image file."""
        url_lower = url.lower()
        return any(ext in url_lower for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'])

    def clean_node_name(self, name: str) -> str:
        """Remove HTML tags and clean up node names."""
        if not name:
            return ''

        # Decode HTML entities
        name = html.unescape(name)

        # Remove span references but keep any alias text
        def replace_ref(match):
            ref_type = match.group(1)
            content = match.group(3) if match.group(3) else ''
            if ref_type == 'node' and content:
                return content  # Return alias text if present
            elif ref_type == 'node':
                # Try to resolve the node reference
                node_id = match.group(2)
                if node_id in self.doc_map:
                    ref_name = self.doc_map[node_id].get('props', {}).get('name', '')
                    return self.clean_node_name(ref_name) if ref_name else ''
                return ''
            elif ref_type == 'date':
                # Parse date from JSON
                try:
                    date_json = json.loads(match.group(2).replace('&quot;', '"'))
                    return date_json.get('dateTimeString', '')
                except:
                    return ''
            return ''

        name = re.sub(
            r'<span data-inlineref-(node|date)="([^"]*)"[^>]*>([^<]*)</span>',
            replace_ref,
            name
        )

        # Remove other HTML tags
        name = re.sub(r'<[^>]+>', '', name)

        # Clean up whitespace
        name = ' '.join(name.split())

        return name.strip()

    def get_node_tags(self, doc: dict) -> list:
        """Get list of supertag names for a node."""
        meta_id = doc.get('props', {}).get('_metaNodeId')
        if not meta_id or meta_id not in self.metanode_tags:
            return []

        tag_ids = self.metanode_tags[meta_id]
        tags = []
        for tid in tag_ids:
            if tid in self.supertags:
                tag_name = self.supertags[tid]
                # Skip system tags and clean up name
                if not tag_name.startswith('(') and tag_name:
                    # Remap certain tags
                    if tag_name == '1:1':
                        tag_name = 'meeting'
                    # Make tag safe for YAML
                    safe_tag = tag_name.replace(' ', '-').lower()
                    # Remove special characters
                    safe_tag = re.sub(r'[^\w\-]', '', safe_tag)
                    if safe_tag:
                        tags.append(safe_tag)
        return tags

    def has_supertag(self, doc: dict) -> bool:
        """Check if a node has a supertag that should be exported.

        If supertag selection was used (selected_supertag_ids is populated),
        only returns True for nodes tagged with selected supertags.
        Otherwise, returns True for any supertag (excluding day tag).
        """
        meta_id = doc.get('props', {}).get('_metaNodeId')
        if not meta_id or meta_id not in self.metanode_tags:
            return False

        tag_ids = self.metanode_tags[meta_id]
        # Filter out the day tag - we don't want daily notes to count as "tagged"
        for tid in tag_ids:
            if tid != self.day_tag_id and tid in self.supertags:
                tag_name = self.supertags[tid]
                if not tag_name.startswith('(') and tag_name:
                    # If we have a supertag selection, only include selected tags
                    if self.selected_supertag_ids:
                        if tid in self.selected_supertag_ids:
                            return True
                    else:
                        return True
        return False

    def has_tag(self, doc: dict, tag_id: str) -> bool:
        """Check if a node has a specific supertag."""
        meta_id = doc.get('props', {}).get('_metaNodeId')
        if not meta_id or meta_id not in self.metanode_tags:
            return False
        return tag_id in self.metanode_tags[meta_id]

    def convert_references(self, text: str) -> str:
        """Convert Tana references to Obsidian [[links]] and image embeds."""
        if not text:
            return ''

        # Decode HTML entities
        text = html.unescape(text)

        download_images = self.settings.download_images

        def replace_node_ref(match):
            node_id = match.group(1)
            alias_text = match.group(2).strip() if match.group(2) else ''

            # Check if this node is an image URL node
            if node_id in self.image_urls:
                url = self.image_urls[node_id]
                if download_images:
                    filename = self.download_image(url)
                    if filename:
                        return f'![[{filename}]]'
                # Fallback: return as link if download fails
                return f'![{alias_text or "image"}]({url})'

            # Get the target node name
            target_name = self.node_names.get(node_id, '')
            if not target_name and node_id in self.doc_map:
                raw_name = self.doc_map[node_id].get('props', {}).get('name', '')
                target_name = self.clean_node_name(raw_name)

            if not target_name:
                return alias_text if alias_text else ''

            # Track this as a referenced node (for potential file creation)
            if node_id in self.doc_map:
                self.referenced_nodes.add(node_id)

            # Check if this node was exported - use its actual filename
            if node_id in self.exported_files:
                safe_name = self.exported_files[node_id]
            else:
                safe_name = self.sanitize_filename(target_name)

            # Use Obsidian alias format if alias differs from name
            if alias_text and alias_text != target_name:
                return f'[[{safe_name}|{alias_text}]]'
            else:
                return f'[[{safe_name}]]'

        def replace_date_ref(match):
            try:
                date_json = json.loads(match.group(1).replace('&quot;', '"'))
                date_str = date_json.get('dateTimeString', '')
                if date_str:
                    return f'[[{date_str}]]'
            except:
                pass
            return ''

        def replace_embedded_image(match):
            """Handle !<a href="URL"></a> pattern (Tana embedded images)."""
            url = match.group(1)
            if download_images and self.is_image_url(url):
                filename = self.download_image(url)
                if filename:
                    return f'![[{filename}]]'
            # Fallback
            return f'![image]({url})'

        def replace_image_link(match):
            """Handle <a href="URL">text</a> that points to an image."""
            url = match.group(1)
            link_text = match.group(2) if match.group(2) else ''

            # Check if this is an image URL
            if self.is_image_url(url):
                if download_images:
                    filename = self.download_image(url)
                    if filename:
                        return f'![[{filename}]]'
                return f'![{link_text or "image"}]({url})'

            # Not an image - keep as regular markdown link
            return f'[{link_text}]({url})'

        # Replace node references
        text = re.sub(
            r'<span data-inlineref-node="([^"]*)"[^>]*>([^<]*)</span>',
            replace_node_ref,
            text
        )

        # Replace date references
        text = re.sub(
            r'<span data-inlineref-date="([^"]*)"[^>]*>[^<]*</span>',
            replace_date_ref,
            text
        )

        # Handle Tana embedded images: !<a href="URL"></a>
        text = re.sub(
            r'!<a href="([^"]+)"[^>]*></a>',
            replace_embedded_image,
            text
        )

        # Handle regular links (some might be images)
        text = re.sub(
            r'<a href="([^"]+)"[^>]*>([^<]*)</a>',
            replace_image_link,
            text
        )

        # Remove any remaining HTML tags (like <b>, etc.)
        # But convert bold/italic first
        text = re.sub(r'<b>([^<]*)</b>', r'**\1**', text)
        text = re.sub(r'<i>([^<]*)</i>', r'*\1*', text)
        text = re.sub(r'<[^>]+>', '', text)

        return text

    def sanitize_filename(self, name: str) -> str:
        """Create a safe filename from a node name."""
        if not name:
            return 'Untitled'

        # Remove/replace invalid filename characters
        invalid_chars = '<>:"/\\|?*\n\r\t'
        for char in invalid_chars:
            name = name.replace(char, '-')

        # Collapse multiple dashes and spaces
        name = re.sub(r'-+', '-', name)
        name = re.sub(r'\s+', ' ', name)

        # Remove leading/trailing dashes, dots, and spaces
        name = name.strip('-. ')

        # Truncate by byte length (Linux max is 255 bytes, keep short for safety)
        max_bytes = 150
        while len(name.encode('utf-8')) > max_bytes:
            name = name[:-1]

        # Try to break at word boundary
        if name and len(name.encode('utf-8')) > max_bytes - 20:
            parts = name.rsplit(' ', 1)
            if len(parts) > 1 and parts[0]:
                name = parts[0]

        # Ensure we have something
        name = name.strip('-. ')

        return name if name else 'Untitled'

    def get_inline_content(self, doc: dict, depth: int = 0, visited: set = None, max_depth: int = 20) -> str:
        """Recursively build inline bullet content from children (for nodes without supertags)."""
        if visited is None:
            visited = set()

        # Prevent infinite recursion
        if depth > max_depth:
            return ''

        doc_id = doc.get('id')
        if doc_id in visited:
            return ''
        visited.add(doc_id)

        content_lines = []

        children_ids = doc.get('children', [])
        for child_id in children_ids:
            if child_id not in self.doc_map:
                continue
            if child_id in visited:
                continue

            child = self.doc_map[child_id]

            # Skip if this child should be skipped entirely
            if self.should_skip_doc(child):
                continue

            child_name = child.get('props', {}).get('name', '')
            if not child_name:
                continue

            # Check if this child is an image node (Firebase URL or has image dimensions)
            child_props = child.get('props', {})
            is_image_url_node = 'firebasestorage.googleapis.com' in child_name and self.is_image_url(child_name)
            has_image_dimensions = child_props.get('_imageWidth') is not None

            if is_image_url_node:
                # This node's name is a Firebase image URL - embed the image
                url = html.unescape(child_name.replace('&amp;', '&'))
                filename = self.download_image(url)
                if filename:
                    indent = '  ' * depth
                    content_lines.append(f'{indent}![[{filename}]]')
                continue
            elif has_image_dimensions:
                # Image with metadata - try to find the URL through metanode mapping
                if child_id in self.image_metadata_urls:
                    url = self.image_metadata_urls[child_id]
                    filename = self.download_image(url)
                    if filename:
                        indent = '  ' * depth
                        content_lines.append(f'{indent}![[{filename}]]')
                continue

            # Convert the content
            converted = self.convert_references(child_name)
            if converted:
                # Add as bullet point with appropriate indentation
                indent = '  ' * depth
                content_lines.append(f'{indent}- {converted}')

                # Recursively add children (all inline since parent had no supertag)
                child_content = self.get_inline_content(child, depth + 1, visited.copy(), max_depth)
                if child_content:
                    content_lines.append(child_content)

        return '\n'.join(content_lines)

    def get_daily_note_content(self, doc: dict, daily_date: str) -> tuple:
        """
        Build content for a daily note.
        Returns (content_string, list_of_tagged_nodes_to_export)

        - Children with supertags: create a reference [[link]] and add to export list
        - Children without supertags: inline as bullet lists
        """
        content_lines = []
        tagged_nodes_to_export = []
        visited = set()
        visited.add(doc.get('id'))

        children_ids = doc.get('children', [])
        for child_id in children_ids:
            if child_id not in self.doc_map:
                continue
            if child_id in visited:
                continue

            child = self.doc_map[child_id]

            # Skip if this child should be skipped entirely
            if self.should_skip_doc(child):
                continue

            child_name = child.get('props', {}).get('name', '')
            if not child_name:
                continue

            # Check if this child is an image node (Firebase URL or has image dimensions)
            child_props = child.get('props', {})
            is_image_url_node = 'firebasestorage.googleapis.com' in child_name and self.is_image_url(child_name)
            has_image_dimensions = child_props.get('_imageWidth') is not None

            if is_image_url_node:
                # This node's name is a Firebase image URL - embed the image
                url = html.unescape(child_name.replace('&amp;', '&'))
                filename = self.download_image(url)
                if filename:
                    content_lines.append(f'![[{filename}]]')
                continue
            elif has_image_dimensions:
                # Image with metadata - try to find the URL through metanode mapping
                if child_id in self.image_metadata_urls:
                    url = self.image_metadata_urls[child_id]
                    filename = self.download_image(url)
                    if filename:
                        content_lines.append(f'![[{filename}]]')
                continue

            # Check if this child has a supertag
            if self.has_supertag(child):
                visited.add(child_id)
                # This node should be a separate file - add a reference
                clean_name = self.clean_node_name(child_name)
                tags = self.get_node_tags(child)
                tag_display = ' #' + ' #'.join(tags) if tags else ''

                # Always use base filename (duplicates will be merged)
                base_filename = self.sanitize_filename(clean_name)

                # Track this node -> filename mapping
                self.exported_files[child_id] = base_filename

                # Add reference to daily note (always points to merged file)
                content_lines.append(f'- [[{base_filename}]]{tag_display}')

                # Queue this node for merging
                tagged_nodes_to_export.append((child, base_filename, daily_date))
            else:
                # No supertag - inline as bullet list
                converted = self.convert_references(child_name)
                if converted:
                    content_lines.append(f'- {converted}')

                    # Recursively add all children as inline content
                    # Pass a fresh visited set starting with just the daily note
                    inline_visited = {doc.get('id')}
                    child_content = self.get_inline_content(child, depth=1, visited=inline_visited)
                    if child_content:
                        content_lines.append(child_content)

        return '\n'.join(content_lines), tagged_nodes_to_export

    def extract_references_from_field(self, field_name: str) -> list:
        """Extract node references from a field's name text.

        Returns a list of (node_id, display_name) tuples for each reference found.
        """
        if not field_name:
            return []

        references = []

        # Find all inline node references: <span data-inlineref-node="ID">alias</span>
        pattern = r'<span data-inlineref-node="([^"]*)"[^>]*>([^<]*)</span>'
        for match in re.finditer(pattern, field_name):
            node_id = match.group(1)
            alias_text = match.group(2).strip() if match.group(2) else ''

            # Get the target node name
            target_name = self.node_names.get(node_id, '')
            if not target_name and node_id in self.doc_map:
                raw_name = self.doc_map[node_id].get('props', {}).get('name', '')
                target_name = self.clean_node_name(raw_name)

            display_name = alias_text if alias_text else target_name
            if display_name:
                references.append((node_id, display_name))

        return references

    def get_field_by_metanode_id(self, doc: dict, field_metanode_id: str) -> dict:
        """Find a child field node by its metanode ID."""
        for child_id in doc.get('children', []):
            if child_id not in self.doc_map:
                continue
            child = self.doc_map[child_id]
            meta_id = child.get('props', {}).get('_metaNodeId')
            if meta_id == field_metanode_id:
                return child
        return None

    def create_frontmatter(self, tags: list, doc: dict = None, daily_date: str = None) -> str:
        """Create YAML frontmatter with tags, date, and dynamic field values."""
        dynamic_fields = {}

        if doc:
            # Get dynamic field values from configured supertag fields
            node_id = doc.get('id', '')
            dynamic_fields = self.get_all_field_values(node_id)

        if not tags and not daily_date and not dynamic_fields:
            return ''

        lines = ['---']
        if tags:
            lines.append('tags:')
            for tag in tags:
                lines.append(f'  - {tag}')
        if daily_date:
            lines.append(f'Date: "[[{daily_date}]]"')

        # Add dynamic field values from configured supertag fields
        for field_name, field_value in dynamic_fields.items():
            lines.append(self._format_frontmatter_field(field_name, field_value))

        lines.append('---')
        lines.append('')

        return '\n'.join(lines)

    def _format_frontmatter_field(self, field_name: str, field_value) -> str:
        """Format a field value for YAML frontmatter.

        Handles:
        - Booleans -> lowercase true/false
        - Lists -> YAML list format
        - Strings with special chars -> quoted (with inner quotes escaped)
        - Numbers -> unquoted
        """
        if isinstance(field_value, bool):
            return f'{field_name}: {str(field_value).lower()}'
        elif isinstance(field_value, list):
            if len(field_value) == 1:
                return self._format_frontmatter_field(field_name, field_value[0])
            lines = [f'{field_name}:']
            for val in field_value:
                # Quote strings that contain special characters
                if isinstance(val, str) and any(c in val for c in ':#{}[]|>&*!"'):
                    # Escape inner double quotes and backslashes for valid YAML
                    escaped_val = val.replace('\\', '\\\\').replace('"', '\\"')
                    lines.append(f'  - "{escaped_val}"')
                else:
                    lines.append(f'  - {val}')
            return '\n'.join(lines)
        elif isinstance(field_value, (int, float)):
            return f'{field_name}: {field_value}'
        else:
            # String value - quote if it contains special YAML characters
            val_str = str(field_value)
            if any(c in val_str for c in ':#{}[]|>&*!"') or val_str.startswith('"'):
                # Escape inner double quotes and backslashes for valid YAML
                escaped_val = val_str.replace('\\', '\\\\').replace('"', '\\"')
                return f'{field_name}: "{escaped_val}"'
            return f'{field_name}: {val_str}'

    def create_merged_frontmatter(self, tags: set, dynamic_fields: dict,
                                   earliest_date: str = None) -> str:
        """Create YAML frontmatter from aggregated/merged data."""
        if not tags and not dynamic_fields and not earliest_date:
            return ''

        lines = ['---']
        if tags:
            lines.append('tags:')
            for tag in sorted(tags):
                lines.append(f'  - {tag}')
        if earliest_date:
            lines.append(f'Date: "[[{earliest_date}]]"')

        # Add dynamic field values
        for field_name, field_values in sorted(dynamic_fields.items()):
            # Convert set to sorted list for consistent output
            if isinstance(field_values, set):
                field_values = sorted(field_values)
            lines.append(self._format_frontmatter_field(field_name, field_values))

        lines.append('---')
        lines.append('')

        return '\n'.join(lines)

    def write_merged_files(self) -> tuple:
        """Write all pending merged files."""
        merged_count = 0
        single_count = 0

        total = len(self.pending_merges)
        for idx, (filename, entries) in enumerate(self.pending_merges.items()):
            self.check_cancelled()

            if idx % 50 == 0:
                self.report_progress("Writing", idx, total, f"Writing merged files ({idx}/{total})")

            # Sort entries by date (None/undated entries go to the end)
            entries.sort(key=lambda x: x[0] if x[0] else '9999-99-99')

            # Collect aggregated frontmatter data
            all_tags = set()
            all_dynamic_fields = {}  # field_name -> set of values
            earliest_date = None
            folder = entries[0][2]  # Use folder from first entry

            for date, doc, _ in entries:
                all_tags.update(self.get_node_tags(doc))
                # Aggregate dynamic field values
                node_id = doc.get('id', '')
                node_fields = self.get_all_field_values(node_id)
                for field_name, field_value in node_fields.items():
                    if field_name not in all_dynamic_fields:
                        all_dynamic_fields[field_name] = set()
                    # Add value(s) to the set
                    if isinstance(field_value, list):
                        all_dynamic_fields[field_name].update(field_value)
                    elif isinstance(field_value, bool):
                        # For booleans, keep track of True/False separately
                        all_dynamic_fields[field_name].add(field_value)
                    else:
                        all_dynamic_fields[field_name].add(field_value)

                if date and (not earliest_date or date < earliest_date):
                    earliest_date = date

            # Build frontmatter
            frontmatter = self.create_merged_frontmatter(
                all_tags, all_dynamic_fields, earliest_date
            )

            # Build content
            content_parts = []
            if frontmatter:
                content_parts.append(frontmatter)

            if len(entries) == 1:
                # Single entry - no date header needed
                single_count += 1
                date, doc, _ = entries[0]
                children_content = self.get_inline_content(doc)
                if children_content:
                    content_parts.append(children_content)
            else:
                # Multiple entries - add date headers for each section
                merged_count += 1
                sections = []
                for date, doc, _ in entries:
                    children_content = self.get_inline_content(doc)
                    if date:
                        header = f'# [[{date}]]'
                    else:
                        header = '# Undated'

                    if children_content:
                        sections.append(f'{header}\n\n{children_content}')
                    else:
                        sections.append(header)

                content_parts.append('\n\n'.join(sections))

            # Write file
            folder.mkdir(parents=True, exist_ok=True)
            file_path = folder / f'{filename}.md'

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content_parts))

        return single_count, merged_count

    def is_daily_note(self, doc: dict) -> bool:
        """Check if a node is a daily note."""
        doc_type = doc.get('props', {}).get('_docType')
        name = doc.get('props', {}).get('name', '')

        # Check if it's a journalPart with a date-like name
        if doc_type == 'journalPart':
            if re.match(r'\d{4}-\d{2}-\d{2}', name):
                return True

        # Also check for day tag
        if self.day_tag_id and self.has_tag(doc, self.day_tag_id):
            if re.match(r'\d{4}-\d{2}-\d{2}', name):
                return True

        return False

    def should_skip_doc(self, doc: dict) -> bool:
        """Check if a document should be completely skipped."""
        # Skip system nodes
        if doc['id'].startswith('SYS_'):
            return True

        # Skip certain doc types
        doc_type = doc.get('props', {}).get('_docType')
        skip_types = [
            'metanode', 'tuple', 'workspace', 'search', 'viewDef',
            'transcriptLine', 'transcript', 'associatedData', 'visual',
            'chat', 'chatbot', 'settings', 'settingsSection', 'syntax',
            'command', 'systemTool', 'placeholder', 'home', 'attrDef',
            'tagDef'
        ]
        if doc_type in skip_types:
            return True

        # Skip if in trash (check ID and owner)
        doc_id = doc.get('id', '')
        owner_id = doc.get('props', {}).get('_ownerId', '')
        if 'TRASH' in owner_id or 'TRASH' in doc_id:
            return True

        # Check if any ancestor is in trash
        if self.is_in_trash(doc):
            return True

        # Skip special system-like nodes
        if doc['id'].endswith(('_WORKSPACE', '_SCHEMA', '_TRASH', '_INBOX',
                               '_STASH', '_SEARCHES', '_QUICK_ADD', '_SIDEBAR_AREAS',
                               '_AVATAR', '_USERS', '_CHATDRAFTS', '_MOVETO',
                               '_CAPTURE_INBOX', '_PINS', '_TRAILING_SIDEBAR')):
            return True

        # Must have a name
        name = doc.get('props', {}).get('name', '')
        if not name:
            return True

        # Skip if name is just a reference with no content
        clean_name = self.clean_node_name(name)
        if not clean_name:
            return True

        # Skip files that would be named like "! 2.md", "!11.md", etc.
        if re.match(r'^!+\s*\d*$', clean_name.strip()):
            return True

        return False

    def should_skip_referenced_node(self, doc: dict) -> bool:
        """Check if a referenced node should be skipped (less strict than should_skip_doc)."""
        # Skip system nodes
        if doc['id'].startswith('SYS_'):
            return True

        # Skip certain doc types
        doc_type = doc.get('props', {}).get('_docType')
        skip_types = [
            'metanode', 'tuple', 'workspace', 'search', 'viewDef',
            'transcriptLine', 'transcript', 'associatedData', 'visual',
            'chat', 'chatbot', 'settings', 'settingsSection', 'syntax',
            'command', 'systemTool', 'placeholder', 'home', 'attrDef',
            'tagDef', 'journalPart'  # Also skip daily notes - they have their own files
        ]
        if doc_type in skip_types:
            return True

        # Skip if in trash
        if self.is_in_trash(doc):
            return True

        # Skip special system-like nodes
        if doc['id'].endswith(('_WORKSPACE', '_SCHEMA', '_TRASH', '_INBOX',
                               '_STASH', '_SEARCHES', '_QUICK_ADD', '_SIDEBAR_AREAS',
                               '_AVATAR', '_USERS', '_CHATDRAFTS', '_MOVETO',
                               '_CAPTURE_INBOX', '_PINS', '_TRAILING_SIDEBAR')):
            return True

        return False

    def is_in_trash(self, doc: dict, visited: set = None) -> bool:
        """Check if a document or any of its ancestors is in the trash."""
        if visited is None:
            visited = set()

        doc_id = doc.get('id', '')
        if doc_id in visited:
            return False
        visited.add(doc_id)

        # Check if this doc is in trash
        if 'TRASH' in doc_id:
            return True

        owner_id = doc.get('props', {}).get('_ownerId', '')
        if 'TRASH' in owner_id:
            return True

        # Check parent
        if owner_id and owner_id in self.doc_map:
            return self.is_in_trash(self.doc_map[owner_id], visited)

        return False

    def export_tagged_node(self, doc: dict, filename: str, folder: Path, daily_date: str = None) -> str:
        """Export a tagged node to a markdown file."""
        name = doc.get('props', {}).get('name', '')

        # Get tags
        tags = self.get_node_tags(doc)

        # Determine the date for frontmatter
        node_date = daily_date
        if not node_date:
            node_date = self.get_node_created_date(doc)

        # Build content
        content_parts = []

        # Build frontmatter with tags, date, and project reference
        frontmatter = self.create_frontmatter(tags, doc, node_date)
        if frontmatter:
            content_parts.append(frontmatter)

        # Add children content (all inline since this is the tagged node's content)
        children_content = self.get_inline_content(doc)
        if children_content:
            content_parts.append(children_content)

        # Write file
        folder.mkdir(parents=True, exist_ok=True)
        file_path = folder / f'{filename}.md'

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content_parts))

        return str(file_path)

    def export_daily_note(self, doc: dict, folder: Path) -> tuple:
        """
        Export a daily note and return list of tagged nodes to export.
        """
        name = doc.get('props', {}).get('name', '')

        # Extract date
        date_match = re.match(r'(\d{4}-\d{2}-\d{2})', name)
        if not date_match:
            return []

        daily_date = date_match.group(1)
        filename = f'{daily_date}.md'

        # Build content
        content_parts = []

        # Get daily note content and list of tagged nodes
        body_content, tagged_nodes = self.get_daily_note_content(doc, daily_date)

        # Skip blank daily notes (no content and no tagged nodes)
        if not body_content and not tagged_nodes:
            return None

        if body_content:
            content_parts.append(body_content)

        # Write file
        folder.mkdir(parents=True, exist_ok=True)
        file_path = folder / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content_parts))

        return tagged_nodes

    def get_node_created_date(self, doc: dict) -> str:
        """Extract the creation date from a node's properties, if available.

        Returns date string in YYYY-MM-DD format, or None if not available.
        """
        props = doc.get('props', {})

        # Try common timestamp field names
        timestamp = None
        for field in ['_createdAt', 'createdAt', '_created', 'created', 'createdTime']:
            if field in props:
                timestamp = props[field]
                break

        if not timestamp:
            return None

        try:
            # Handle millisecond timestamps (common in JS-based systems)
            if isinstance(timestamp, (int, float)):
                # If timestamp is in milliseconds (13+ digits), convert to seconds
                if timestamp > 1e12:
                    timestamp = timestamp / 1000
                dt = datetime.fromtimestamp(timestamp)
                return dt.strftime('%Y-%m-%d')
            # Handle ISO format strings
            elif isinstance(timestamp, str):
                # Try parsing ISO format
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d')
        except (ValueError, OSError, OverflowError):
            pass

        return None

    def find_daily_note_ancestor(self, doc: dict, visited: set = None) -> str:
        """Find the daily note date that contains this node, if any."""
        if visited is None:
            visited = set()

        doc_id = doc.get('id')
        if doc_id in visited:
            return None
        visited.add(doc_id)

        # Check if this is a daily note
        if self.is_daily_note(doc):
            name = doc.get('props', {}).get('name', '')
            date_match = re.match(r'(\d{4}-\d{2}-\d{2})', name)
            if date_match:
                return date_match.group(1)

        # Check parent
        owner_id = doc.get('props', {}).get('_ownerId')
        if owner_id and owner_id in self.doc_map:
            return self.find_daily_note_ancestor(self.doc_map[owner_id], visited)

        return None

    def run(self) -> ConversionResult:
        """Main export process with progress reporting."""
        try:
            # Phase 0: Load and index
            self.load_data()
            self.check_cancelled()
            self.build_indices()
            self.check_cancelled()

            # Create output directories
            self.output_dir.mkdir(parents=True, exist_ok=True)

            # Get daily notes folder from day tag's configured folder (or default)
            daily_notes_dir = self.output_dir
            if self.day_tag_id and self.day_tag_id in self.supertag_folders:
                folder_name = self.supertag_folders[self.day_tag_id]
                if folder_name:
                    daily_notes_dir = self.output_dir / folder_name

            # Counters
            daily_count = 0
            blank_daily_count = 0
            tagged_count = 0
            skipped_count = 0

            # Collect all tagged nodes to export (from daily notes)
            all_tagged_nodes = []

            # Phase 1: Export daily notes (only if #day supertag is selected)
            # Check if day tag is selected (or if no selection filter is active)
            export_daily_notes = True
            if self.selected_supertag_ids and self.day_tag_id:
                export_daily_notes = self.day_tag_id in self.selected_supertag_ids

            if export_daily_notes:
                self.report_progress("Daily Notes", 0, len(self.docs), "Exporting daily notes...")

                for idx, doc in enumerate(self.docs):
                    self.check_cancelled()

                    if self.should_skip_doc(doc):
                        skipped_count += 1
                        continue

                    if self.is_daily_note(doc):
                        tagged_nodes = self.export_daily_note(doc, daily_notes_dir)
                        if tagged_nodes is None:
                            # Blank daily note - skipped
                            blank_daily_count += 1
                        else:
                            all_tagged_nodes.extend(tagged_nodes)
                            daily_count += 1

                        if daily_count % 100 == 0:
                            self.report_progress("Daily Notes", daily_count, 0, f"Exported {daily_count} daily notes...")

                self.report_progress("Daily Notes", daily_count, daily_count, f"Exported {daily_count} daily notes")
            else:
                self.report_progress("Daily Notes", 0, 0, "Skipped (day supertag not selected)")

            # Phase 2: Collect tagged nodes for merging
            self.report_progress("Tagged Nodes", 0, len(all_tagged_nodes), f"Collecting {len(all_tagged_nodes)} tagged nodes...")
            self.check_cancelled()

            for idx, (node, filename, daily_date) in enumerate(all_tagged_nodes):
                # Determine folder based on node's supertag configuration
                folder = self._get_node_output_folder(node)

                # Add to pending merges
                if filename not in self.pending_merges:
                    self.pending_merges[filename] = []
                self.pending_merges[filename].append((daily_date, node, folder))
                tagged_count += 1

                if tagged_count % 100 == 0:
                    self.report_progress("Tagged Nodes", tagged_count, len(all_tagged_nodes), f"Collected {tagged_count} tagged nodes...")

            # Phase 3: Find orphan tagged nodes (not under any daily note)
            self.report_progress("Orphan Nodes", 0, len(self.docs), "Finding orphan tagged nodes...")
            self.check_cancelled()
            orphan_count = 0

            for idx, doc in enumerate(self.docs):
                self.check_cancelled()

                if self.should_skip_doc(doc):
                    continue

                doc_id = doc.get('id')

                # Skip if already collected
                if doc_id in self.exported_files:
                    continue

                # Skip daily notes (already handled)
                if self.is_daily_note(doc):
                    continue

                # Check if this node has a supertag
                if self.has_supertag(doc):
                    name = doc.get('props', {}).get('name', '')
                    clean_name = self.clean_node_name(name)

                    # Find associated date if any
                    daily_date = self.find_daily_note_ancestor(doc)
                    if not daily_date:
                        daily_date = self.get_node_created_date(doc)

                    # Always use base filename (duplicates will be merged)
                    base_filename = self.sanitize_filename(clean_name)

                    # Track this node -> filename mapping
                    self.exported_files[doc_id] = base_filename

                    # Determine folder based on node's supertag configuration
                    folder = self._get_node_output_folder(doc)

                    # Add to pending merges
                    if base_filename not in self.pending_merges:
                        self.pending_merges[base_filename] = []
                    self.pending_merges[base_filename].append((daily_date, doc, folder))
                    orphan_count += 1

            self.report_progress("Orphan Nodes", orphan_count, orphan_count, f"Found {orphan_count} orphan tagged nodes")

            # Phase 4: Write all merged files
            self.report_progress("Writing", 0, len(self.pending_merges), f"Writing {len(self.pending_merges)} merged files...")
            self.check_cancelled()
            single_count, merged_count = self.write_merged_files()

            # Phase 5: Create files for referenced nodes that don't have files yet
            # (only if include_library_nodes is enabled)
            referenced_count = 0

            if self.settings.include_library_nodes:
                # Copy the set to avoid "Set changed size during iteration" error
                # (convert_references adds to referenced_nodes when processing content)
                referenced_nodes_snapshot = list(self.referenced_nodes)
                self.report_progress("Referenced Nodes", 0, len(referenced_nodes_snapshot), "Creating files for referenced nodes...")
                self.check_cancelled()

                for node_id in referenced_nodes_snapshot:
                    self.check_cancelled()

                    # Skip if already has a file
                    if node_id in self.exported_files:
                        continue

                    # Skip if node doesn't exist
                    if node_id not in self.doc_map:
                        continue

                    doc = self.doc_map[node_id]

                    # Skip if should be skipped (trash, system nodes, etc.)
                    if self.should_skip_referenced_node(doc):
                        continue

                    # Skip if node has any supertag (this option is for nodes WITHOUT supertags)
                    # Nodes with supertags should be exported via supertag selection, not here
                    if self._doc_has_any_supertag(doc):
                        continue

                    name = doc.get('props', {}).get('name', '')
                    clean_name = self.clean_node_name(name)
                    if not clean_name:
                        continue

                    # Create filename
                    filename = self.sanitize_filename(clean_name)

                    # Track this node -> filename mapping
                    self.exported_files[node_id] = filename

                    # Get any date context
                    node_date = self.find_daily_note_ancestor(doc)
                    if not node_date:
                        node_date = self.get_node_created_date(doc)

                    # Build content
                    content_parts = []

                    # Add frontmatter with tags if any
                    tags = self.get_node_tags(doc)
                    frontmatter = self.create_frontmatter(tags, doc, node_date)
                    if frontmatter:
                        content_parts.append(frontmatter)

                    # Add children content
                    children_content = self.get_inline_content(doc)
                    if children_content:
                        content_parts.append(children_content)

                    # Determine output folder for untagged library nodes
                    if self.settings.untagged_library_folder:
                        output_folder = self.output_dir / self.settings.untagged_library_folder
                        output_folder.mkdir(parents=True, exist_ok=True)
                    else:
                        output_folder = self.output_dir

                    # Write file
                    file_path = output_folder / f'{filename}.md'
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(content_parts))

                    referenced_count += 1

                self.report_progress("Referenced Nodes", referenced_count, referenced_count, f"Created {referenced_count} files for referenced nodes")

            # Calculate totals
            total_files_written = len(self.pending_merges) + referenced_count

            self.report_progress("Complete", total_files_written, total_files_written, "Conversion complete!")

            return ConversionResult(
                success=True,
                daily_notes_count=daily_count,
                blank_daily_notes_skipped=blank_daily_count,
                tagged_nodes_count=tagged_count,
                orphan_nodes_count=orphan_count,
                referenced_nodes_count=referenced_count,
                images_downloaded=len(self.downloaded_images),
                image_errors=self.image_download_errors.copy(),
                files_written=total_files_written,
                single_files=single_count,
                merged_files=merged_count,
            )

        except ConversionCancelled:
            return ConversionResult(success=False, error_message="Conversion cancelled by user")
        except FileAccessError as e:
            return ConversionResult(success=False, error_message=str(e))
        except Exception as e:
            return ConversionResult(success=False, error_message=f"Unexpected error: {str(e)}")
