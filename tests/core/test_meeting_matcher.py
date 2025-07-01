"""Tests for meeting matcher functionality."""

import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from dayflow.core.meeting_matcher import MeetingMatcher


class TestMeetingMatcher:
    """Test the meeting matcher functionality."""

    @pytest.fixture
    def temp_vault(self):
        """Create a temporary vault for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_meeting_note(self, temp_vault):
        """Create a sample meeting note."""
        meetings_dir = temp_vault / "Meetings"
        meetings_dir.mkdir()

        # Current time for testing
        now = datetime.now(timezone.utc)

        # Create a meeting note that's currently active
        meeting_file = meetings_dir / "2024-01-15 Team Standup.md"
        meeting_content = f"""---
title: Team Standup
date: 2024-01-15
start_time: {now.isoformat()}
end_time: {(now + timedelta(hours=1)).isoformat()}
type: meeting
location: Conference Room A
tags: [calendar-sync]
---

# Team Standup

Meeting content here.
"""
        meeting_file.write_text(meeting_content, encoding="utf-8")
        return meetings_dir, now

    def test_find_current_meeting(self, temp_vault, sample_meeting_note):
        """Test finding currently active meeting."""
        meetings_dir, current_time = sample_meeting_note
        matcher = MeetingMatcher(temp_vault)

        # Should find the current meeting
        current = matcher.find_current_meeting(
            meetings_dir, current_time + timedelta(minutes=30)
        )

        assert current is not None
        assert current["title"] == "Team Standup"
        assert current["location"] == "Conference Room A"
        assert current["file_path"].name == "2024-01-15 Team Standup.md"

    def test_no_current_meeting(self, temp_vault, sample_meeting_note):
        """Test when no meeting is currently active."""
        meetings_dir, current_time = sample_meeting_note
        matcher = MeetingMatcher(temp_vault)

        # Check 2 hours later - meeting should be over
        current = matcher.find_current_meeting(
            meetings_dir, current_time + timedelta(hours=2)
        )

        assert current is None

    def test_find_upcoming_meeting(self, temp_vault):
        """Test finding upcoming meeting."""
        meetings_dir = temp_vault / "Meetings"
        meetings_dir.mkdir()

        matcher = MeetingMatcher(temp_vault)
        now = datetime.now(timezone.utc)

        # Create a meeting starting in 10 minutes
        upcoming_file = meetings_dir / "2024-01-15 Budget Review.md"
        upcoming_content = f"""---
title: Budget Review
date: 2024-01-15
start_time: {(now + timedelta(minutes=10)).isoformat()}
end_time: {(now + timedelta(minutes=70)).isoformat()}
type: meeting
---

# Budget Review
"""
        upcoming_file.write_text(upcoming_content, encoding="utf-8")

        # Should find the upcoming meeting
        upcoming = matcher.find_upcoming_meeting(
            meetings_dir, now, lookahead_minutes=15
        )

        assert upcoming is not None
        assert upcoming["title"] == "Budget Review"

    def test_find_recent_meeting(self, temp_vault):
        """Test finding recently ended meeting."""
        meetings_dir = temp_vault / "Meetings"
        meetings_dir.mkdir()

        matcher = MeetingMatcher(temp_vault)
        now = datetime.now(timezone.utc)

        # Create a meeting that ended 20 minutes ago
        recent_file = meetings_dir / "2024-01-15 Morning Scrum.md"
        recent_content = f"""---
title: Morning Scrum
date: 2024-01-15
start_time: {(now - timedelta(minutes=50)).isoformat()}
end_time: {(now - timedelta(minutes=20)).isoformat()}
type: meeting
---

# Morning Scrum
"""
        recent_file.write_text(recent_content, encoding="utf-8")

        # Should find the recent meeting
        recent = matcher.find_recent_meeting(meetings_dir, now, lookback_minutes=30)

        assert recent is not None
        assert recent["title"] == "Morning Scrum"

    def test_multiple_meetings_priority(self, temp_vault):
        """Test that most relevant meeting is returned when multiple exist."""
        meetings_dir = temp_vault / "Meetings"
        meetings_dir.mkdir()

        matcher = MeetingMatcher(temp_vault)
        now = datetime.now(timezone.utc)

        # Create multiple overlapping meetings
        for i, (start_offset, end_offset, title) in enumerate(
            [
                (-90, -30, "Early Meeting"),
                (-60, 30, "Overlapping Meeting 1"),
                (-30, 60, "Current Meeting"),
                (-15, 45, "Most Recent Start"),
            ]
        ):
            meeting_file = meetings_dir / f"2024-01-15 {title}.md"
            content = f"""---
