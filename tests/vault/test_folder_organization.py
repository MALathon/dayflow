"""Tests for year/month/day folder organization of calendar events."""

import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

import pytest

from dayflow.core.obsidian_formatter import ObsidianNoteFormatter
from dayflow.vault.config import VaultConfig
from dayflow.vault.connection import VaultConnection


class TestFolderOrganization:
    """Test organizing calendar events into year/month/day folders."""

    @pytest.fixture
    def temp_vault(self):
        """Create a temporary vault for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def vault_connection(self, temp_vault):
        """Create vault connection with folder organization enabled."""
        config = Mock(spec=VaultConfig)
        config.vault_path = temp_vault
        config.get_location.return_value = temp_vault / "Calendar"
        config.get_setting = Mock(
            side_effect=lambda key, default=None: {
                "calendar.folder_organization": "year/month/day",
                "calendar.time_prefix": True,
            }.get(key, default)
        )

        return VaultConnection(config)

    def test_year_month_day_folder_structure(self, vault_connection):
        """Test that notes are organized into year/month/day folders."""
        # Create test event
        event = {
            "subject": "Team Meeting",
            "start_time": datetime(2024, 3, 15, 10, 0, tzinfo=timezone.utc),
            "end_time": datetime(2024, 3, 15, 11, 0, tzinfo=timezone.utc),
        }

        formatter = ObsidianNoteFormatter()
        filename = formatter.generate_filename(event)
        content = formatter.format_event(event)

        # Write note with folder organization
        note_path = vault_connection.write_note(
            content, filename, "calendar_events", date_folder=event["start_time"].date()
        )

        # Check folder structure
        assert note_path.exists()
        assert "2024" in str(note_path)
        assert "03" in str(note_path)  # Month should be zero-padded
        assert "15" in str(note_path)  # Day should be zero-padded

        # Check exact path structure
        expected_path = (
            vault_connection.config.vault_path
            / "Calendar"
            / "2024"
            / "03"
            / "15"
            / filename
        )
        assert note_path == expected_path

    def test_time_prefixed_filenames(self, vault_connection):
        """Test that filenames include time prefix for ordering."""
        formatter = ObsidianNoteFormatter(use_time_prefix=True)

        # Test morning meeting
        event1 = {
            "subject": "Morning Standup",
            "start_time": datetime(2024, 3, 15, 9, 30, tzinfo=timezone.utc),
            "end_time": datetime(2024, 3, 15, 10, 0, tzinfo=timezone.utc),
        }

        filename1 = formatter.generate_filename(event1)
        assert filename1 == "0930 - Morning Standup.md"

        # Test afternoon meeting
        event2 = {
            "subject": "Afternoon Review",
            "start_time": datetime(2024, 3, 15, 14, 15, tzinfo=timezone.utc),
            "end_time": datetime(2024, 3, 15, 15, 0, tzinfo=timezone.utc),
        }

        filename2 = formatter.generate_filename(event2)
        assert filename2 == "1415 - Afternoon Review.md"

        # Verify sort order
        assert filename1 < filename2

    def test_all_day_events_sorting(self, vault_connection):
        """Test that all-day events sort before timed events."""
        formatter = ObsidianNoteFormatter(use_time_prefix=True)

        # All-day event
        all_day = {
            "subject": "Company Holiday",
            "start_time": datetime(2024, 3, 15, 0, 0, tzinfo=timezone.utc),
            "end_time": datetime(2024, 3, 16, 0, 0, tzinfo=timezone.utc),
            "is_all_day": True,
        }

        # Morning meeting
        morning = {
            "subject": "Morning Meeting",
            "start_time": datetime(2024, 3, 15, 9, 0, tzinfo=timezone.utc),
            "end_time": datetime(2024, 3, 15, 10, 0, tzinfo=timezone.utc),
        }

        all_day_name = formatter.generate_filename(all_day)
        morning_name = formatter.generate_filename(morning)

        # All-day events should use "0000" prefix to sort first
        assert all_day_name == "0000 - Company Holiday.md"
        assert morning_name == "0900 - Morning Meeting.md"
        assert all_day_name < morning_name

    def test_multiple_events_same_time(self, vault_connection):
        """Test handling of multiple events at the same time."""
        formatter = ObsidianNoteFormatter(use_time_prefix=True)

        # Two meetings at 10:00
        event1 = {
            "subject": "Project A Review",
            "start_time": datetime(2024, 3, 15, 10, 0, tzinfo=timezone.utc),
            "end_time": datetime(2024, 3, 15, 11, 0, tzinfo=timezone.utc),
        }

        event2 = {
            "subject": "Project B Review",
            "start_time": datetime(2024, 3, 15, 10, 0, tzinfo=timezone.utc),
            "end_time": datetime(2024, 3, 15, 11, 0, tzinfo=timezone.utc),
        }

        filename1 = formatter.generate_filename(event1)
        filename2 = formatter.generate_filename(event2)

        # Both should have same time prefix
        assert filename1 == "1000 - Project A Review.md"
        assert filename2 == "1000 - Project B Review.md"

        # Different filenames despite same time
        assert filename1 != filename2

    def test_folder_organization_disabled(self, temp_vault):
        """Test flat structure when folder organization is disabled."""
        config = Mock(spec=VaultConfig)
        config.vault_path = temp_vault
        config.get_location.return_value = temp_vault / "Calendar"
        config.get_setting = Mock(return_value=None)  # No folder organization

        vault_connection = VaultConnection(config)

        event = {
            "subject": "Team Meeting",
            "start_time": datetime(2024, 3, 15, 10, 0, tzinfo=timezone.utc),
            "end_time": datetime(2024, 3, 15, 11, 0, tzinfo=timezone.utc),
        }

        formatter = ObsidianNoteFormatter()
        filename = formatter.generate_filename(event)
        content = formatter.format_event(event)

        # Write note without folder organization
        note_path = vault_connection.write_note(content, filename, "calendar_events")

        # Should be directly in Calendar folder
        expected_path = temp_vault / "Calendar" / filename
        assert note_path == expected_path
        assert "2024" not in str(note_path.parent)

    def test_custom_folder_pattern(self, temp_vault):
        """Test custom folder organization patterns."""
        config = Mock(spec=VaultConfig)
        config.vault_path = temp_vault
        config.get_location.return_value = temp_vault / "Calendar"
        config.get_setting = Mock(
            side_effect=lambda key, default=None: {
                "calendar.folder_organization": "year/week"  # Weekly folders
            }.get(key, default)
        )

        vault_connection = VaultConnection(config)

        event = {
            "subject": "Weekly Review",
            "start_time": datetime(
                2024, 3, 15, 10, 0, tzinfo=timezone.utc
            ),  # Week 11 of 2024
            "end_time": datetime(2024, 3, 15, 11, 0, tzinfo=timezone.utc),
        }

        formatter = ObsidianNoteFormatter()
        filename = formatter.generate_filename(event)
        content = formatter.format_event(event)

        note_path = vault_connection.write_note(
            content, filename, "calendar_events", date_folder=event["start_time"].date()
        )

        # Should be in year/week folder
        assert "2024" in str(note_path)
        assert "W11" in str(note_path)  # Week 11
