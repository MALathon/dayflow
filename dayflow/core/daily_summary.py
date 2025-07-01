"""Daily summary generator for calendar events."""

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..vault.connection import VaultConnection
from .obsidian_formatter import ObsidianNoteFormatter


class DailySummaryGenerator:
    """Generates daily summary notes that link to individual meeting notes."""

    def __init__(self, vault_connection: VaultConnection):
        """Initialize with vault connection.

        Args:
            vault_connection: Vault connection for reading/writing notes
        """
        self.vault_connection = vault_connection
        self.formatter = ObsidianNoteFormatter()

    def generate_daily_summary(
        self,
        summary_date: date,
        events: List[Dict[str, Any]],
        current_meeting: Optional[Dict[str, Any]] = None,
    ) -> Optional[Path]:
        """Generate a daily summary note for the given date.

        Args:
            summary_date: Date to generate summary for
            events: List of events for that day
            current_meeting: Optional current meeting to highlight

        Returns:
            Path to created/updated summary note, or None if no events
        """
        if not events:
            return None

        # Sort events by start time
        sorted_events = sorted(events, key=lambda e: e["start_time"])

        # Generate summary content
        content = self._format_daily_summary(
            summary_date, sorted_events, current_meeting
        )

        # Generate filename
        filename = f"{summary_date.strftime('%Y-%m-%d')} Daily Summary.md"

        # Write to daily notes location
        return self.vault_connection.write_note(content, filename, "daily_notes")

    def _format_daily_summary(
        self,
        summary_date: date,
        events: List[Dict[str, Any]],
        current_meeting: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Format the daily summary content.

        Args:
            summary_date: Date of the summary
            events: List of events for the day

        Returns:
            Formatted markdown content
        """
        # Build frontmatter
        frontmatter_lines = [
            "---",
            f"date: {summary_date}",
            "type: daily-summary",
            f"meetings_count: {len(events)}",
            "tags: [daily, calendar-sync]",
            f"generated: {datetime.now(timezone.utc).isoformat()}",
            "---",
        ]

        # Build content
        content_lines = [
            f'# {summary_date.strftime("%Y-%m-%d")} - Daily Summary',
            "",
            f'> 📅 {len(events)} meeting{"s" if len(events) != 1 else ""} today',
            "",
        ]

        # Add meetings section
        content_lines.extend(["## Meetings", ""])

        # Group meetings by time
        all_day_events = [e for e in events if e.get("is_all_day", False)]
        timed_events = [e for e in events if not e.get("is_all_day", False)]

        # Add all-day events first
        if all_day_events:
            content_lines.extend(["### All Day", ""])
            for event in all_day_events:
                note_link = self._get_meeting_note_link(event)
                cancelled = (
                    " ~~(Cancelled)~~" if event.get("is_cancelled", False) else ""
                )
                content_lines.append(f"- [[{note_link}]]{cancelled}")
            content_lines.append("")

        # Add timed events
        if timed_events:
            content_lines.extend(["### Schedule", ""])

            for event in timed_events:
                start_time = event["start_time"].strftime("%H:%M")
                end_time = event.get("end_time", event["start_time"]).strftime("%H:%M")
                note_link = self._get_meeting_note_link(event)

                # Build meeting line
                meeting_line = f"**{start_time}-{end_time}** | [[{note_link}]]"

                # Add current meeting indicator
                if current_meeting and event.get("id") == current_meeting.get("id"):
                    meeting_line = f"⏰ **NOW** | {meeting_line}"

                # Add location if present
                if event.get("location"):
                    meeting_line += f' | 📍 {event["location"]}'

                # Add online meeting indicator
                if event.get("is_online_meeting"):
                    meeting_line += " | 💻 Online"

                # Add cancelled indicator
                if event.get("is_cancelled"):
                    meeting_line = f"~~{meeting_line}~~"

                content_lines.append(meeting_line)

                # Add attendees on next line if present
                if event.get("attendees"):
                    attendee_names = []
                    for a in event["attendees"][:5]:
                        # Handle both Graph API and simple structures
                        if isinstance(a, dict):
                            if "emailAddress" in a:
                                # Graph API structure with nested emailAddress
                                email_addr = a.get("emailAddress", {})
                                if isinstance(email_addr, dict):
                                    name = email_addr.get(
                                        "name", email_addr.get("address", "Unknown")
                                    )
                                else:
                                    name = "Unknown"
                            else:
                                # Simple structure (for backwards compatibility)
                                name = a.get("name", a.get("email", "Unknown"))
                        else:
                            name = "Unknown"
                        attendee_names.append(name)

                    attendee_list = ", ".join(
                        [f"[[{name}]]" for name in attendee_names]
                    )
                    if len(event["attendees"]) > 5:
                        attendee_list += f' +{len(event["attendees"]) - 5} more'
                    content_lines.append(f"   👥 {attendee_list}")

                content_lines.append("")

        # Add quick access section
        content_lines.extend(["## Quick Links", "", "### By Time", ""])

        # Morning, afternoon, evening breakdown
        morning = [e for e in timed_events if e["start_time"].hour < 12]
        afternoon = [e for e in timed_events if 12 <= e["start_time"].hour < 17]
        evening = [e for e in timed_events if e["start_time"].hour >= 17]

        if morning:
            content_lines.append(f"🌅 **Morning** ({len(morning)} meetings)")
            for event in morning:
                note_link = self._get_meeting_note_link(event)
                time_str = event["start_time"].strftime("%H:%M")
                content_lines.append(f"- {time_str} - [[{note_link}]]")
            content_lines.append("")

        if afternoon:
            content_lines.append(f"☀️ **Afternoon** ({len(afternoon)} meetings)")
            for event in afternoon:
                note_link = self._get_meeting_note_link(event)
                time_str = event["start_time"].strftime("%H:%M")
                content_lines.append(f"- {time_str} - [[{note_link}]]")
            content_lines.append("")

        if evening:
            content_lines.append(f"🌙 **Evening** ({len(evening)} meetings)")
            for event in evening:
                note_link = self._get_meeting_note_link(event)
                time_str = event["start_time"].strftime("%H:%M")
                content_lines.append(f"- {time_str} - [[{note_link}]]")
            content_lines.append("")

        # Add action items section
        content_lines.extend(
            [
                "## Action Items Summary",
                "",
                "_Collect action items from today's meetings:_",
                "",
            ]
        )

        for event in events:
            if not event.get("is_cancelled", False):
                note_link = self._get_meeting_note_link(event)
                content_lines.extend([f"### [[{note_link}]]", "- [ ] ", ""])

        # Add daily reflection section
        content_lines.extend(
            [
                "## Daily Reflection",
                "",
                "### Key Accomplishments",
                "- ",
                "",
                "### Challenges",
                "- ",
                "",
                "### Tomorrow's Priorities",
                "- [ ] ",
                "",
            ]
        )

        # Add metadata section
        content_lines.extend(
            ["---", "", f'_Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}_']
        )

        # Combine frontmatter and content
        return "\n".join(frontmatter_lines) + "\n\n" + "\n".join(content_lines)

    def _get_meeting_note_link(self, event: Dict[str, Any]) -> str:
        """Get the note name for linking (without .md extension).

        Args:
            event: Event data

        Returns:
            Note name for wiki linking
        """
        # Use the same filename generation as the formatter
        filename = self.formatter.generate_filename(event)
        # Remove .md extension for wiki links
        return filename[:-3] if filename.endswith(".md") else filename

    def update_daily_summaries(
        self, events_by_date: Dict[date, List[Dict[str, Any]]]
    ) -> Dict[str, int]:
        """Update daily summaries for multiple dates.

        Args:
            events_by_date: Dictionary mapping dates to lists of events

        Returns:
            Statistics about created/updated summaries
        """
        created = 0
        updated = 0

        for summary_date, events in events_by_date.items():
            if not events:
                continue

            # Check if summary already exists
            filename = f"{summary_date.strftime('%Y-%m-%d')} Daily Summary.md"
            exists = self.vault_connection.note_exists(filename, "daily_notes")

            # Generate summary
            self.generate_daily_summary(summary_date, events)

            if exists:
                updated += 1
            else:
                created += 1

        return {"created": created, "updated": updated, "total": created + updated}
