"""Tests for sync engine and vault connection integration."""

import shutil
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from dayflow.core.sync import CalendarSyncEngine
from dayflow.vault.config import VaultConfig
from dayflow.vault.connection import VaultConnection


class TestSyncVaultIntegration:
    """Test integration between sync engine and vault."""

    @pytest.fixture
    def temp_vault(self):
        """Create a temporary vault for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_config(self, temp_vault):
        """Create a mock config with temp vault."""
        config = Mock(spec=VaultConfig)
        config.vault_path = Path(temp_vault)
        config.get_location.return_value = Path(temp_vault) / "Calendar Events"
        config.get_setting = Mock(return_value=None)  # No folder organization
        return config

    @pytest.fixture
    def vault_connection(self, mock_config):
        """Create vault connection with mock config."""
        return VaultConnection(mock_config)

    @pytest.fixture
    def mock_graph_events(self):
        """Sample calendar events from Graph API."""
        return [
            {
                "subject": "Team Standup",
                "start_time": datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
                "end_time": datetime(2024, 1, 15, 9, 30, tzinfo=timezone.utc),
                "is_all_day": False,
                "location": "Conference Room A",
                "attendees": [
                    {"name": "John Doe", "email": "john@example.com"},
                    {"name": "Jane Smith", "email": "jane@example.com"},
                ],
            },
            {
                "subject": "Project Review",
                "start_time": datetime(2024, 1, 16, 14, 0, tzinfo=timezone.utc),
                "end_time": datetime(2024, 1, 16, 15, 30, tzinfo=timezone.utc),
                "is_all_day": False,
                "body": "Please review the attached documents before the meeting.",
                "is_online_meeting": True,
                "online_meeting_url": "https://teams.microsoft.com/meet/12345",
            },
        ]

    @patch("dayflow.core.sync.GraphAPIClient")
    def test_sync_creates_notes_in_vault(
        self, mock_graph_client, vault_connection, mock_graph_events
    ):
        """Test that sync creates notes in the vault."""
        # Setup mock
        mock_client_instance = mock_graph_client.return_value
        mock_client_instance.fetch_calendar_events.return_value = mock_graph_events

        # Create sync engine with vault connection
        engine = CalendarSyncEngine("fake_token")
        engine.vault_connection = vault_connection

        # Perform sync
        result = engine.sync()

        # Check results
        assert result["events_synced"] == 2
        assert result["notes_created"] == 2
        assert result["notes_updated"] == 0
        assert (
            result["daily_summaries_created"] > 0
        )  # Should create at least one daily summary

        # Check files were created
        calendar_folder = vault_connection.config.get_location("calendar_events")
        assert calendar_folder.exists()

        files = list(calendar_folder.glob("*.md"))
        assert len(files) == 2

        # Check file contents
        file_names = [f.name for f in files]
        assert "2024-01-15 Team Standup.md" in file_names
        assert "2024-01-16 Project Review.md" in file_names

    @patch("dayflow.core.sync.GraphAPIClient")
    def test_sync_updates_existing_notes(
        self, mock_graph_client, vault_connection, mock_graph_events
    ):
        """Test that sync updates existing notes instead of creating duplicates."""
        # Create an existing note
        calendar_folder = vault_connection.config.get_location("calendar_events")
        calendar_folder.mkdir(parents=True, exist_ok=True)
        existing_file = calendar_folder / "2024-01-15 Team Standup.md"
        existing_file.write_text("# Old content", encoding="utf-8")

        # Setup mock
        mock_client_instance = mock_graph_client.return_value
        mock_client_instance.fetch_calendar_events.return_value = mock_graph_events

        # Create sync engine with vault connection
        engine = CalendarSyncEngine("fake_token")
        engine.vault_connection = vault_connection

        # Perform sync
        result = engine.sync()

        # Check results
        assert result["events_synced"] == 2
        assert result["notes_created"] == 1  # Only one new note
        assert result["notes_updated"] == 1  # One updated

        # Check content was updated
        content = existing_file.read_text(encoding="utf-8")
        assert "# Team Standup" in content
        assert "Old content" not in content

    @patch("dayflow.core.sync.GraphAPIClient")
    def test_sync_handles_cancelled_events(self, mock_graph_client, vault_connection):
        """Test that sync handles cancelled events properly."""
        events = [
            {
                "subject": "Cancelled Meeting",
                "start_time": datetime(2024, 1, 20, 10, 0, tzinfo=timezone.utc),
                "end_time": datetime(2024, 1, 20, 11, 0, tzinfo=timezone.utc),
                "is_cancelled": True,
                "is_all_day": False,
            }
        ]

        # Setup mock
        mock_client_instance = mock_graph_client.return_value
        mock_client_instance.fetch_calendar_events.return_value = events

        # Create sync engine with vault connection
        engine = CalendarSyncEngine("fake_token")
        engine.vault_connection = vault_connection

        # Perform sync - should filter out cancelled events
        result = engine.sync()

        assert result["events_synced"] == 0  # Cancelled event filtered out
        assert result["notes_created"] == 0

    @patch("dayflow.core.sync.GraphAPIClient")
    def test_sync_with_date_range(
        self, mock_graph_client, vault_connection, mock_graph_events
    ):
        """Test sync with specific date range."""
        # Setup mock
        mock_client_instance = mock_graph_client.return_value
        mock_client_instance.fetch_calendar_events.return_value = mock_graph_events

        # Create sync engine with vault connection
        engine = CalendarSyncEngine("fake_token")
        engine.vault_connection = vault_connection

        # Sync with specific dates
        start = date(2024, 1, 15)
        end = date(2024, 1, 20)
        result = engine.sync(start_date=start, end_date=end)

        # Verify date range was passed
        mock_client_instance.fetch_calendar_events.assert_called_once_with(start, end)
        assert result["events_synced"] == 2

    @patch("dayflow.core.sync.GraphAPIClient")
    def test_sync_error_handling(self, mock_graph_client, vault_connection):
        """Test sync handles errors gracefully."""
        # Setup mock to raise error
        mock_client_instance = mock_graph_client.return_value
        mock_client_instance.fetch_calendar_events.side_effect = Exception(
            "Network error"
        )

        # Create sync engine with vault connection
        engine = CalendarSyncEngine("fake_token")
        engine.vault_connection = vault_connection

        # Sync should raise the exception
        with pytest.raises(Exception, match="Network error"):
            engine.sync()

    def test_sync_without_vault_connection(self):
        """Test sync without vault connection still returns events."""
        with patch("dayflow.core.sync.GraphAPIClient") as mock_graph_client:
            mock_client_instance = mock_graph_client.return_value
            mock_client_instance.fetch_calendar_events.return_value = [
                {
                    "subject": "Test Event",
                    "start_time": datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
                    "end_time": datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
                    "is_all_day": False,
                }
            ]

            # Create sync engine without vault connection
            engine = CalendarSyncEngine("fake_token")

            # Should still work but not create notes
            result = engine.sync()

            assert result["events_synced"] == 1
            assert result["notes_created"] == 0
            assert result["notes_updated"] == 0

    @patch("dayflow.core.sync.GraphAPIClient")
    def test_sync_without_daily_summaries(
        self, mock_graph_client, vault_connection, mock_graph_events
    ):
        """Test sync with daily summaries disabled."""
        # Setup mock
        mock_client_instance = mock_graph_client.return_value
        mock_client_instance.fetch_calendar_events.return_value = mock_graph_events

        # Create sync engine with daily summaries disabled
        engine = CalendarSyncEngine(
            "fake_token", vault_connection, create_daily_summaries=False
        )

        # Perform sync
        result = engine.sync()

        # Check results
        assert result["events_synced"] == 2
        assert result["notes_created"] == 2
        assert result["daily_summaries_created"] == 0
        assert result["daily_summaries_updated"] == 0
