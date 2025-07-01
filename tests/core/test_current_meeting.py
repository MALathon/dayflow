"""Tests for current meeting identification."""

import shutil
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from dayflow.core.current_meeting import CurrentMeetingManager
from dayflow.vault.config import VaultConfig
from dayflow.vault.connection import VaultConnection


class TestCurrentMeeting:
    """Test current meeting identification and management."""

    @pytest.fixture
    def temp_vault(self):
        """Create a temporary vault for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def vault_connection(self, temp_vault):
        """Create vault connection."""
        config = Mock(spec=VaultConfig)
        config.vault_path = temp_vault
        config.get_location = Mock(
            side_effect=lambda key: {
                "calendar_events": temp_vault / "Calendar",
                "home": temp_vault,
            }.get(key, temp_vault / key)
        )

        return VaultConnection(config)

    @pytest.fixture
    def sample_events(self):
        """Create sample events for testing."""
        now = datetime.now(timezone.utc)
        return [
            {
                "subject": "Past Meeting",
                "start_time": now - timedelta(hours=2),
                "end_time": now - timedelta(hours=1),
                "id": "past-meeting",
            },
            {
                "subject": "Current Meeting",
                "start_time": now - timedelta(minutes=15),
                "end_time": now + timedelta(minutes=45),
                "id": "current-meeting",
            },
            {
                "subject": "Upcoming Meeting",
                "start_time": now + timedelta(hours=1),
                "end_time": now + timedelta(hours=2),
                "id": "upcoming-meeting",
            },
            {
                "subject": "All Day Event",
                "start_time": now.replace(hour=0, minute=0, second=0, microsecond=0),
                "end_time": (now + timedelta(days=1)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                ),
                "is_all_day": True,
                "id": "all-day-event",
            },
        ]

    def test_identify_current_meeting(self, vault_connection, sample_events):
        """Test identifying the currently active meeting."""
        manager = CurrentMeetingManager(vault_connection)

        # Find current meeting
        current = manager.get_current_meeting(sample_events)

        assert current is not None
        assert current["subject"] == "Current Meeting"
        assert current["id"] == "current-meeting"

    def test_no_current_meeting(self, vault_connection):
        """Test when there's no current meeting."""
        manager = CurrentMeetingManager(vault_connection)

        now = datetime.now(timezone.utc)
        events = [
            {
                "subject": "Past Meeting",
                "start_time": now - timedelta(hours=2),
                "end_time": now - timedelta(hours=1),
            },
            {
                "subject": "Future Meeting",
                "start_time": now + timedelta(hours=2),
                "end_time": now + timedelta(hours=3),
            },
        ]

        current = manager.get_current_meeting(events)
        assert current is None

    def test_multiple_overlapping_meetings(self, vault_connection):
        """Test handling multiple meetings at current time."""
        manager = CurrentMeetingManager(vault_connection)

        now = datetime.now(timezone.utc)
        events = [
            {
                "subject": "Meeting A",
                "start_time": now - timedelta(minutes=30),
                "end_time": now + timedelta(minutes=30),
                "id": "meeting-a",
            },
            {
                "subject": "Meeting B",
                "start_time": now - timedelta(minutes=15),
                "end_time": now + timedelta(minutes=45),
                "id": "meeting-b",
            },
        ]

        # Should return the more recently started meeting
        current = manager.get_current_meeting(events)
        assert current["id"] == "meeting-b"

    def test_current_meeting_shortcut(self, vault_connection, sample_events):
        """Test creating/updating current meeting shortcut."""
        manager = CurrentMeetingManager(vault_connection)

        # Create current meeting shortcut
        current = sample_events[1]  # Current Meeting
        shortcut_path = manager.update_current_meeting_shortcut(current)

        assert shortcut_path.exists()
        assert shortcut_path.name == "Current Meeting.md"
        assert shortcut_path.parent == vault_connection.config.vault_path

        # Check content
        content = shortcut_path.read_text()
        assert "Current Meeting" in content
        assert "[[" in content  # Link to actual meeting note
        assert "Current Meeting]]" in content
        assert "⏰ NOW" in content  # Current indicator

    def test_clear_current_meeting_shortcut(self, vault_connection):
        """Test clearing current meeting shortcut when no meeting active."""
        manager = CurrentMeetingManager(vault_connection)

        # Create a dummy shortcut
        shortcut_path = vault_connection.config.vault_path / "Current Meeting.md"
        shortcut_path.write_text("Old meeting")

        # Clear when no current meeting
        manager.update_current_meeting_shortcut(None)

        # Should either not exist or have placeholder content
        if shortcut_path.exists():
            content = shortcut_path.read_text()
            assert "No meeting currently in progress" in content

    def test_next_meeting_info(self, vault_connection, sample_events):
        """Test getting next upcoming meeting info."""
        manager = CurrentMeetingManager(vault_connection)

        # Get next meeting
        next_meeting = manager.get_next_meeting(sample_events)

        assert next_meeting is not None
        assert next_meeting["subject"] == "Upcoming Meeting"
        assert next_meeting["id"] == "upcoming-meeting"

    def test_meeting_status_indicators(self, vault_connection):
        """Test generating meeting status indicators."""
        manager = CurrentMeetingManager(vault_connection)

        now = datetime.now(timezone.utc)

        # Past meeting
        past = {
            "start_time": now - timedelta(hours=2),
            "end_time": now - timedelta(hours=1),
        }
        assert manager.get_meeting_status(past) == "past"

        # Current meeting
        current = {
            "start_time": now - timedelta(minutes=15),
            "end_time": now + timedelta(minutes=45),
        }
        assert manager.get_meeting_status(current) == "current"

        # Upcoming meeting (within 15 minutes)
        soon = {
            "start_time": now + timedelta(minutes=10),
            "end_time": now + timedelta(minutes=70),
        }
        assert manager.get_meeting_status(soon) == "soon"

        # Future meeting
        future = {
            "start_time": now + timedelta(hours=2),
            "end_time": now + timedelta(hours=3),
        }
        assert manager.get_meeting_status(future) == "future"

    def test_daily_summary_with_current_meeting(self, vault_connection, sample_events):
        """Test daily summary highlighting current meeting."""
        from dayflow.core.daily_summary import DailySummaryGenerator

        generator = DailySummaryGenerator(vault_connection)
        manager = CurrentMeetingManager(vault_connection)

        # Set current meeting context
        current = manager.get_current_meeting(sample_events)

        # Generate daily summary with current meeting highlighted
        summary_date = date.today()
        summary_path = generator.generate_daily_summary(
            summary_date, sample_events, current_meeting=current
        )

        content = summary_path.read_text()

        # Current meeting should be highlighted
        assert "⏰ **NOW**" in content
        assert "Current Meeting" in content

    def test_home_page_current_meeting_widget(self, vault_connection, sample_events):
        """Test home page widget for current meeting."""
        manager = CurrentMeetingManager(vault_connection)

        # Generate widget content
        widget = manager.generate_home_widget(sample_events)

        assert "## 📅 Current Meeting" in widget
        assert "[[Current Meeting]]" in widget
        assert "Started 15 minutes ago" in widget
        assert "minutes remaining" in widget  # Don't check exact time due to timing

        # Also shows next meeting
        assert "### 🔜 Next Meeting" in widget
        assert "Upcoming Meeting" in widget
        assert "in " in widget  # Shows time until next meeting

    @patch("dayflow.core.current_meeting.datetime")
    def test_meeting_transition_handling(self, mock_datetime, vault_connection):
        """Test handling transition between meetings."""
        manager = CurrentMeetingManager(vault_connection)

        # Set initial time - during first meeting
        initial_time = datetime(2024, 3, 15, 10, 30, tzinfo=timezone.utc)
        mock_datetime.now.return_value = initial_time

        meetings = [
            {
                "subject": "Morning Meeting",
                "start_time": datetime(2024, 3, 15, 10, 0, tzinfo=timezone.utc),
                "end_time": datetime(2024, 3, 15, 11, 0, tzinfo=timezone.utc),
                "id": "morning",
            },
            {
                "subject": "Afternoon Meeting",
                "start_time": datetime(2024, 3, 15, 11, 0, tzinfo=timezone.utc),
                "end_time": datetime(2024, 3, 15, 12, 0, tzinfo=timezone.utc),
                "id": "afternoon",
            },
        ]

        # First check - morning meeting is current
        current = manager.get_current_meeting(meetings)
        assert current["id"] == "morning"

        # Time passes - now in afternoon meeting
        mock_datetime.now.return_value = datetime(
            2024, 3, 15, 11, 30, tzinfo=timezone.utc
        )

        current = manager.get_current_meeting(meetings)
        assert current["id"] == "afternoon"
