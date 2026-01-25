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

        # Field IDs from settings
        self.project_field_id = settings.project_field_id
        self.people_involved_field_id = settings.people_involved_field_id
        self.company_field_id = settings.company_field_id
        self.cookbook_field_id = settings.cookbook_field_id
        self.url_field_id = settings.url_field_id

        # Internal state
        self.docs = []
        self.doc_map = {}
        self.supertags = {}  # tag_id -> tag_name
        self.metanode_tags = {}  # metanode_id -> set of tag_ids
        self.node_names = {}  # node_id -> clean name (for reference resolution)
        self.task_tag_id = None
        self.day_tag_id = None
        self.week_tag_id = None
        self.year_tag_id = None
        self.readwise_tag_id = None
        self.meeting_tag_id = None
        self.note_tag_id = None
        self.project_tag_id = None
        self.person_tag_id = None
        self.one_on_one_tag_id = None  # 1:1 tag (maps to meeting)
        self.recipe_tag_id = None
        self.highlight_tag_ids = set()  # Can have multiple tags with same name
        self.field_definition_tag_ids = set()  # Can have multiple tags with same name
        self.exported_files = {}  # node_id -> filename (without .md)
        self.used_filenames = {}  # filename -> node_id (to track duplicates)
        self.referenced_nodes = set()  # node IDs referenced in content via [[links]]
        self.pending_merges = {}  # base_filename -> list of (date, doc, folder)

        # Image handling
        self.attachments_dir = self.output_dir / 'Attachments'
        self.downloaded_images = {}  # url -> local filename
        self.image_download_errors = []  # track failed downloads
        self.image_urls = {}  # node_id -> firebase_url
        self.image_metadata_urls = {}  # node_id -> firebase_url

        # Selected supertags filter (from wizard selection)
        self.selected_supertag_ids = set()
        if settings.supertag_configs:
            self.selected_supertag_ids = {
                config.supertag_id for config in settings.supertag_configs
                if config.include
            }

        # Indices for field values (populated via tuples)
        self.meeting_projects = {}  # meeting_id -> list of project node IDs
        self.meeting_people = {}  # meeting_id -> list of person node IDs
        self.person_companies = {}  # person_id -> list of company node IDs
        self.recipe_cookbooks = {}  # recipe_id -> list of cookbook node IDs
        self.node_urls = {}  # node_id -> URL string

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

    def get_field_value(self, node_id: str, field_id: str):
        """Get the value(s) for a specific field on a node.

        Returns the resolved value(s) based on field type:
        - For reference fields: returns the node name(s)
        - For text/option fields: returns the value text
        - For checkbox fields: returns True/False based on SYS_V03 presence

        Returns: single value or list of values, or None if not set
        """
        if node_id not in self.node_field_values:
            return None

        node_fields = self.node_field_values[node_id]
        if field_id not in node_fields:
            return None

        value_ids = node_fields[field_id]
        if not value_ids:
            return None

        values = []
        for value_id in value_ids:
            # Check for checkbox "Yes" value
            if value_id == 'SYS_V03':
                return True
            elif value_id == 'SYS_V04':  # "No" value
                return False

            # Get value from doc
            value_doc = self.doc_map.get(value_id)
            if value_doc:
                value_name = value_doc.get('props', {}).get('name', '')
                if value_name:
                    values.append(value_name)

        if not values:
            return None
        elif len(values) == 1:
            return values[0]
        else:
            return values

    def get_all_field_values(self, node_id: str) -> dict:
        """Get all configured field values for a node.

        Returns dict with frontmatter_name as key and formatted value.
        Only includes fields that have values set.
        """
        result = {}

        if node_id not in self.node_field_values:
            return result

        for field_id, mapping_info in self.field_info_map.items():
            value = self.get_field_value(node_id, field_id)
            if value is None:
                continue

            frontmatter_name = mapping_info['frontmatter_name']
            transform = mapping_info['transform']

            # Apply transform
            if transform == 'wikilink':
                if isinstance(value, list):
                    result[frontmatter_name] = [f'[[{v}]]' for v in value]
                else:
                    result[frontmatter_name] = f'[[{value}]]'
            elif transform == 'status':
                # Status transform: convert to done/open based on boolean
                if isinstance(value, bool):
                    result[frontmatter_name] = 'done' if value else 'open'
                else:
                    result[frontmatter_name] = value
            else:
                # No transform
                result[frontmatter_name] = value

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
                if tag_name.lower() == 'task':
                    self.task_tag_id = doc['id']
                elif tag_name.lower() == 'day':
                    self.day_tag_id = doc['id']
                elif tag_name.lower() == 'week':
                    self.week_tag_id = doc['id']
                elif tag_name.lower() == 'year':
                    self.year_tag_id = doc['id']
                elif tag_name.lower() == 'readwise':
                    self.readwise_tag_id = doc['id']
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
                elif tag_name.lower() == 'highlight':
                    self.highlight_tag_ids.add(doc['id'])
                elif tag_name.lower() == 'field-definition' or tag_name.lower() == 'field definition':
                    self.field_definition_tag_ids.add(doc['id'])

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

        # Build meeting -> project/people indices via tuples
        for doc in self.docs:
            if doc.get('props', {}).get('_docType') == 'tuple':
                children = doc.get('children', [])
                owner_id = doc.get('props', {}).get('_ownerId')
                if not owner_id or len(children) < 2:
                    continue

                # Check for Project field
                if self.project_field_id in children:
                    value_ids = [c for c in children if c != self.project_field_id]
                    for value_id in value_ids:
                        if value_id in self.doc_map:
                            if owner_id not in self.meeting_projects:
                                self.meeting_projects[owner_id] = []
                            self.meeting_projects[owner_id].append(value_id)

                # Check for People Involved field
                if self.people_involved_field_id in children:
                    value_ids = [c for c in children if c != self.people_involved_field_id]
                    for value_id in value_ids:
                        if value_id in self.doc_map:
                            if owner_id not in self.meeting_people:
                                self.meeting_people[owner_id] = []
                            self.meeting_people[owner_id].append(value_id)

                # Check for Company field (on #person nodes)
                if self.company_field_id in children:
                    value_ids = [c for c in children if c != self.company_field_id]
                    for value_id in value_ids:
                        if value_id in self.doc_map:
                            if owner_id not in self.person_companies:
                                self.person_companies[owner_id] = []
                            self.person_companies[owner_id].append(value_id)

                # Check for Cookbook field (on #recipe nodes)
                if self.cookbook_field_id in children:
                    value_ids = [c for c in children if c != self.cookbook_field_id]
                    for value_id in value_ids:
                        if value_id in self.doc_map:
                            if owner_id not in self.recipe_cookbooks:
                                self.recipe_cookbooks[owner_id] = []
                            self.recipe_cookbooks[owner_id].append(value_id)

                # Check for URL field (SYS_A78) - stores URL as node name
                if self.url_field_id in children:
                    value_ids = [c for c in children if c != self.url_field_id]
                    for value_id in value_ids:
                        if value_id in self.doc_map:
                            url_node = self.doc_map[value_id]
                            url_value = url_node.get('props', {}).get('name', '')
                            if url_value and url_value.startswith(('http://', 'https://')):
                                self.node_urls[owner_id] = html.unescape(url_value)

        self.report_progress("Indexing", message="Built field indices")
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

    def get_project_reference(self, doc: dict) -> list:
        """Get the project reference(s) for a node, if it has any.

        Returns a list of project filenames (sanitized for use as Obsidian links).
        """
        doc_id = doc.get('id')
        projects = []

        # Check if this node has project references via tuples
        if doc_id in self.meeting_projects:
            for project_node_id in self.meeting_projects[doc_id]:
                if project_node_id in self.doc_map:
                    project_node = self.doc_map[project_node_id]
                    project_name = project_node.get('props', {}).get('name', '')
                    clean_name = self.clean_node_name(project_name)
                    if clean_name:
                        # Check if this project node was exported - use its actual filename
                        if project_node_id in self.exported_files:
                            projects.append(self.exported_files[project_node_id])
                        else:
                            projects.append(self.sanitize_filename(clean_name))

        return projects

    def get_people_involved(self, doc: dict) -> list:
        """Get the people involved references for a node.

        Returns a list of person filenames (sanitized for use as Obsidian links).
        """
        doc_id = doc.get('id')
        people = []

        # Check if this node has people references via tuples
        if doc_id in self.meeting_people:
            for person_node_id in self.meeting_people[doc_id]:
                if person_node_id in self.doc_map:
                    person_node = self.doc_map[person_node_id]
                    person_name = person_node.get('props', {}).get('name', '')
                    clean_name = self.clean_node_name(person_name)
                    if clean_name:
                        # Check if this person node was exported - use its actual filename
                        if person_node_id in self.exported_files:
                            people.append(self.exported_files[person_node_id])
                        else:
                            people.append(self.sanitize_filename(clean_name))

        return people

    def get_company_reference(self, doc: dict) -> list:
        """Get the company references for a node (used for #person nodes).

        Returns a list of company filenames (sanitized for use as Obsidian links).
        """
        doc_id = doc.get('id')
        companies = []

        # Check if this node has company references via tuples
        if doc_id in self.person_companies:
            for company_node_id in self.person_companies[doc_id]:
                if company_node_id in self.doc_map:
                    company_node = self.doc_map[company_node_id]
                    company_name = company_node.get('props', {}).get('name', '')
                    clean_name = self.clean_node_name(company_name)
                    if clean_name:
                        # Check if this company node was exported - use its actual filename
                        if company_node_id in self.exported_files:
                            companies.append(self.exported_files[company_node_id])
                        else:
                            companies.append(self.sanitize_filename(clean_name))

        return companies

    def get_cookbook_reference(self, doc: dict) -> list:
        """Get the cookbook references for a node (used for #recipe nodes).

        Returns a list of cookbook filenames (sanitized for use as Obsidian links).
        """
        doc_id = doc.get('id')
        cookbooks = []

        # Check if this node has cookbook references via tuples
        if doc_id in self.recipe_cookbooks:
            for cookbook_node_id in self.recipe_cookbooks[doc_id]:
                if cookbook_node_id in self.doc_map:
                    cookbook_node = self.doc_map[cookbook_node_id]
                    cookbook_name = cookbook_node.get('props', {}).get('name', '')
                    clean_name = self.clean_node_name(cookbook_name)
                    if clean_name:
                        # Check if this cookbook node was exported - use its actual filename
                        if cookbook_node_id in self.exported_files:
                            cookbooks.append(self.exported_files[cookbook_node_id])
                        else:
                            cookbooks.append(self.sanitize_filename(clean_name))

        return cookbooks

    def get_url_value(self, doc: dict) -> str:
        """Get the URL field value for a node, if any.

        Returns the URL string or None.
        """
        doc_id = doc.get('id')
        return self.node_urls.get(doc_id)

    def get_task_status(self, doc: dict) -> str:
        """Get the task status for a node.

        Returns "done" if the task is complete, "open" if not, or None if not a task.
        The done status is stored as a '_done' timestamp property on the node.
        """
        if not self.is_task(doc):
            return None
        done_timestamp = doc.get('props', {}).get('_done')
        return "done" if done_timestamp else "open"

    def get_task_completed_date(self, doc: dict) -> str:
        """Get the completion date for a done task.

        Returns date string in YYYY-MM-DD format, or None if not done or not a task.
        The '_done' property contains the completion timestamp in milliseconds.
        """
        if not self.is_task(doc):
            return None
        done_timestamp = doc.get('props', {}).get('_done')
        if not done_timestamp:
            return None
        try:
            # Convert millisecond timestamp to date
            dt = datetime.fromtimestamp(done_timestamp / 1000)
            return dt.strftime('%Y-%m-%d')
        except (ValueError, OSError, OverflowError):
            return None

    def format_timestamp_iso(self, timestamp_ms: int) -> str:
        """Format a millisecond timestamp as ISO 8601 with timezone.

        Returns format like: 2026-01-23T18:18:35.468-05:00
        """
        if not timestamp_ms:
            return None
        try:
            # Convert milliseconds to seconds, keeping milliseconds for formatting
            dt = datetime.fromtimestamp(timestamp_ms / 1000).astimezone()
            # Format with milliseconds and timezone
            # Python's %z gives +HHMM, we need +HH:MM
            base = dt.strftime('%Y-%m-%dT%H:%M:%S')
            millis = f'.{int(timestamp_ms % 1000):03d}'
            tz = dt.strftime('%z')
            # Insert colon in timezone offset (e.g., -0500 -> -05:00)
            tz_formatted = f'{tz[:3]}:{tz[3:]}' if len(tz) == 5 else tz
            return f'{base}{millis}{tz_formatted}'
        except (ValueError, OSError, OverflowError):
            return None

    def get_node_created_timestamp(self, doc: dict) -> str:
        """Get the creation timestamp for a node in ISO 8601 format."""
        created = doc.get('props', {}).get('created')
        if created:
            return self.format_timestamp_iso(created)
        return None

    def get_node_modified_timestamp(self, doc: dict) -> str:
        """Get the last modified timestamp for a node in ISO 8601 format.

        modifiedTs can be a list or dict of timestamps - we take the max value.
        """
        modified_ts = doc.get('modifiedTs')
        if not modified_ts:
            # Fall back to created timestamp if no modifiedTs
            return self.get_node_created_timestamp(doc)

        try:
            if isinstance(modified_ts, list):
                # Filter out zeros and get max
                timestamps = [t for t in modified_ts if t and t > 0]
                if timestamps:
                    return self.format_timestamp_iso(max(timestamps))
            elif isinstance(modified_ts, dict):
                timestamps = [v for v in modified_ts.values() if v and v > 0]
                if timestamps:
                    return self.format_timestamp_iso(max(timestamps))
            elif isinstance(modified_ts, str):
                # Sometimes stored as JSON string
                parsed = json.loads(modified_ts)
                if isinstance(parsed, dict):
                    timestamps = [v for v in parsed.values() if v and v > 0]
                    if timestamps:
                        return self.format_timestamp_iso(max(timestamps))
        except (ValueError, TypeError, json.JSONDecodeError):
            pass

        # Fall back to created timestamp
        return self.get_node_created_timestamp(doc)

    def create_frontmatter(self, tags: list, doc: dict = None, daily_date: str = None) -> str:
        """Create YAML frontmatter with tags, date, project reference, people involved, company, cookbook, URL, and task status."""
        projects = []
        people_involved = []
        companies = []
        cookbooks = []
        url = None
        task_status = None
        completed_date = None
        date_created = None
        date_modified = None
        if doc:
            projects = self.get_project_reference(doc)
            people_involved = self.get_people_involved(doc)
            companies = self.get_company_reference(doc)
            cookbooks = self.get_cookbook_reference(doc)
            url = self.get_url_value(doc)
            task_status = self.get_task_status(doc)
            completed_date = self.get_task_completed_date(doc)
            if task_status:
                date_created = self.get_node_created_timestamp(doc)
                date_modified = self.get_node_modified_timestamp(doc)

        if not tags and not projects and not people_involved and not companies and not cookbooks and not url and not daily_date and not task_status:
            return ''

        lines = ['---']
        if task_status:
            lines.append(f'status: {task_status}')
            lines.append('priority: normal')
            if daily_date:
                lines.append(f'scheduled: {daily_date}')
        if completed_date:
            lines.append(f'completedDate: {completed_date}')
        if date_created:
            lines.append(f'dateCreated: {date_created}')
        if date_modified:
            lines.append(f'dateModified: {date_modified}')
        if tags:
            lines.append('tags:')
            for tag in tags:
                lines.append(f'  - {tag}')
        if daily_date:
            lines.append(f'Date: "[[{daily_date}]]"')
        if projects:
            if len(projects) == 1:
                lines.append(f'Project: "[[{projects[0]}]]"')
            else:
                lines.append('Project:')
                for project in projects:
                    lines.append(f'  - "[[{project}]]"')
        if people_involved:
            if len(people_involved) == 1:
                lines.append(f'People Involved: "[[{people_involved[0]}]]"')
            else:
                lines.append('People Involved:')
                for person in people_involved:
                    lines.append(f'  - "[[{person}]]"')
        if companies:
            if len(companies) == 1:
                lines.append(f'Company: "[[{companies[0]}]]"')
            else:
                lines.append('Company:')
                for company in companies:
                    lines.append(f'  - "[[{company}]]"')
        if cookbooks:
            if len(cookbooks) == 1:
                lines.append(f'Cookbook: "[[{cookbooks[0]}]]"')
            else:
                lines.append('Cookbook:')
                for cookbook in cookbooks:
                    lines.append(f'  - "[[{cookbook}]]"')
        if url:
            lines.append(f'URL: "{url}"')

        # Add dynamic field values from configured supertag fields
        if doc:
            node_id = doc.get('id', '')
            dynamic_fields = self.get_all_field_values(node_id)
            for field_name, field_value in dynamic_fields.items():
                # Skip fields we've already handled above (to avoid duplicates)
                if field_name.lower() in ('status', 'project', 'people_involved', 'company', 'cookbook', 'url'):
                    continue
                # Format the value for YAML
                lines.append(self._format_frontmatter_field(field_name, field_value))

        lines.append('---')
        lines.append('')

        return '\n'.join(lines)

    def _format_frontmatter_field(self, field_name: str, field_value) -> str:
        """Format a field value for YAML frontmatter.

        Handles:
        - Booleans -> lowercase true/false
        - Lists -> YAML list format
        - Strings with special chars -> quoted
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
                if isinstance(val, str) and any(c in val for c in ':#{}[]|>&*!'):
                    lines.append(f'  - "{val}"')
                else:
                    lines.append(f'  - {val}')
            return '\n'.join(lines)
        elif isinstance(field_value, (int, float)):
            return f'{field_name}: {field_value}'
        else:
            # String value - quote if it contains special YAML characters
            val_str = str(field_value)
            if any(c in val_str for c in ':#{}[]|>&*!') or val_str.startswith('"'):
                return f'{field_name}: "{val_str}"'
            return f'{field_name}: {val_str}'

    def create_merged_frontmatter(self, tags: set, projects: set, people: set,
                                   companies: set, cookbooks: set = None, urls: set = None,
                                   earliest_date: str = None, task_status: str = None,
                                   completed_date: str = None, date_created: str = None,
                                   date_modified: str = None) -> str:
        """Create YAML frontmatter from aggregated/merged data."""
        if cookbooks is None:
            cookbooks = set()
        if urls is None:
            urls = set()

        if not tags and not projects and not people and not companies and not cookbooks and not urls and not earliest_date and not task_status:
            return ''

        lines = ['---']
        if task_status:
            lines.append(f'status: {task_status}')
            lines.append('priority: normal')
            if earliest_date:
                lines.append(f'scheduled: {earliest_date}')
        if completed_date:
            lines.append(f'completedDate: {completed_date}')
        if date_created:
            lines.append(f'dateCreated: {date_created}')
        if date_modified:
            lines.append(f'dateModified: {date_modified}')
        if tags:
            lines.append('tags:')
            for tag in sorted(tags):
                lines.append(f'  - {tag}')
        if earliest_date:
            lines.append(f'Date: "[[{earliest_date}]]"')
        if projects:
            sorted_projects = sorted(projects)
            if len(sorted_projects) == 1:
                lines.append(f'Project: "[[{sorted_projects[0]}]]"')
            else:
                lines.append('Project:')
                for project in sorted_projects:
                    lines.append(f'  - "[[{project}]]"')
        if people:
            sorted_people = sorted(people)
            if len(sorted_people) == 1:
                lines.append(f'People Involved: "[[{sorted_people[0]}]]"')
            else:
                lines.append('People Involved:')
                for person in sorted_people:
                    lines.append(f'  - "[[{person}]]"')
        if companies:
            sorted_companies = sorted(companies)
            if len(sorted_companies) == 1:
                lines.append(f'Company: "[[{sorted_companies[0]}]]"')
            else:
                lines.append('Company:')
                for company in sorted_companies:
                    lines.append(f'  - "[[{company}]]"')
        if cookbooks:
            sorted_cookbooks = sorted(cookbooks)
            if len(sorted_cookbooks) == 1:
                lines.append(f'Cookbook: "[[{sorted_cookbooks[0]}]]"')
            else:
                lines.append('Cookbook:')
                for cookbook in sorted_cookbooks:
                    lines.append(f'  - "[[{cookbook}]]"')
        if urls:
            # Use the first URL if there are multiple (shouldn't normally happen)
            sorted_urls = sorted(urls)
            lines.append(f'URL: "{sorted_urls[0]}"')
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
            all_projects = set()
            all_people = set()
            all_companies = set()
            all_cookbooks = set()
            all_urls = set()
            earliest_date = None
            folder = entries[0][2]  # Use folder from first entry
            # For task status: track if any task is done and if any is a task
            has_task = False
            all_done = True
            latest_completed_date = None
            earliest_created = None
            latest_modified = None

            for date, doc, _ in entries:
                all_tags.update(self.get_node_tags(doc))
                all_projects.update(self.get_project_reference(doc))
                all_people.update(self.get_people_involved(doc))
                all_companies.update(self.get_company_reference(doc))
                all_cookbooks.update(self.get_cookbook_reference(doc))
                url = self.get_url_value(doc)
                if url:
                    all_urls.add(url)
                if date and (not earliest_date or date < earliest_date):
                    earliest_date = date
                # Check task status
                if self.is_task(doc):
                    has_task = True
                    done_timestamp = doc.get('props', {}).get('_done')
                    if not done_timestamp:
                        all_done = False
                    else:
                        # Track the most recent completion date
                        comp_date = self.get_task_completed_date(doc)
                        if comp_date and (not latest_completed_date or comp_date > latest_completed_date):
                            latest_completed_date = comp_date
                    # Track earliest created and latest modified timestamps
                    created_ts = self.get_node_created_timestamp(doc)
                    if created_ts and (not earliest_created or created_ts < earliest_created):
                        earliest_created = created_ts
                    modified_ts = self.get_node_modified_timestamp(doc)
                    if modified_ts and (not latest_modified or modified_ts > latest_modified):
                        latest_modified = modified_ts

            # Determine merged task status (done only if ALL constituent tasks are done)
            task_status = None
            completed_date = None
            date_created = None
            date_modified = None
            if has_task:
                task_status = "done" if all_done else "open"
                if all_done:
                    completed_date = latest_completed_date
                date_created = earliest_created
                date_modified = latest_modified

            # Build frontmatter
            frontmatter = self.create_merged_frontmatter(
                all_tags, all_projects, all_people, all_companies,
                all_cookbooks, all_urls, earliest_date, task_status, completed_date,
                date_created, date_modified
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

    def is_task(self, doc: dict) -> bool:
        """Check if a node is tagged as a task."""
        if not self.task_tag_id:
            return False
        return self.has_tag(doc, self.task_tag_id)

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

        # Skip nodes tagged with #week or #year (if configured)
        if self.settings.skip_week_nodes and self.week_tag_id and self.has_tag(doc, self.week_tag_id):
            return True
        if self.settings.skip_year_nodes and self.year_tag_id and self.has_tag(doc, self.year_tag_id):
            return True

        # Skip nodes tagged with #highlight or #field-definition (if configured)
        if self.settings.skip_highlights:
            for highlight_id in self.highlight_tag_ids:
                if self.has_tag(doc, highlight_id):
                    return True
        if self.settings.skip_field_definitions:
            for field_def_id in self.field_definition_tag_ids:
                if self.has_tag(doc, field_def_id):
                    return True

        # Skip Readwise integration nodes (if configured)
        if self.settings.skip_readwise:
            if self.readwise_tag_id and self.has_tag(doc, self.readwise_tag_id):
                return True
            # Also skip if name contains Readwise indicators
            if 'readwise' in name.lower():
                return True

        # Skip nodes with "(highlights)" in the title
        if '(highlights)' in clean_name.lower():
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

        # Skip nodes tagged with skippable tags (using settings)
        if self.settings.skip_week_nodes and self.week_tag_id and self.has_tag(doc, self.week_tag_id):
            return True
        if self.settings.skip_year_nodes and self.year_tag_id and self.has_tag(doc, self.year_tag_id):
            return True
        if self.settings.skip_highlights:
            for highlight_id in self.highlight_tag_ids:
                if self.has_tag(doc, highlight_id):
                    return True
        if self.settings.skip_field_definitions:
            for field_def_id in self.field_definition_tag_ids:
                if self.has_tag(doc, field_def_id):
                    return True
        if self.settings.skip_readwise and self.readwise_tag_id and self.has_tag(doc, self.readwise_tag_id):
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
            daily_notes_dir = self.output_dir / 'Daily Notes'
            tasks_dir = self.output_dir / 'Tasks'

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
                # Determine folder based on tags
                if self.is_task(node):
                    folder = tasks_dir
                else:
                    folder = self.output_dir

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

                    # Determine folder
                    if self.is_task(doc):
                        folder = tasks_dir
                    else:
                        folder = self.output_dir

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

                    # Write file
                    file_path = self.output_dir / f'{filename}.md'
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
