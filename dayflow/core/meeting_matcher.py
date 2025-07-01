"""Meeting matcher to find which meeting a note belongs to based on time."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class MeetingMatcher:
    """Matches notes to meetings based on creation time."""

    def __init__(self, vault_path: Path):
        """Initialize with vault path.

        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_path = vault_path

    def find_current_meeting(
        self, meeting_notes_path: Path, current_time: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """Find the meeting that is currently happening.

        Args:
            meeting_notes_path: Path to folder containing meeting notes
            current_time: Time to check (defaults to now)

        Returns:
            Meeting data if found, None otherwise
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)

        # Get all meeting notes
        meetings = self.get_all_meetings(meeting_notes_path)

        # Find meetings that are currently active
        active_meetings = []
        for meeting in meetings:
            if self.is_meeting_active(meeting, current_time):
                active_meetings.append(meeting)

        if not active_meetings:
            return None

        # If multiple meetings, return the one that started most recently
        return max(active_meetings, key=lambda m: m["start_time"])

    def find_upcoming_meeting(
        self,
        meeting_notes_path: Path,
        current_time: Optional[datetime] = None,
        lookahead_minutes: int = 15,
    ) -> Optional[Dict[str, Any]]:
        """Find the next upcoming meeting within lookahead window.

        Args:
            meeting_notes_path: Path to folder containing meeting notes
            current_time: Time to check (defaults to now)
            lookahead_minutes: How many minutes ahead to look

        Returns:
            Meeting data if found, None otherwise
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)

        meetings = self.get_all_meetings(meeting_notes_path)

        # Find meetings starting soon
        upcoming = []
        for meeting in meetings:
            if self.is_meeting_upcoming(meeting, current_time, lookahead_minutes):
                upcoming.append(meeting)

        if not upcoming:
            return None

        # Return the one starting soonest
        return min(upcoming, key=lambda m: m["start_time"])

    def find_recent_meeting(
        self,
        meeting_notes_path: Path,
        current_time: Optional[datetime] = None,
        lookback_minutes: int = 30,
    ) -> Optional[Dict[str, Any]]:
        """Find the most recent meeting that ended.

        Args:
            meeting_notes_path: Path to folder containing meeting notes
            current_time: Time to check (defaults to now)
            lookback_minutes: How many minutes back to look

        Returns:
            Meeting data if found, None otherwise
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)

        meetings = self.get_all_meetings(meeting_notes_path)

        # Find recently ended meetings
        recent = []
        for meeting in meetings:
            if self.is_meeting_recent(meeting, current_time, lookback_minutes):
                recent.append(meeting)

        if not recent:
            return None

        # Return the one that ended most recently
        return max(recent, key=lambda m: m.get("end_time", m["start_time"]))

    def get_all_meetings(self, meeting_notes_path: Path) -> List[Dict[str, Any]]:
        """Get all meetings from note files.

        Args:
            meeting_notes_path: Path to folder containing meeting notes

        Returns:
            List of meeting data dictionaries
        """
        meetings = []

        if not meeting_notes_path.exists():
            return meetings

        for note_file in meeting_notes_path.glob("*.md"):
            meeting_data = self.parse_meeting_note(note_file)
            if meeting_data:
                meetings.append(meeting_data)

        return meetings

    def parse_meeting_note(self, note_path: Path) -> Optional[Dict[str, Any]]:
        """Parse meeting data from a note file.

        Args:
            note_path: Path to the note file

        Returns:
            Meeting data if valid, None otherwise
        """
        try:
            content = note_path.read_text(encoding="utf-8")

            # Extract frontmatter
            if not content.startswith("---"):
                return None

            parts = content.split("---", 2)
            if len(parts) < 3:
                return None

            frontmatter = yaml.safe_load(parts[1])

            # Ensure it's a meeting note
            if frontmatter.get("type") != "meeting":
                return None

            # Parse times
            start_time = self.parse_time(frontmatter.get("start_time"))
            end_time = self.parse_time(frontmatter.get("end_time"))

            if not start_time:
                return None

            return {
                "file_path": note_path,
                "title": frontmatter.get("title", "Untitled"),
                "start_time": start_time,
                "end_time": end_time,
                "is_all_day": frontmatter.get("is_all_day", False),
                "location": frontmatter.get("location"),
                "frontmatter": frontmatter,
            }

        except Exception:
            return None

    def parse_time(self, time_str: Any) -> Optional[datetime]:
        """Parse time from various formats.

        Args:
            time_str: Time string or datetime object

        Returns:
            Parsed datetime or None
        """
        if isinstance(time_str, datetime):
            return time_str

        if not isinstance(time_str, str):
            return None

        try:
            # Try ISO format first
            return datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        except Exception:
            try:
                # Try other common formats
                return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            except Exception:
                return None

    def is_meeting_active(
        self, meeting: Dict[str, Any], current_time: datetime
    ) -> bool:
        """Check if a meeting is currently active.

        Args:
            meeting: Meeting data
            current_time: Current time

        Returns:
            True if meeting is active
        """
        start = meeting["start_time"]
        end = meeting.get("end_time")

        # Ensure timezone awareness
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end and end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)

        # Check if current time is within meeting time
        if current_time < start:
            return False

        if end and current_time > end:
            return False

        # If no end time, assume 1 hour duration
        if not end:

            assumed_end = start + timedelta(hours=1)
            if current_time > assumed_end:
                return False

        return True

    def is_meeting_upcoming(
        self, meeting: Dict[str, Any], current_time: datetime, lookahead_minutes: int
    ) -> bool:
        """Check if a meeting is starting soon.

        Args:
            meeting: Meeting data
            current_time: Current time
            lookahead_minutes: How many minutes ahead to look

        Returns:
            True if meeting is upcoming
        """

        start = meeting["start_time"]

        # Ensure timezone awareness
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)

        # Check if meeting starts within lookahead window
        window_end = current_time + timedelta(minutes=lookahead_minutes)

        return current_time <= start <= window_end

    def is_meeting_recent(
        self, meeting: Dict[str, Any], current_time: datetime, lookback_minutes: int
    ) -> bool:
        """Check if a meeting recently ended.

        Args:
            meeting: Meeting data
            current_time: Current time
            lookback_minutes: How many minutes back to look

        Returns:
            True if meeting recently ended
        """

        end = meeting.get("end_time", meeting["start_time"])

        # Ensure timezone awareness
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)

        # If no end time, assume 1 hour duration
        if not meeting.get("end_time"):
            end = meeting["start_time"] + timedelta(hours=1)

        # Check if meeting ended within lookback window
        window_start = current_time - timedelta(minutes=lookback_minutes)

        return window_start <= end <= current_time