title: {title}
date: 2024-01-15
start_time: {(now + timedelta(minutes=start_offset)).isoformat()}
end_time: {(now + timedelta(minutes=end_offset)).isoformat()}
type: meeting
---
"""
            meeting_file.write_text(content, encoding="utf-8")

        # Should return the meeting that started most recently
        current = matcher.find_current_meeting(meetings_dir, now)

        assert current is not None
        assert current["title"] == "Most Recent Start"

    def test_all_day_meeting(self, temp_vault):
        """Test handling of all-day meetings."""
        meetings_dir = temp_vault / "Meetings"
        meetings_dir.mkdir()

        matcher = MeetingMatcher(temp_vault)
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Create an all-day meeting
        allday_file = meetings_dir / "2024-01-15 Company Holiday.md"
        allday_content = f"""---
title: Company Holiday
date: 2024-01-15
start_time: {today_start.isoformat()}
end_time: {(today_start + timedelta(days=1)).isoformat()}
type: meeting
is_all_day: true
---

# Company Holiday
"""
        allday_file.write_text(allday_content, encoding="utf-8")

        # Should find the all-day meeting
        current = matcher.find_current_meeting(meetings_dir, now)

        assert current is not None
        assert current["title"] == "Company Holiday"
        assert current["is_all_day"] is True

    def test_parse_meeting_note_invalid(self, temp_vault):
        """Test parsing invalid meeting notes."""
        meetings_dir = temp_vault / "Meetings"
        meetings_dir.mkdir()

        matcher = MeetingMatcher(temp_vault)

        # Create invalid notes
        invalid_files = [
            # No frontmatter
            ("No Frontmatter.md", "# Just a regular note\n\nWith content"),
            # Not a meeting type
            ("Not Meeting.md", "---\ntitle: Some Note\ntype: note\n---\n\n# Content"),
            # Missing start_time
            ("No Time.md", "---\ntitle: Meeting\ntype: meeting\n---\n\n# Content"),
        ]

        for filename, content in invalid_files:
            (meetings_dir / filename).write_text(content, encoding="utf-8")

        # Should not find any valid meetings
        meetings = matcher.get_all_meetings(meetings_dir)
        assert len(meetings) == 0

    def test_timezone_handling(self, temp_vault):
        """Test proper timezone handling."""
        meetings_dir = temp_vault / "Meetings"
        meetings_dir.mkdir()

        matcher = MeetingMatcher(temp_vault)

        # Create meeting with different timezone formats
        now = datetime.now(timezone.utc)
        meeting_file = meetings_dir / "2024-01-15 TZ Test.md"

        # Use CST timezone (-06:00)
        cst_time = now.astimezone(timezone(timedelta(hours=-6)))
        meeting_content = f"""---
title: Timezone Test Meeting
date: 2024-01-15
start_time: {cst_time.isoformat()}
end_time: {(cst_time + timedelta(hours=1)).isoformat()}
type: meeting
---

# Timezone Test
"""
        meeting_file.write_text(meeting_content, encoding="utf-8")

        # Should find the meeting regardless of timezone
        current = matcher.find_current_meeting(meetings_dir, now)

        assert current is not None
        assert current["title"] == "Timezone Test Meeting"

    def test_no_end_time_handling(self, temp_vault):
        """Test meetings without end time (assumes 1 hour duration)."""
        meetings_dir = temp_vault / "Meetings"
        meetings_dir.mkdir()

        matcher = MeetingMatcher(temp_vault)
        now = datetime.now(timezone.utc)

        # Create meeting without end time
        meeting_file = meetings_dir / "2024-01-15 No End Time.md"
        meeting_content = f"""---
title: No End Time Meeting
date: 2024-01-15
start_time: {(now - timedelta(minutes=30)).isoformat()}
type: meeting
---

# Meeting without end time
"""
        meeting_file.write_text(meeting_content, encoding="utf-8")

        # Should find it within the assumed 1-hour duration
        current = matcher.find_current_meeting(meetings_dir, now)
        assert current is not None

        # Should not find it after 1 hour
        later = matcher.find_current_meeting(meetings_dir, now + timedelta(minutes=45))
        assert later is None
