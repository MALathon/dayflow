"""Integration test for the full sync pipeline."""

import shutil
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from dayflow.core.sync import CalendarSyncEngine
from dayflow.vault.config import VaultConfig
from dayflow.vault.connection import VaultConnection


class TestFullSyncPipeline:
    """Test the complete sync pipeline from Graph API to Obsidian notes."""

    @pytest.fixture
    def temp_vault(self):
        """Create a temporary vault for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_graph_response(self):
        """Mock Graph API response with realistic data."""
        return {
            "value": [
                {
                    "id": "event1",
                    "subject": "Team Standup",
                    "start": {"dateTime": "2024-01-15T09:00:00", "timeZone": "UTC"},
                    "end": {"dateTime": "2024-01-15T09:30:00", "timeZone": "UTC"},
                    "location": {
                        "displayName": "Conference Room A",
                        "address": {"street": "123 Main St"},
                    },
                    "attendees": [
                        {
                            "emailAddress": {
                                "name": "John Doe",
                                "address": "john.doe@example.com",
                            },
                            "type": "required",
                        },
                        {
                            "emailAddress": {
                                "name": "Jane Smith",
                                "address": "jane.smith@example.com",
                            },
                            "type": "optional",
                        },
                    ],
                    "body": {
                        "contentType": "html",
                        "content": "<p>Daily team sync to discuss progress and blockers.</p>",
                    },
                    "isOnlineMeeting": False,
                    "isAllDay": False,
                    "isCancelled": False,
                },
                {
                    "id": "event2",
                    "subject": "Project Review",
                    "start": {"dateTime": "2024-01-15T14:00:00", "timeZone": "UTC"},
                    "end": {"dateTime": "2024-01-15T15:30:00", "timeZone": "UTC"},
                    "attendees": [
                        {
                            "emailAddress": {
                                "name": "Alice Johnson",
                                "address": "alice@example.com",
                            },
                            "type": "required",
                        },
                        {
                            "emailAddress": {
                                # No name, just email
                                "address": "noreply@example.com"
                            },
                            "type": "optional",
                        },
                    ],
                    "body": {
                        "contentType": "html",
                        "content": """<html><body>
<p>Review project status and next steps.</p>
<p>&nbsp;</p>
<p>Agenda:</p>
<ul>
<li>Progress update</li>
<li>Risk assessment</li>
<li>Next milestones</li>
</ul>
</body></html>""",
                    },
                    "isOnlineMeeting": True,
                    "onlineMeeting": {
                        "joinUrl": "https://teams.microsoft.com/meet/123456"
                    },
                    "isAllDay": False,
                    "isCancelled": False,
                },
            ]
        }

    @patch("requests.get")
    def test_full_sync_pipeline(self, mock_get, temp_vault, mock_graph_response):
        """Test the complete sync pipeline."""
        # Set up mock response
        mock_response = Mock()
        mock_response.json.return_value = mock_graph_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Set up vault with mock config
        vault_config = Mock(spec=VaultConfig)
        vault_config.vault_path = temp_vault
        vault_config.get_location = Mock(
            side_effect=lambda key: {
                "meetings": temp_vault / "Meetings",
                "calendar_events": temp_vault / "Meetings",  # Same as meetings
                "daily_notes": temp_vault / "Daily Notes",
            }.get(key, temp_vault / key)
        )
        vault_config.get_setting = Mock(return_value=None)  # No folder organization

        vault_connection = VaultConnection(vault_config)

        # Create sync engine
        sync_engine = CalendarSyncEngine(
            access_token="mock-token",
            vault_connection=vault_connection,
            create_daily_summaries=True,
        )

        # Run sync
        result = sync_engine.sync(
            start_date=date(2024, 1, 15), end_date=date(2024, 1, 15)
        )

        # Check sync results
        assert result["notes_created"] == 2
        assert result["notes_updated"] == 0
        assert result["daily_summaries_created"] == 1
        assert result["daily_summaries_updated"] == 0

        # Check meeting notes were created
        meetings_dir = temp_vault / "Meetings"
        assert meetings_dir.exists()

        # Check first meeting note
        standup_note = meetings_dir / "2024-01-15 Team Standup.md"
        assert standup_note.exists()

        standup_content = standup_note.read_text()
        # Check attendees are properly formatted
        assert "John Doe" in standup_content
        assert "Jane Smith" in standup_content
        assert "Unknown" not in standup_content
        assert "- [[John Doe]]" in standup_content
        assert "- [[Jane Smith]]" in standup_content

        # Check location
        assert "Conference Room A" in standup_content

        # Check body was converted from HTML
        assert "Daily team sync to discuss progress and blockers." in standup_content
        assert "<p>" not in standup_content  # HTML should be removed

        # Check second meeting note
        review_note = meetings_dir / "2024-01-15 Project Review.md"
        assert review_note.exists()

        review_content = review_note.read_text()
        # Check attendees with missing name
        assert "Alice Johnson" in review_content
        assert "noreply@example.com" in review_content  # Falls back to email
        assert "- [[Alice Johnson]]" in review_content
        assert "- [[noreply@example.com]]" in review_content

        # Check HTML conversion with list
        assert "Review project status and next steps." in review_content
        assert "- Progress update" in review_content
        assert "- Risk assessment" in review_content
        assert "- Next milestones" in review_content
        assert "<ul>" not in review_content
        assert "&nbsp;" not in review_content

        # Check online meeting info
        assert (
            "online_meeting_url: https://teams.microsoft.com/meet/123456"
            in review_content
        )

        # Check daily summary was created
        daily_notes_dir = temp_vault / "Daily Notes"
        assert daily_notes_dir.exists()

        daily_summary = daily_notes_dir / "2024-01-15 Daily Summary.md"
        assert daily_summary.exists()

        summary_content = daily_summary.read_text()
        # Check summary content
        assert "2024-01-15 - Daily Summary" in summary_content
        assert "2 meetings today" in summary_content

        # Check meeting links
        assert "[[2024-01-15 Team Standup]]" in summary_content
        assert "[[2024-01-15 Project Review]]" in summary_content

        # Check attendees in summary
        assert "👥 [[John Doe]], [[Jane Smith]]" in summary_content
        assert "👥 [[Alice Johnson]], [[noreply@example.com]]" in summary_content

        # Check schedule section
        assert "09:00-09:30" in summary_content
        assert "14:00-15:30" in summary_content
        assert "Conference Room A" in summary_content
        assert "💻 Online" in summary_content

        # Check no "Unknown" attendees
        assert summary_content.count("Unknown") == 0
