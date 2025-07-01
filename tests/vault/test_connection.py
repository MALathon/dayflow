"""
Test cases for vault connection and file operations.
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from dayflow.vault.config import VaultConfig
from dayflow.vault.connection import VaultConnection


class TestVaultConnection:
    """Test vault connection functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.temp_dir) / "test_vault"
        self.vault_path.mkdir()

        # Create mock config
        self.mock_config = Mock(spec=VaultConfig)
        self.mock_config.vault_path = self.vault_path
        self.mock_config.get_location.side_effect = self._mock_get_location

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def _mock_get_location(self, location_type):
        """Mock location mapping."""
        locations = {
            "calendar_events": self.vault_path / "Meetings",
            "daily_notes": self.vault_path / "Daily Notes",
            "people": self.vault_path / "People",
        }
        return locations.get(location_type)

    def test_connection_initialization(self):
        """Test creating a vault connection."""
        conn = VaultConnection(self.mock_config)
        assert conn.vault_path == self.vault_path
        assert conn.config == self.mock_config

    def test_ensure_folder_exists_creates_new_folder(self):
        """Test that ensure_folder_exists creates folders."""
        conn = VaultConnection(self.mock_config)

        # Folder shouldn't exist yet
        meetings_folder = self.vault_path / "Meetings"
        assert not meetings_folder.exists()

        # Ensure it exists
        result = conn.ensure_folder_exists("calendar_events")

        # Should create the folder
        assert meetings_folder.exists()
        assert meetings_folder.is_dir()
        assert result == meetings_folder

    def test_ensure_folder_exists_with_nested_path(self):
        """Test creating nested folder structures."""
        # Mock a nested path
        self.mock_config.get_location.side_effect = lambda t: (
            self.vault_path / "1-Projects/Work/Meetings"
            if t == "calendar_events"
            else None
        )

        conn = VaultConnection(self.mock_config)
        result = conn.ensure_folder_exists("calendar_events")

        # Should create all parent directories
        assert result.exists()
        assert (self.vault_path / "1-Projects").exists()
        assert (self.vault_path / "1-Projects/Work").exists()

    def test_ensure_folder_exists_preserves_existing(self):
        """Test that existing folders are preserved."""
        conn = VaultConnection(self.mock_config)

        # Create folder manually
        meetings_folder = self.vault_path / "Meetings"
        meetings_folder.mkdir()
        test_file = meetings_folder / "existing.md"
        test_file.write_text("existing content")

        # Ensure folder exists
        result = conn.ensure_folder_exists("calendar_events")

        # Should not delete existing content
        assert test_file.exists()
        assert test_file.read_text() == "existing content"
        assert result == meetings_folder

    def test_write_note_basic(self):
        """Test writing a basic note."""
        conn = VaultConnection(self.mock_config)

        content = """---
date: 2024-01-15
type: meeting
---

# Team Standup

Meeting notes here."""

        # Write the note
        file_path = conn.write_note(content, "2024-01-15 Team Standup.md")

        # Check the note was written
        assert file_path.exists()
        assert file_path.name == "2024-01-15 Team Standup.md"
        assert file_path.read_text() == content

        # Check it's in the right location
        assert file_path.parent == self.vault_path / "Meetings"

    def test_write_note_custom_folder(self):
        """Test writing a note to a custom folder type."""
        conn = VaultConnection(self.mock_config)

        content = "# John Doe\n\nContact information"

        # Write to people folder
        file_path = conn.write_note(content, "John Doe.md", folder_type="people")

        # Check location
        assert file_path.parent == self.vault_path / "People"
        assert file_path.read_text() == content

    def test_write_note_overwrites_existing(self):
        """Test that writing a note overwrites existing files."""
        conn = VaultConnection(self.mock_config)

        # Write initial note
        conn.write_note("Original content", "test.md")

        # Overwrite with new content
        file_path = conn.write_note("New content", "test.md")

        # Should have new content
        assert file_path.read_text() == "New content"

    def test_write_note_handles_invalid_filenames(self):
        """Test handling of invalid filenames."""
        conn = VaultConnection(self.mock_config)

        # Try to write with invalid characters
        content = "Test content"

        # Should sanitize the filename
        file_path = conn.write_note(content, "Invalid/File:Name?.md")

        # Should have sanitized the name
        assert file_path.exists()
        assert "/" not in file_path.name
        assert ":" not in file_path.name
        assert "?" not in file_path.name

    def test_read_note(self):
        """Test reading an existing note."""
        conn = VaultConnection(self.mock_config)

        # Write a note first
        content = "# Test Note\n\nThis is content"
        conn.write_note(content, "test.md")

        # Read it back
        read_content = conn.read_note("test.md", folder_type="calendar_events")
        assert read_content == content

    def test_read_nonexistent_note_returns_none(self):
        """Test reading a note that doesn't exist."""
        conn = VaultConnection(self.mock_config)

        content = conn.read_note("nonexistent.md")
        assert content is None

    def test_list_notes_in_folder(self):
        """Test listing notes in a folder."""
        conn = VaultConnection(self.mock_config)

        # Create some notes
        conn.write_note("Content 1", "note1.md")
        conn.write_note("Content 2", "note2.md")
        conn.write_note("Content 3", "note3.md", folder_type="people")

        # List notes in calendar_events
        notes = conn.list_notes("calendar_events")
        assert len(notes) == 2
        assert any(n.name == "note1.md" for n in notes)
        assert any(n.name == "note2.md" for n in notes)

        # List notes in people folder
        people_notes = conn.list_notes("people")
        assert len(people_notes) == 1
        assert people_notes[0].name == "note3.md"

    def test_note_exists(self):
        """Test checking if a note exists."""
        conn = VaultConnection(self.mock_config)

        # Write a note
        conn.write_note("Content", "existing.md")

        # Check existence
        assert conn.note_exists("existing.md", folder_type="calendar_events")
        assert not conn.note_exists("nonexistent.md", folder_type="calendar_events")

    def test_get_note_path(self):
        """Test getting the full path for a note."""
        conn = VaultConnection(self.mock_config)

        # Get path for a note
        path = conn.get_note_path(
            "2024-01-15 Meeting.md", folder_type="calendar_events"
        )

        assert path == self.vault_path / "Meetings" / "2024-01-15 Meeting.md"

    def test_connection_with_unconfigured_location(self):
        """Test handling of unconfigured location types."""
        # Mock config that returns None for unknown types
        self.mock_config.get_location.side_effect = lambda t: None

        conn = VaultConnection(self.mock_config)

        # Should raise error when trying to use unconfigured location
        with pytest.raises(
            ValueError, match="Location type 'unknown_type' not configured"
        ):
            conn.ensure_folder_exists("unknown_type")
