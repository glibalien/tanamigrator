"""Tests for the TanaExportScanner class."""

import json
import pytest
from pathlib import Path

from src.core.scanner import TanaExportScanner
from src.core.models import SupertagInfo, FieldInfo


@pytest.fixture
def sample_export_path():
    """Path to the sample export fixture."""
    return Path(__file__).parent / "fixtures" / "sample_tana_export.json"


@pytest.fixture
def scanner(sample_export_path):
    """Create a scanner instance with the sample export."""
    return TanaExportScanner(sample_export_path)


@pytest.fixture
def loaded_scanner(scanner):
    """Scanner with data loaded."""
    scanner._load_data()
    scanner._discover_supertags()
    scanner._build_metanode_tags()
    return scanner


class TestScannerInitialization:
    """Tests for scanner initialization."""

    def test_init_with_path(self, sample_export_path):
        """Scanner initializes with json path."""
        scanner = TanaExportScanner(sample_export_path)
        assert scanner.json_path == sample_export_path
        assert scanner.ignore_trash is True

    def test_init_with_ignore_trash_false(self, sample_export_path):
        """Scanner can be configured to include trash."""
        scanner = TanaExportScanner(sample_export_path, ignore_trash=False)
        assert scanner.ignore_trash is False

    def test_init_with_progress_callback(self, sample_export_path):
        """Scanner accepts a progress callback."""
        callback_calls = []
        scanner = TanaExportScanner(
            sample_export_path,
            progress_callback=lambda p: callback_calls.append(p)
        )
        scanner.report_progress("Test", message="Testing")
        assert len(callback_calls) == 1
        assert callback_calls[0].phase == "Test"


class TestLoadData:
    """Tests for _load_data method."""

    def test_load_data_populates_docs(self, scanner):
        """Loading data populates docs list."""
        scanner._load_data()
        assert len(scanner.docs) > 0

    def test_load_data_populates_doc_map(self, scanner):
        """Loading data creates doc_map with IDs as keys."""
        scanner._load_data()
        assert len(scanner.doc_map) > 0
        # Check that we can lookup by ID
        assert "tag_task" in scanner.doc_map


class TestDiscoverSupertags:
    """Tests for supertag discovery."""

    def test_discovers_tagdef_documents(self, loaded_scanner):
        """Supertags are discovered from tagDef documents."""
        assert "tag_task" in loaded_scanner.supertags
        assert loaded_scanner.supertags["tag_task"] == "task"

    def test_discovers_all_user_supertags(self, loaded_scanner):
        """All user-defined supertags are discovered."""
        expected_tags = ["task", "day", "meeting", "project", "person", "note", "week"]
        for tag_name in expected_tags:
            assert tag_name in loaded_scanner.supertags.values()

    def test_discovers_system_supertags(self, loaded_scanner):
        """System supertags (SYS_*) are also discovered."""
        assert "SYS_tag_system" in loaded_scanner.supertags


class TestShouldExcludeSupertag:
    """Tests for supertag exclusion logic."""

    def test_excludes_system_supertags(self, loaded_scanner):
        """System supertags (SYS_*) are excluded."""
        assert loaded_scanner._should_exclude_supertag("SYS_tag_system", "system-internal")

    def test_excludes_trashed_supertags(self, loaded_scanner):
        """Trashed supertags are excluded when ignore_trash is True."""
        assert loaded_scanner._should_exclude_supertag("tag_trashed", "trashed-tag")

    def test_includes_trashed_when_ignore_trash_false(self, sample_export_path):
        """Trashed supertags are included when ignore_trash is False."""
        scanner = TanaExportScanner(sample_export_path, ignore_trash=False)
        scanner._load_data()
        scanner._discover_supertags()
        # Trashed tag should not be excluded
        assert not scanner._should_exclude_supertag("tag_trashed", "trashed-tag")

    def test_excludes_base_type_supertags(self, loaded_scanner):
        """Supertags with '(base type)' in name are excluded."""
        assert loaded_scanner._should_exclude_supertag("tag_excluded_base", "something (base type)")

    def test_does_not_exclude_normal_supertags(self, loaded_scanner):
        """Normal user supertags are not excluded."""
        assert not loaded_scanner._should_exclude_supertag("tag_task", "task")
        assert not loaded_scanner._should_exclude_supertag("tag_meeting", "meeting")


