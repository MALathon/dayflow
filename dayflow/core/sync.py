"""Calendar synchronization engine."""

from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional, Tuple

from ..vault.connection import VaultConnection
from .current_meeting import CurrentMeetingManager
from .daily_summary import DailySummaryGenerator
from .graph_client import GraphAPIClient, GraphAPIError
from .obsidian_formatter import ObsidianNoteFormatter


class CalendarSyncEngine:
    """Engine for synchronizing calendar events to Obsidian."""

    def __init__(
        self,
        access_token: str,
        vault_connection: Optional[VaultConnection] = None,
        create_daily_summaries: bool = True,
    ):
        """Initialize with access token.

        Args:
            access_token: Microsoft Graph API access token
            vault_connection: Optional vault connection for writing notes
            create_daily_summaries: Whether to create daily summary notes
        """
        self.access_token = access_token
        self.graph_client = GraphAPIClient(access_token)
        self.vault_connection = vault_connection

        # Check if we should use time prefixes based on folder organization
        use_time_prefix = False
        if vault_connection:
            folder_org = vault_connection.config.get_setting(
                "calendar.folder_organization"
            )
            use_time_prefix = folder_org is not None

        self.formatter = ObsidianNoteFormatter(use_time_prefix=use_time_prefix)
        self.create_daily_summaries = create_daily_summaries
        self.daily_summary_generator = (
            DailySummaryGenerator(vault_connection) if vault_connection else None
        )
        self.current_meeting_manager = (
            CurrentMeetingManager(vault_connection) if vault_connection else None
        )

    def sync(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Perform calendar synchronization.

        Args:
            start_date: Start date for sync (default: yesterday)
            end_date: End date for sync (default: 7 days from today)

        Returns:
            Dictionary with sync results including:
            - events_synced: Number of events synced
            - events: List of event data
            - sync_time: When sync was performed
            - notes_created: Number of new notes created
            - notes_updated: Number of notes updated
        """
        # Use default date range if not specified
        if start_date is None:
            start_date = date.today() - timedelta(days=1)
        if end_date is None:
            end_date = date.today() + timedelta(days=7)

        # Fetch events from Graph API
        try:
            events = self.graph_client.fetch_calendar_events(start_date, end_date)
        except GraphAPIError:
            # Re-raise Graph API errors for now
            raise

        # Filter out cancelled events
        active_events = [
            event for event in events if not event.get("is_cancelled", False)
        ]

        # Process events and create/update notes
        notes_created = 0
        notes_updated = 0
        daily_summaries_created = 0
        daily_summaries_updated = 0

        if self.vault_connection:
            for event in active_events:
                created, updated = self._process_event(event)
                if created:
                    notes_created += 1
                elif updated:
                    notes_updated += 1

            # Create daily summaries if enabled
            if self.create_daily_summaries and self.daily_summary_generator:
                # Group events by date
                events_by_date = {}
                for event in active_events:
                    event_date = event["start_time"].date()
                    if event_date not in events_by_date:
                        events_by_date[event_date] = []
                    events_by_date[event_date].append(event)

                # Find current meeting if applicable
                current_meeting = None
                if self.current_meeting_manager:
                    current_meeting = self.current_meeting_manager.get_current_meeting(
                        active_events
                    )
                    # Update current meeting shortcut
                    self.current_meeting_manager.update_current_meeting_shortcut(
                        current_meeting
                    )

                # Generate daily summaries with current meeting highlighted
                for event_date, events in events_by_date.items():
                    # Only pass current_meeting if it's on this date
                    current_for_date = None
                    if (
                        current_meeting
                        and current_meeting["start_time"].date() == event_date
                    ):
                        current_for_date = current_meeting

                    filename = f"{event_date.strftime('%Y-%m-%d')} Daily Summary.md"
                    exists = self.vault_connection.note_exists(filename, "daily_notes")

                    self.daily_summary_generator.generate_daily_summary(
                        event_date, events, current_meeting=current_for_date
                    )

                    if exists:
                        daily_summaries_updated += 1
                    else:
                        daily_summaries_created += 1

        # Return sync results
        return {
            "events_synced": len(active_events),
            "events": active_events,
            "sync_time": datetime.now(),
            "notes_created": notes_created,
            "notes_updated": notes_updated,
            "daily_summaries_created": daily_summaries_created,
            "daily_summaries_updated": daily_summaries_updated,
        }

    def _process_event(self, event: Dict[str, Any]) -> Tuple[bool, bool]:
        """Process a single event and create/update note.

        Args:
            event: Calendar event data

        Returns:
            Tuple of (created, updated) booleans
        """
        if not self.vault_connection:
            return (False, False)

        # Generate filename
        filename = self.formatter.generate_filename(event)

        # Check if note already exists
        exists = self.vault_connection.note_exists(filename, "calendar_events")

        # Format event as note
        content = self.formatter.format_event(event)

        # Get event date for folder organization
        event_date = event["start_time"].date()

        # Write to vault with date folder if configured
        self.vault_connection.write_note(
            content, filename, "calendar_events", date_folder=event_date
        )

        return (not exists, exists)  # (created, updated)


class ContinuousSyncManager:
    """Manager for continuous synchronization."""

    def __init__(self, sync_engine, interval_minutes=5):
        self.sync_engine = sync_engine
        self.interval_minutes = interval_minutes

    def start(self):
        """Start continuous synchronization."""
        pass
