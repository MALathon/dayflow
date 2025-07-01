"""Tests for daily summary generator."""

import shutil
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

from dayflow.core.daily_summary import DailySummaryGenerator
from dayflow.vault.config import VaultConfig
from dayflow.vault.connection import VaultConnection


class TestDailySummaryGenerator:
    """Test the daily summary generator."""

    @pytest.fixture
    def temp_vault(self):
        """Create a temporary vault for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_vault_connection(self, temp_vault):
        """Create a mock vault connection."""
        mock_config = Mock(spec=VaultConfig)
        mock_config.vault_path = temp_vault
        mock_config.get_location.return_value = temp_vault / "Daily Notes"

        connection = VaultConnection(mock_config)
        return connection

    @pytest.fixture
    def sample_events(self):
        """Create sample events for testing."""
        base_date = date(2024, 1, 15)
        return [
            {
                "subject": "Morning Standup",
                "start_time": datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
                "end_time": datetime(2024, 1, 15, 9, 30, tzinfo=timezone.utc),
                "location": "Conference Room A",
                "is_all_day": False,
                "attendees": [
                    {"name": "John Doe", "email": "john@example.com"},
                    {"name": "Jane Smith", "email": "jane@example.com"},
                ],
            },
            {
                "subject": "Budget Review",
                "start_time": datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
                "end_time": datetime(2024, 1, 15, 15, 30, tzinfo=timezone.utc),
                "is_online_meeting": True,
                "online_meeting_url": "https://teams.microsoft.com/meet/12345",
                "is_all_day": False,
            },
            {
                "subject": "Project Planning",
                "start_time": datetime(2024, 1, 15, 16, 0, tzinfo=timezone.utc),
                "end_time": datetime(2024, 1, 15, 17, 0, tzinfo=timezone.utc),
                "is_all_day": False,
                "attendees": [
                    {"name": "Alice Johnson"},
                    {"name": "Bob Wilson"},
                    {"name": "Carol Davis"},
                    {"name": "Dave Miller"},
                    {"name": "Eve Brown"},
                    {"name": "Frank Taylor"},  # More than 5 to test truncation
                ],
            },
        ]

    def test_generate_daily_summary_basic(self, mock_vault_connection, sample_events):
        """Test basic daily summary generation."""
        generator = DailySummaryGenerator(mock_vault_connection)
        summary_date = date(2024, 1, 15)

        # Generate summary
        result_path = generator.generate_daily_summary(summary_date, sample_events)

        assert result_path is not None
        assert result_path.name == "2024-01-15 Daily Summary.md"
        assert result_path.exists()

        # Check content
        content = result_path.read_text()

        # Check frontmatter
        assert "date: 2024-01-15" in content
        assert "type: daily-summary" in content
        assert "meetings_count: 3" in content

        # Check header
        assert "# 2024-01-15 - Daily Summary" in content
        assert "📅 3 meetings today" in content

        # Check meeting links
        assert "[[2024-01-15 Morning Standup]]" in content
        assert "[[2024-01-15 Budget Review]]" in content
        assert "[[2024-01-15 Project Planning]]" in content

    def test_generate_daily_summary_with_schedule(
        self, mock_vault_connection, sample_events
    ):
        """Test that schedule section is properly formatted."""
        generator = DailySummaryGenerator(mock_vault_connection)
        summary_date = date(2024, 1, 15)

        result_path = generator.generate_daily_summary(summary_date, sample_events)
        content = result_path.read_text()

        # Check schedule formatting
        assert "### Schedule" in content
        assert (
            "**09:00-09:30** | [[2024-01-15 Morning Standup]] | 📍 Conference Room A"
            in content
        )
        assert "**14:00-15:30** | [[2024-01-15 Budget Review]] | 💻 Online" in content
        assert "**16:00-17:00** | [[2024-01-15 Project Planning]]" in content

    def test_generate_daily_summary_with_attendees(
        self, mock_vault_connection, sample_events
    ):
        """Test attendee formatting and truncation."""
        generator = DailySummaryGenerator(mock_vault_connection)
        summary_date = date(2024, 1, 15)

        result_path = generator.generate_daily_summary(summary_date, sample_events)
        content = result_path.read_text()

        # Check attendees for morning standup
        assert "👥 [[John Doe]], [[Jane Smith]]" in content

        # Check attendee truncation for project planning
        assert (
            "[[Alice Johnson]], [[Bob Wilson]], [[Carol Davis]], [[Dave Miller]], [[Eve Brown]] +1 more"
            in content
        )

    def test_generate_daily_summary_time_grouping(
        self, mock_vault_connection, sample_events
    ):
        """Test morning/afternoon/evening grouping."""
        generator = DailySummaryGenerator(mock_vault_connection)
        summary_date = date(2024, 1, 15)

        result_path = generator.generate_daily_summary(summary_date, sample_events)
        content = result_path.read_text()

        # Check time groupings
        assert "🌅 **Morning** (1 meetings)" in content
        assert "09:00 - [[2024-01-15 Morning Standup]]" in content

        assert "☀️ **Afternoon** (2 meetings)" in content
        assert "14:00 - [[2024-01-15 Budget Review]]" in content
        assert "16:00 - [[2024-01-15 Project Planning]]" in content

    def test_generate_daily_summary_with_all_day_event(self, mock_vault_connection):
        """Test handling of all-day events."""
        events = [
            {
                "subject": "Company Holiday",
                "start_time": datetime(2024, 1, 15, 0, 0, tzinfo=timezone.utc),
                "end_time": datetime(2024, 1, 16, 0, 0, tzinfo=timezone.utc),
                "is_all_day": True,
            },
            {
                "subject": "Team Meeting",
                "start_time": datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
                "end_time": datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
                "is_all_day": False,
            },
        ]

        generator = DailySummaryGenerator(mock_vault_connection)
        result_path = generator.generate_daily_summary(date(2024, 1, 15), events)
        content = result_path.read_text()

        # All-day events should be listed first
        assert "### All Day" in content
        assert "- [[2024-01-15 Company Holiday]]" in content

        # Then timed events
        assert "### Schedule" in content
        assert "**10:00-11:00** | [[2024-01-15 Team Meeting]]" in content

    def test_generate_daily_summary_with_cancelled_event(self, mock_vault_connection):
        """Test handling of cancelled events."""
        events = [
            {
                "subject": "Cancelled Meeting",
                "start_time": datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
                "end_time": datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
                "is_cancelled": True,
                "is_all_day": False,
            },
            {
                "subject": "Active Meeting",
                "start_time": datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
                "end_time": datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
                "is_all_day": False,
            },
        ]

        generator = DailySummaryGenerator(mock_vault_connection)
        result_path = generator.generate_daily_summary(date(2024, 1, 15), events)
        content = result_path.read_text()

        # Cancelled events should be struck through
        assert "~~**10:00-11:00** | [[2024-01-15 Cancelled Meeting]]~~" in content

        # Cancelled events should not have action items
        assert "### [[2024-01-15 Cancelled Meeting]]" not in content
        assert "### [[2024-01-15 Active Meeting]]" in content

    def test_generate_daily_summary_action_items_section(
        self, mock_vault_connection, sample_events
    ):
        """Test action items summary section."""
        generator = DailySummaryGenerator(mock_vault_connection)
        result_path = generator.generate_daily_summary(date(2024, 1, 15), sample_events)
        content = result_path.read_text()

        # Check action items section
        assert "## Action Items Summary" in content
        assert "### [[2024-01-15 Morning Standup]]" in content
        assert "### [[2024-01-15 Budget Review]]" in content
        assert "### [[2024-01-15 Project Planning]]" in content
        assert "- [ ]" in content  # Empty checkbox for action items

    def test_generate_daily_summary_reflection_section(
        self, mock_vault_connection, sample_events
    ):
        """Test daily reflection section."""
        generator = DailySummaryGenerator(mock_vault_connection)
        result_path = generator.generate_daily_summary(date(2024, 1, 15), sample_events)
        content = result_path.read_text()

        # Check reflection section
        assert "## Daily Reflection" in content
        assert "### Key Accomplishments" in content
        assert "### Challenges" in content
        assert "### Tomorrow's Priorities" in content

    def test_generate_daily_summary_no_events(self, mock_vault_connection):
        """Test handling when no events exist."""
        generator = DailySummaryGenerator(mock_vault_connection)
        result = generator.generate_daily_summary(date(2024, 1, 15), [])

        assert result is None

    def test_update_daily_summaries_multiple_dates(self, mock_vault_connection):
        """Test updating summaries for multiple dates."""
        generator = DailySummaryGenerator(mock_vault_connection)

        # Create events for multiple dates
        events_by_date = {
            date(2024, 1, 15): [
                {
                    "subject": "Meeting 1",
                    "start_time": datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
                    "end_time": datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
                    "is_all_day": False,
                }
            ],
            date(2024, 1, 16): [
                {
                    "subject": "Meeting 2",
                    "start_time": datetime(2024, 1, 16, 14, 0, tzinfo=timezone.utc),
                    "end_time": datetime(2024, 1, 16, 15, 0, tzinfo=timezone.utc),
                    "is_all_day": False,
                }
            ],
            date(2024, 1, 17): [],  # No events this day
        }

        # Update summaries
        stats = generator.update_daily_summaries(events_by_date)

        assert stats["created"] == 2
        assert stats["updated"] == 0
        assert stats["total"] == 2

        # Check files were created
        daily_notes_path = mock_vault_connection.config.get_location("daily_notes")
        assert (daily_notes_path / "2024-01-15 Daily Summary.md").exists()
        assert (daily_notes_path / "2024-01-16 Daily Summary.md").exists()
        assert not (daily_notes_path / "2024-01-17 Daily Summary.md").exists()

    def test_update_daily_summaries_existing_file(self, mock_vault_connection):
        """Test updating existing daily summary."""
        generator = DailySummaryGenerator(mock_vault_connection)

        # Create an existing summary
        daily_notes_path = mock_vault_connection.config.get_location("daily_notes")
        daily_notes_path.mkdir(parents=True, exist_ok=True)
        existing_file = daily_notes_path / "2024-01-15 Daily Summary.md"
        existing_file.write_text("# Old content")

        # Update with new events
        events_by_date = {
            date(2024, 1, 15): [
                {
                    "subject": "Updated Meeting",
                    "start_time": datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
                    "end_time": datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
                    "is_all_day": False,
                }
            ]
        }

        stats = generator.update_daily_summaries(events_by_date)

        assert stats["created"] == 0
        assert stats["updated"] == 1
        assert stats["total"] == 1

        # Check content was updated
        new_content = existing_file.read_text()
        assert "Old content" not in new_content
        assert "[[2024-01-15 Updated Meeting]]" in new_content

    def test_evening_meetings(self, mock_vault_connection):
        """Test evening meeting categorization."""
        events = [
            {
                "subject": "Evening Review",
                "start_time": datetime(2024, 1, 15, 18, 0, tzinfo=timezone.utc),
                "end_time": datetime(2024, 1, 15, 19, 0, tzinfo=timezone.utc),
                "is_all_day": False,
            }
        ]

        generator = DailySummaryGenerator(mock_vault_connection)
        result_path = generator.generate_daily_summary(date(2024, 1, 15), events)
        content = result_path.read_text()

        assert "🌙 **Evening** (1 meetings)" in content
        assert "18:00 - [[2024-01-15 Evening Review]]" in content

    def test_generate_daily_summary_with_graph_api_attendees(
        self, mock_vault_connection
    ):
        """Test that daily summary correctly handles Graph API attendee structure."""
        # This is the actual structure returned by Graph API after normalization
        events = [
            {
                "subject": "Team Meeting",
                "start_time": datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
                "end_time": datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
                "location": "Conference Room A",
                "is_all_day": False,
                "attendees": [
                    {
                        "emailAddress": {
                            "name": "John Doe",
                            "address": "john@example.com",
                        },
                        "type": "required",
                    },
                    {
                        "emailAddress": {
                            "name": "Jane Smith",
                            "address": "jane@example.com",
                        },
                        "type": "optional",
                    },
                ],
            }
        ]

        generator = DailySummaryGenerator(mock_vault_connection)
        result_path = generator.generate_daily_summary(date(2024, 1, 15), events)
        content = result_path.read_text()

        # Check that names appear correctly, not "Unknown"
        assert "John Doe" in content
        assert "Jane Smith" in content
        assert "Unknown" not in content
        assert "👥 [[John Doe]], [[Jane Smith]]" in content

    def test_generate_daily_summary_with_mixed_attendee_formats(
        self, mock_vault_connection
    ):
        """Test handling of mixed attendee formats in the same event."""
        events = [
            {
                "subject": "Mixed Format Meeting",
                "start_time": datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
                "end_time": datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
                "is_all_day": False,
                "attendees": [
                    # Graph API format
                    {
                        "emailAddress": {
                            "name": "Graph User",
                            "address": "graph@example.com",
                        },
                        "type": "required",
                    },
                    # Simple format
                    {"name": "Simple User", "email": "simple@example.com"},
                    # Graph API with missing name
                    {"emailAddress": {"address": "noname@example.com"}},
                    # Malformed - no useful data
                    {"type": "optional"},
                ],
            }
        ]

        generator = DailySummaryGenerator(mock_vault_connection)
        result_path = generator.generate_daily_summary(date(2024, 1, 15), events)
        content = result_path.read_text()

        # Check all formats are handled
        assert "Graph User" in content
        assert "Simple User" in content
        assert "noname@example.com" in content  # Falls back to email
        assert "Unknown" in content  # For malformed attendee
        assert (
            "👥 [[Graph User]], [[Simple User]], [[noname@example.com]], [[Unknown]]"
            in content
        )