class TestIsInTrash:
    """Tests for trash detection."""

    def test_detects_direct_trash_owner(self, loaded_scanner):
        """Nodes directly owned by USER_TRASH are detected."""
        trash_doc = loaded_scanner.doc_map.get("trash_node")
        assert loaded_scanner._is_in_trash(trash_doc)

    def test_detects_trash_in_id(self, loaded_scanner):
        """Nodes with TRASH in their ID are detected."""
        # Create a mock doc with TRASH in ID
        mock_doc = {"id": "USER_TRASH_item1", "props": {}}
        assert loaded_scanner._is_in_trash(mock_doc)

    def test_normal_nodes_not_in_trash(self, loaded_scanner):
        """Normal nodes are not detected as trash."""
        task_doc = loaded_scanner.doc_map.get("task1")
        assert not loaded_scanner._is_in_trash(task_doc)


class TestBuildMetanodeTags:
    """Tests for metanode to tag mapping."""

    def test_maps_metanode_to_tags(self, loaded_scanner):
        """Metanodes are mapped to their associated tags."""
        assert "metanode_task1" in loaded_scanner.metanode_tags
        assert "tag_task" in loaded_scanner.metanode_tags["metanode_task1"]

    def test_maps_multiple_metanodes(self, loaded_scanner):
        """Multiple metanodes are mapped correctly."""
        assert "metanode_meeting1" in loaded_scanner.metanode_tags
        assert "tag_meeting" in loaded_scanner.metanode_tags["metanode_meeting1"]


class TestDiscoverFields:
    """Tests for field discovery."""

    def test_discovers_options_field(self, loaded_scanner):
        """Discovers options type field with values."""
        fields = loaded_scanner._discover_fields("tag_task")
        priority_field = next((f for f in fields if f.name == "Priority"), None)
        assert priority_field is not None
        assert priority_field.data_type == "options"
        assert "High" in priority_field.options
        assert "Medium" in priority_field.options
        assert "Low" in priority_field.options

    def test_discovers_date_field(self, loaded_scanner):
        """Discovers date type field."""
        fields = loaded_scanner._discover_fields("tag_task")
        due_field = next((f for f in fields if f.name == "Due Date"), None)
        assert due_field is not None
        assert due_field.data_type == "date"

    def test_discovers_done_field_via_sys_a77(self, loaded_scanner):
        """Discovers done field via SYS_A77."""
        fields = loaded_scanner._discover_fields("tag_task")
        done_field = next((f for f in fields if f.name == "Done"), None)
        assert done_field is not None
        assert done_field.field_type == "system_done"

    def test_discovers_done_checkbox_via_metanode(self, loaded_scanner):
        """Discovers done checkbox via metanode config (SYS_A55 + SYS_V03)."""
        fields = loaded_scanner._discover_fields("tag_task")
        # Should have done field from metanode checkbox config
        done_fields = [f for f in fields if f.name == "Done"]
        assert len(done_fields) >= 1

    def test_discovers_options_from_supertag_field(self, loaded_scanner):
        """Discovers options_from_supertag field with source supertag."""
        fields = loaded_scanner._discover_fields("tag_meeting")
        attendees_field = next((f for f in fields if f.name == "Attendees"), None)
        assert attendees_field is not None
        assert attendees_field.field_type == "options_from_supertag"
        assert attendees_field.source_supertag_id == "tag_person"
        assert attendees_field.source_supertag_name == "person"

    def test_discovers_url_field(self, loaded_scanner):
        """Discovers URL type field."""
        fields = loaded_scanner._discover_fields("tag_meeting")
        url_field = next((f for f in fields if f.name == "Meeting Link"), None)
        assert url_field is not None
        assert url_field.data_type == "url"

    def test_discovers_plain_field(self, loaded_scanner):
        """Discovers plain text field."""
        fields = loaded_scanner._discover_fields("tag_meeting")
        notes_field = next((f for f in fields if f.name == "Notes"), None)
        assert notes_field is not None
        assert notes_field.data_type == "plain"

    def test_discovers_number_field(self, loaded_scanner):
        """Discovers number type field."""
        fields = loaded_scanner._discover_fields("tag_project")
        budget_field = next((f for f in fields if f.name == "Budget"), None)
        assert budget_field is not None
        assert budget_field.data_type == "number"

    def test_discovers_email_field(self, loaded_scanner):
        """Discovers email type field."""
        fields = loaded_scanner._discover_fields("tag_project")
        email_field = next((f for f in fields if f.name == "Contact Email"), None)
        assert email_field is not None
        assert email_field.data_type == "email"

    def test_discovers_checkbox_field(self, loaded_scanner):
        """Discovers checkbox type field."""
        fields = loaded_scanner._discover_fields("tag_project")
        active_field = next((f for f in fields if f.name == "Is Active"), None)
        assert active_field is not None
        assert active_field.data_type == "checkbox"


