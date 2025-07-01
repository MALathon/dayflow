"""Integration tests for sync with folder organization."""

import shutil
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from dayflow.core.sync import CalendarSyncEngine
from dayflow.vault.config import VaultConfig
from dayflow.vault.connection import VaultConnection


class TestSyncWithFolders:
    """Test sync engine with folder organization features."""

    @pytest.fixture
    def temp_vault(self):
        """Create a temporary vault for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def vault_config(self, temp_vault):
        """Create vault config with folder organization."""
        config = VaultConfig()

        # Set up locations
        config.config = {
            "vault": {
                "path": str(temp_vault),
                "locations": {
                    "calendar_events": "Calendar",
                    "daily_notes": "Daily Notes",
                },
            },
            "calendar": {
                "folder_organization": "year/month/day",
            },
        }

        return config

    @pytest.fixture
    def vault_connection(self, vault_config):
        """Create vault connection."""
        return VaultConnection(vault_config)

    @pytest.fixture
    def mock_graph_events(self):
        """Create mock calendar events."""
        # Use a fixed base date for consistent testing
        base_dt = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

        return [
            {
                "id": "event1",
                "subject": "Morning Standup",
                "start_time": base_dt.replace(
                    hour=9, minute=0, second=0, microsecond=0
                ),
                "end_time": base_dt.replace(hour=9, minute=30, second=0, microsecond=0),
                "attendees": [
                    {
                        "emailAddress": {
                            "name": "John Doe",
                            "address": "john@example.com",
                        }
                    }
                ],
                "location": "Conference Room A",
                "is_online_meeting": False,
            },
            {
                "id": "event2",
                "subject": "Current Project Review",
                "start_time": base_dt.replace(
                    hour=11, minute=45, second=0, microsecond=0
                ),
                "end_time": base_dt.replace(
                    hour=12, minute=45, second=0, microsecond=0
                ),
                "attendees": [
                    {
                        "emailAddress": {
                            "name": "Jane Smith",
                            "address": "jane@example.com",
                        }
                    }
                ],
                "is_online_meeting": True,
                "online_meeting_url": "https://teams.microsoft.com/meeting/123",
            },
            {
                "id": "event3",
                "subject": "Afternoon Workshop",
                "start_time": base_dt.replace(
                    hour=14, minute=0, second=0, microsecond=0
                ),
                "end_time": base_dt.replace(hour=16, minute=0, second=0, microsecond=0),
                "location": "Training Room",
                "is_online_meeting": False,
            },
            {
                "id": "event4",
                "subject": "Tomorrow Planning",
                "start_time": (base_dt + timedelta(days=1)).replace(
                    hour=10, minute=0, second=0, microsecond=0
                ),
                "end_time": (base_dt + timedelta(days=1)).replace(
                    hour=11, minute=0, second=0, microsecond=0
                ),
                "is_online_meeting": False,
            },
        ]

    @patch("dayflow.core.sync.GraphAPIClient")
    def test_sync_creates_folder_structure(
        self, mock_graph_client, vault_connection, mock_graph_events
    ):
        """Test that sync creates year/month/day folder structure."""
        # Mock Graph API to return events
        mock_client_instance = Mock()
        mock_graph_client.return_value = mock_client_instance
        mock_client_instance.fetch_calendar_events.return_value = mock_graph_events

        # Create sync engine
        engine = CalendarSyncEngine("fake-token", vault_connection)

        # Run sync
        results = engine.sync()
        assert results["notes_created"] > 0

        # Verify folder structure was created
        expected_folder = (
            vault_connection.config.vault_path / "Calendar" / "2025" / "01" / "15"
        )

        assert expected_folder.exists()
        assert expected_folder.is_dir()

        # Check tomorrow's folder too
        tomorrow_folder = (
            vault_connection.config.vault_path / "Calendar" / "2025" / "01" / "16"
        )

        assert tomorrow_folder.exists()

    @patch("dayflow.core.sync.GraphAPIClient")
    def test_time_prefixed_filenames(
        self, mock_graph_client, vault_connection, mock_graph_events
    ):
        """Test that files are created with time prefixes."""
        # Mock Graph API
        mock_client_instance = Mock()
        mock_graph_client.return_value = mock_client_instance
        mock_client_instance.fetch_calendar_events.return_value = mock_graph_events

        # Create sync engine
        engine = CalendarSyncEngine("fake-token", vault_connection)

        # Run sync
        results = engine.sync()
        assert results["notes_created"] > 0

        # Check files were created with time prefixes
        today_folder = (
            vault_connection.config.vault_path / "Calendar" / "2025" / "01" / "15"
        )

        files = list(today_folder.glob("*.md"))
        assert len(files) == 3  # Three events today

        # Check file naming
        filenames = sorted([f.name for f in files])
        assert filenames[0].startswith("0900 - ")  # Morning Standup
        assert "Morning Standup" in filenames[0]
        assert filenames[1].startswith("1145 - ")  # Current Project Review
        assert filenames[2].startswith("1400 - ")  # Afternoon Workshop

    @patch("dayflow.core.sync.GraphAPIClient")
    @patch("dayflow.core.current_meeting.datetime")
    def test_current_meeting_shortcut(
        self, mock_datetime, mock_graph_client, vault_connection, mock_graph_events
    ):
        """Test that current meeting shortcut is created."""
        # Mock current time to be during the "Current Project Review" meeting
        mock_now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now

        # Mock Graph API
        mock_client_instance = Mock()
        mock_graph_client.return_value = mock_client_instance
        mock_client_instance.fetch_calendar_events.return_value = mock_graph_events

        # Create sync engine
        engine = CalendarSyncEngine("fake-token", vault_connection)

        # Run sync
        results = engine.sync()
        assert results["notes_created"] > 0

        # Check current meeting shortcut exists
        shortcut_path = vault_connection.config.vault_path / "Current Meeting.md"
        assert shortcut_path.exists()

        # Check content
        content = shortcut_path.read_text(encoding="utf-8")
        assert "Current Project Review" in content
        assert "⏰ NOW" in content
        assert "[[" in content  # Has wiki link

    @patch("dayflow.core.sync.GraphAPIClient")
    @patch("dayflow.core.current_meeting.datetime")
    def test_daily_summary_with_current_highlight(
        self, mock_datetime, mock_graph_client, vault_connection, mock_graph_events
    ):
        """Test that daily summary highlights current meeting."""
        # Mock current time to be during the "Current Project Review" meeting
        mock_now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now

        # Mock Graph API
        mock_client_instance = Mock()
        mock_graph_client.return_value = mock_client_instance
        mock_client_instance.fetch_calendar_events.return_value = mock_graph_events

        # Create sync engine
        engine = CalendarSyncEngine("fake-token", vault_connection)

        # Run sync
        results = engine.sync()
        assert results["notes_created"] > 0

        # Check daily summary
        event_date = date(2025, 1, 15)
        summary_path = (
            vault_connection.config.vault_path
            / "Daily Notes"
            / f"{event_date.strftime('%Y-%m-%d')} Daily Summary.md"
        )

        assert summary_path.exists()

        content = summary_path.read_text(encoding="utf-8")
        assert "⏰ **NOW**" in content
        assert "Current Project Review" in content

    @patch("dayflow.core.sync.GraphAPIClient")
    def test_no_folder_org_uses_flat_structure(
        self, mock_graph_client, temp_vault, mock_graph_events
    ):
        """Test that without folder organization, flat structure is used."""
        # Create config without folder organization
        config = VaultConfig()
        config.config = {
            "vault": {
                "path": str(temp_vault),
                "locations": {
                    "calendar_events": "Calendar",
                    "daily_notes": "Daily Notes",
                },
            }
            # No calendar.folder_organization setting
        }

        vault_connection = VaultConnection(config)

        # Mock Graph API
        mock_client_instance = Mock()
        mock_graph_client.return_value = mock_client_instance
        mock_client_instance.fetch_calendar_events.return_value = mock_graph_events

        # Create sync engine
        engine = CalendarSyncEngine("fake-token", vault_connection)

        # Run sync
        results = engine.sync()
        assert results["notes_created"] > 0

        # Check flat structure with date prefix in filename
        calendar_folder = temp_vault / "Calendar"
        files = list(calendar_folder.glob("*.md"))

        # Files should be directly in Calendar folder
        assert len(files) == 4

        # Check date-prefixed naming
        event_date = date(2025, 1, 15)
        for f in files:
            if "Morning Standup" in f.name:
                assert f.name.startswith(event_date.strftime("%Y-%m-%d"))
                assert not f.name.startswith("0900")  # No time prefix in flat mode
