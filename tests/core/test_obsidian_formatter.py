"""Tests for Obsidian note formatter."""

from datetime import datetime, timezone

from dayflow.core.obsidian_formatter import ObsidianNoteFormatter


class TestObsidianNoteFormatter:
    """Test the Obsidian note formatter."""

    def test_format_simple_event(self):
        """Test formatting a simple calendar event."""
        event = {
            "subject": "Team Meeting",
            "start_time": datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            "end_time": datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
            "is_all_day": False,
        }

        formatter = ObsidianNoteFormatter()
        content = formatter.format_event(event)

        # Check frontmatter
        assert content.startswith("---\n")
        assert "title: Team Meeting" in content
        assert "date: 2024-01-15" in content
        assert "start_time: 2024-01-15T14:00:00+00:00" in content
        assert "end_time: 2024-01-15T15:00:00+00:00" in content
        assert "type: meeting" in content
        assert "tags: [calendar-sync]" in content

        # Check content
        assert "# Team Meeting" in content
        assert "**Date**: 2024-01-15" in content
        assert "**Time**: 14:00 - 15:00 UTC" in content

    def test_format_event_with_location(self):
        """Test formatting event with location."""
        event = {
            "subject": "Client Presentation",
            "start_time": datetime(2024, 1, 20, 10, 0, tzinfo=timezone.utc),
            "end_time": datetime(2024, 1, 20, 11, 30, tzinfo=timezone.utc),
            "location": "Conference Room A",
            "is_all_day": False,
        }

        formatter = ObsidianNoteFormatter()
        content = formatter.format_event(event)

        assert "location: Conference Room A" in content
        assert "**Location**: Conference Room A" in content

    def test_format_event_with_attendees(self):
        """Test formatting event with attendees."""
        event = {
            "subject": "Project Review",
            "start_time": datetime(2024, 1, 22, 15, 0, tzinfo=timezone.utc),
            "end_time": datetime(2024, 1, 22, 16, 0, tzinfo=timezone.utc),
            "attendees": [
                {"name": "John Doe", "email": "john@example.com"},
                {"name": "Jane Smith", "email": "jane@example.com"},
            ],
            "is_all_day": False,
        }

        formatter = ObsidianNoteFormatter()
        content = formatter.format_event(event)

        assert "## Attendees" in content
        assert "- [[John Doe]]" in content
        assert "- [[Jane Smith]]" in content

    def test_format_event_with_graph_api_attendees(self):
        """Test formatting event with attendees in Graph API structure.

        This test ensures attendee names are extracted correctly and don't show as 'Unknown'.
        """
        event = {
            "subject": "Team Meeting",
            "start_time": datetime(2024, 1, 22, 15, 0, tzinfo=timezone.utc),
            "end_time": datetime(2024, 1, 22, 16, 0, tzinfo=timezone.utc),
            "attendees": [
                {
                    "type": "required",
                    "status": {"response": "accepted"},
                    "emailAddress": {
                        "name": "John Doe",
                        "address": "john.doe@mayo.edu",
                    },
                },
                {
                    "type": "optional",
                    "status": {"response": "tentative"},
                    "emailAddress": {
                        "name": "Jane Smith",
                        "address": "jane.smith@mayo.edu",
                    },
                },
                {
                    "type": "required",
                    "emailAddress": {
                        # No name, only email address
                        "address": "noname@mayo.edu"
                    },
                },
            ],
            "is_all_day": False,
        }

        formatter = ObsidianNoteFormatter()
        content = formatter.format_event(event)

        # Names should be extracted correctly
        assert "## Attendees" in content
        assert "- [[John Doe]]" in content
        assert "- [[Jane Smith]]" in content
        # For attendee without name, should use email
        assert "- [[noname@mayo.edu]]" in content
        # Should NOT contain "Unknown"
        assert "[[Unknown]]" not in content

    def test_format_all_day_event(self):
        """Test formatting all-day event."""
        event = {
            "subject": "Company Holiday",
            "start_time": datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc),
            "end_time": datetime(2024, 1, 2, 0, 0, tzinfo=timezone.utc),
            "is_all_day": True,
        }

        formatter = ObsidianNoteFormatter()
        content = formatter.format_event(event)

        assert "is_all_day: true" in content
        assert "**Time**: All day" in content

    def test_format_event_with_body(self):
        """Test formatting event with body content."""
        event = {
            "subject": "Strategy Session",
            "start_time": datetime(2024, 1, 25, 13, 0, tzinfo=timezone.utc),
            "end_time": datetime(2024, 1, 25, 15, 0, tzinfo=timezone.utc),
            "body": "Please review the attached documents before the meeting.\n\nAgenda:\n1. Q1 Goals\n2. Budget Review",
            "is_all_day": False,
        }

        formatter = ObsidianNoteFormatter()
        content = formatter.format_event(event)

        assert "## Description" in content
        assert "Please review the attached documents" in content
        assert "1. Q1 Goals" in content

    def test_format_recurring_event(self):
        """Test formatting recurring event."""
        event = {
            "subject": "Weekly Standup",
            "start_time": datetime(2024, 1, 8, 9, 0, tzinfo=timezone.utc),
            "end_time": datetime(2024, 1, 8, 9, 30, tzinfo=timezone.utc),
            "is_recurring": True,
            "recurrence_pattern": "Weekly on Monday",
            "is_all_day": False,
        }

        formatter = ObsidianNoteFormatter()
        content = formatter.format_event(event)

        assert "is_recurring: true" in content
        assert "recurrence_pattern: Weekly on Monday" in content
        assert "**Recurrence**: Weekly on Monday" in content

    def test_format_online_meeting(self):
        """Test formatting online meeting with join URL."""
        event = {
            "subject": "Remote Team Sync",
            "start_time": datetime(2024, 1, 18, 16, 0, tzinfo=timezone.utc),
            "end_time": datetime(2024, 1, 18, 17, 0, tzinfo=timezone.utc),
            "is_online_meeting": True,
            "online_meeting_url": "https://teams.microsoft.com/meet/12345",
            "is_all_day": False,
        }

        formatter = ObsidianNoteFormatter()
        content = formatter.format_event(event)

        assert "is_online_meeting: true" in content
        assert "online_meeting_url: https://teams.microsoft.com/meet/12345" in content
        assert "[Join Meeting](https://teams.microsoft.com/meet/12345)" in content

    def test_sanitize_frontmatter_value(self):
        """Test sanitizing values for frontmatter."""
        event = {
            "subject": 'Meeting: Project "Alpha"',
            "start_time": datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            "end_time": datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
            "location": "Room: B-102\nBuilding 5",
            "is_all_day": False,
        }

        formatter = ObsidianNoteFormatter()
        content = formatter.format_event(event)

        # Check that special characters are properly escaped
        assert 'title: "Meeting: Project \\"Alpha\\""' in content
        assert 'location: "Room: B-102\\nBuilding 5"' in content

    def test_generate_filename(self):
        """Test filename generation for events."""
        formatter = ObsidianNoteFormatter()

        # Simple event
        event1 = {
            "subject": "Team Meeting",
            "start_time": datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
        }
        filename1 = formatter.generate_filename(event1)
        assert filename1 == "2024-01-15 Team Meeting.md"

        # Event with special characters
        event2 = {
            "subject": "Budget Review: Q1/Q2",
            "start_time": datetime(2024, 2, 1, 10, 0, tzinfo=timezone.utc),
        }
        filename2 = formatter.generate_filename(event2)
        assert filename2 == "2024-02-01 Budget Review- Q1-Q2.md"

        # Long subject
        event3 = {
            "subject": "A" * 100,
            "start_time": datetime(2024, 3, 1, 9, 0, tzinfo=timezone.utc),
        }
        filename3 = formatter.generate_filename(event3)
        assert filename3.startswith("2024-03-01 ")
        assert len(filename3) <= 100  # Reasonable filename length

    def test_format_event_with_custom_tags(self):
        """Test adding custom tags to events."""
        event = {
            "subject": "Engineering Review",
            "start_time": datetime(2024, 1, 30, 14, 0, tzinfo=timezone.utc),
            "end_time": datetime(2024, 1, 30, 15, 30, tzinfo=timezone.utc),
            "is_all_day": False,
        }

        formatter = ObsidianNoteFormatter()
        content = formatter.format_event(event, tags=["engineering", "review", "q1"])

        assert "tags: [calendar-sync, engineering, review, q1]" in content

    def test_format_cancelled_event(self):
        """Test formatting cancelled event."""
        event = {
            "subject": "Cancelled Meeting",
            "start_time": datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            "end_time": datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc),
            "is_cancelled": True,
            "is_all_day": False,
        }

        formatter = ObsidianNoteFormatter()
        content = formatter.format_event(event)

        assert "is_cancelled: true" in content
        assert "status: cancelled" in content
        assert "> ⚠️ This event has been cancelled" in content
