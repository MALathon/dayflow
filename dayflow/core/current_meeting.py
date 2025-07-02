"""Current meeting identification and management."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..vault.connection import VaultConnection
from .obsidian_formatter import ObsidianNoteFormatter


class CurrentMeetingManager:
    """Manages identification and tracking of current meetings."""

    def __init__(self, vault_connection: VaultConnection):
        """Initialize with vault connection.

        Args:
            vault_connection: Connection to the vault
        """
        self.vault_connection = vault_connection
        self.formatter = ObsidianNoteFormatter()

    def get_current_meeting(
        self, events: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Get the currently active meeting.

        Args:
            events: List of calendar events

        Returns:
            Current meeting or None
        """
        now = datetime.now(timezone.utc)

        # Find meetings that are currently active
        active_meetings = []
        for event in events:
            start = event["start_time"]
            end = event.get("end_time", start + timedelta(hours=1))

            # Convert to UTC if needed
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            if end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)

            if start <= now <= end:
                active_meetings.append(event)

        if not active_meetings:
            return None

        # If multiple meetings, prioritize non-all-day events
        # and then return the most recently started
        non_all_day = [e for e in active_meetings if not e.get("is_all_day", False)]
        if non_all_day:
            return max(non_all_day, key=lambda e: e["start_time"])
        return max(active_meetings, key=lambda e: e["start_time"])

    def get_next_meeting(
        self, events: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Get the next upcoming meeting.

        Args:
            events: List of calendar events

        Returns:
            Next meeting or None
        """
        now = datetime.now(timezone.utc)

        # Find future meetings
        future_meetings = []
        for event in events:
            start = event["start_time"]
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)

            if start > now:
                future_meetings.append(event)

        if not future_meetings:
            return None

        # Return the soonest meeting
        return min(future_meetings, key=lambda e: e["start_time"])

    def get_meeting_status(self, event: Dict[str, Any]) -> str:
        """Get the status of a meeting relative to current time.

        Args:
            event: Calendar event

        Returns:
            Status: "past", "current", "soon", or "future"
        """
        now = datetime.now(timezone.utc)
        start = event["start_time"]
        end = event.get("end_time", start + timedelta(hours=1))

        # Convert to UTC if needed
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)

        if end < now:
            return "past"
        elif start <= now <= end:
            return "current"
        elif start - now <= timedelta(minutes=15):
            return "soon"
        else:
            return "future"

    def update_current_meeting_shortcut(
        self, current_meeting: Optional[Dict[str, Any]]
    ) -> Optional[Path]:
        """Update the current meeting shortcut in vault root.

        Args:
            current_meeting: Current meeting info or None

        Returns:
            Path to shortcut file
        """
        shortcut_path = self.vault_connection.config.vault_path / "Current Meeting.md"

        if current_meeting:
            # Create shortcut content
            content = self._format_current_meeting_shortcut(current_meeting)
            shortcut_path.write_text(content, encoding="utf-8")
        else:
            # No current meeting - create placeholder or remove
            content = self._format_no_meeting_placeholder()
            shortcut_path.write_text(content, encoding="utf-8")

        return shortcut_path

    def _format_current_meeting_shortcut(self, meeting: Dict[str, Any]) -> str:
        """Format the current meeting shortcut content.

        Args:
            meeting: Current meeting data

        Returns:
            Formatted shortcut content
        """
        # Generate the actual note filename
        filename = self.formatter.generate_filename(meeting)
        note_name = filename[:-3]  # Remove .md extension

        # Calculate time info
        now = datetime.now(timezone.utc)
        start = meeting["start_time"]
        end = meeting.get("end_time", start + timedelta(hours=1))

        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)

        elapsed = now - start
        remaining = end - now

        elapsed_min = int(elapsed.total_seconds() / 60)
        remaining_min = int(remaining.total_seconds() / 60)

        lines = [
            "---",
            "title: Current Meeting Shortcut",
            "tags: [current-meeting, shortcut]",
            "---",
            "",
            f"# ⏰ NOW: {meeting.get('subject', 'Untitled')}",
            "",
            f"[[{note_name}]]",
            "",
            "## Meeting Status",
            f"- Started: {elapsed_min} minutes ago",
            f"- Remaining: {remaining_min} minutes",
            "",
        ]

        if meeting.get("location"):
            lines.extend(
                [
                    "## Location",
                    f"📍 {meeting['location']}",
                    "",
                ]
            )

        if meeting.get("attendees"):
            lines.extend(
                [
                    "## Attendees",
                    "",
                ]
            )
            # Use the same attendee extraction logic as daily summary
            for attendee in meeting["attendees"][:5]:
                if isinstance(attendee, dict):
                    if "emailAddress" in attendee:
                        email_addr = attendee.get("emailAddress", {})
                        if isinstance(email_addr, dict):
                            name = email_addr.get(
                                "name", email_addr.get("address", "Unknown")
                            )
                        else:
                            name = "Unknown"
                    else:
                        name = attendee.get("name", attendee.get("email", "Unknown"))
                else:
                    name = str(attendee)
                lines.append(f"- [[{name}]]")

            if len(meeting["attendees"]) > 5:
                lines.append(f"- ...and {len(meeting['attendees']) - 5} more")
            lines.append("")

        return "\n".join(lines)

    def _format_no_meeting_placeholder(self) -> str:
        """Format placeholder when no meeting is active."""
        return """---
title: Current Meeting Shortcut
tags: [current-meeting, shortcut]
---

# No Meeting Currently Active

No meeting currently in progress.

## Next Meeting

Check your [[Daily Summary]] for upcoming meetings.
"""

    def generate_home_widget(self, events: List[Dict[str, Any]]) -> str:
        """Generate a widget for the home page showing current/next meetings.

        Args:
            events: List of calendar events

        Returns:
            Formatted widget content
        """
        current = self.get_current_meeting(events)
        next_meeting = self.get_next_meeting(events)

        lines = ["## 📅 Current Meeting", ""]

        if current:
            # Current meeting info
            elapsed = datetime.now(timezone.utc) - current["start_time"]
            elapsed_min = int(elapsed.total_seconds() / 60)

            remaining = current.get(
                "end_time", current["start_time"] + timedelta(hours=1)
            ) - datetime.now(timezone.utc)
            remaining_min = int(remaining.total_seconds() / 60)

            lines.extend(
                [
                    f"**[[Current Meeting]]** - {current.get('subject', 'Untitled')}",
                    f"Started {elapsed_min} minutes ago • "
                    f"{remaining_min} minutes remaining",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    "*No meeting currently in progress*",
                    "",
                ]
            )

        if next_meeting:
            # Next meeting info
            time_until = next_meeting["start_time"] - datetime.now(timezone.utc)

            if time_until.total_seconds() < 3600:  # Less than an hour
                minutes = int(time_until.total_seconds() / 60)
                time_str = f"in {minutes} minutes"
            elif time_until.total_seconds() < 86400:  # Less than a day
                hours = int(time_until.total_seconds() / 3600)
                time_str = f"in {hours} hour{'s' if hours != 1 else ''}"
            else:
                days = int(time_until.total_seconds() / 86400)
                time_str = f"in {days} day{'s' if days != 1 else ''}"

            lines.extend(
                [
                    "### 🔜 Next Meeting",
                    "",
                    f"**{next_meeting.get('subject', 'Untitled')}** - {time_str}",
                    f"At {next_meeting['start_time'].strftime('%H:%M')}",
                ]
            )

        return "\n".join(lines)