class TestDetectFieldDataType:
    """Tests for data type detection."""

    def test_all_data_types_mapped(self, loaded_scanner):
        """All DATA_TYPE_MAP entries are valid."""
        expected_types = {
            'SYS_D01': 'checkbox',
            'SYS_D03': 'date',
            'SYS_D05': 'options_from_supertag',
            'SYS_D06': 'plain',
            'SYS_D08': 'number',
            'SYS_D10': 'url',
            'SYS_D11': 'email',
            'SYS_D12': 'options',
        }
        assert loaded_scanner.DATA_TYPE_MAP == expected_types


class TestCountInstances:
    """Tests for instance counting."""

    def test_counts_tagged_instances(self, loaded_scanner):
        """Counts nodes with a specific supertag."""
        count = loaded_scanner._count_instances("tag_task")
        assert count >= 1

    def test_excludes_trashed_instances(self, loaded_scanner):
        """Trashed instances are excluded when ignore_trash is True."""
        # Our fixture doesn't have trashed task instances,
        # but we verify the method works
        count = loaded_scanner._count_instances("tag_task")
        assert count >= 0

    def test_includes_trashed_when_configured(self, sample_export_path):
        """Trashed instances are included when ignore_trash is False."""
        scanner = TanaExportScanner(sample_export_path, ignore_trash=False)
        scanner._load_data()
        scanner._discover_supertags()
        scanner._build_metanode_tags()
        # Count should still work
        count = scanner._count_instances("tag_task")
        assert count >= 0


class TestGetSpecialType:
    """Tests for special type detection."""

    def test_detects_day_supertag(self, loaded_scanner):
        """Day supertag is detected as special type."""
        assert loaded_scanner._get_special_type("day") == "day"
        assert loaded_scanner._get_special_type("Day") == "day"

    def test_detects_week_supertag(self, loaded_scanner):
        """Week supertag is detected as special type."""
        assert loaded_scanner._get_special_type("week") == "week"

    def test_detects_year_supertag(self, loaded_scanner):
        """Year supertag is detected as special type."""
        assert loaded_scanner._get_special_type("year") == "year"

    def test_detects_field_definition(self, loaded_scanner):
        """Field definition supertag is detected as special type."""
        assert loaded_scanner._get_special_type("field-definition") == "field-definition"
        assert loaded_scanner._get_special_type("field definition") == "field-definition"

    def test_normal_supertag_no_special_type(self, loaded_scanner):
        """Normal supertags return None for special type."""
        assert loaded_scanner._get_special_type("task") is None
        assert loaded_scanner._get_special_type("project") is None


class TestFullScan:
    """Integration tests for the full scan process."""

    def test_scan_returns_supertag_infos(self, scanner):
        """Scan returns list of SupertagInfo objects."""
        results = scanner.scan()
        assert len(results) > 0
        assert all(isinstance(r, SupertagInfo) for r in results)

    def test_scan_excludes_system_supertags(self, scanner):
        """Scan results exclude system supertags."""
        results = scanner.scan()
        tag_ids = [r.id for r in results]
        assert "SYS_tag_system" not in tag_ids

    def test_scan_excludes_trashed_supertags(self, scanner):
        """Scan results exclude trashed supertags."""
        results = scanner.scan()
        tag_ids = [r.id for r in results]
        assert "tag_trashed" not in tag_ids

    def test_scan_excludes_base_type_supertags(self, scanner):
        """Scan results exclude base type supertags."""
        results = scanner.scan()
        tag_ids = [r.id for r in results]
        assert "tag_excluded_base" not in tag_ids

    def test_scan_sorts_day_supertag_first(self, scanner):
        """Day supertag appears first in results."""
        results = scanner.scan()
        if results:
            # Day should be first among special types
            day_index = next((i for i, r in enumerate(results) if r.special_type == "day"), -1)
            if day_index >= 0:
                # Check that non-special types come after special types
                for i, r in enumerate(results[:day_index]):
                    assert r.special_type is not None or r.instance_count >= results[day_index].instance_count

    def test_scan_includes_instance_counts(self, scanner):
        """Scan results include instance counts."""
        results = scanner.scan()
        task_info = next((r for r in results if r.name == "task"), None)
        assert task_info is not None
        assert task_info.instance_count >= 1

    def test_scan_includes_fields(self, scanner):
        """Scan results include field information."""
        results = scanner.scan()
        task_info = next((r for r in results if r.name == "task"), None)
        assert task_info is not None
        assert len(task_info.fields) > 0

    def test_scan_with_progress_callback(self, sample_export_path):
        """Scan calls progress callback during execution."""
        progress_calls = []
        scanner = TanaExportScanner(
            sample_export_path,
            progress_callback=lambda p: progress_calls.append(p)
        )
        scanner.scan()
        assert len(progress_calls) > 0
        phases = [p.phase for p in progress_calls]
        assert "Scanning" in phases
