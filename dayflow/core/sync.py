"""Calendar synchronization engine."""

from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional

from .graph_client import GraphAPIClient, GraphAPIError
from .obsidian_formatter import ObsidianNoteFormatter
from .daily_summary import DailySummaryGenerator
from ..vault.connection import VaultConnection


class CalendarSyncEngine:
    """Engine for synchronizing calendar events to Obsidian."""
    
    def __init__(self, access_token: str, vault_connection: Optional[VaultConnection] = None, 
                 create_daily_summaries: bool = True):
        """Initialize with access token.
        
        Args:
            access_token: Microsoft Graph API access token
            vault_connection: Optional vault connection for writing notes
            create_daily_summaries: Whether to create daily summary notes
        """
        self.access_token = access_token
        self.graph_client = GraphAPIClient(access_token)
        self.vault_connection = vault_connection
        self.formatter = ObsidianNoteFormatter()
        self.create_daily_summaries = create_daily_summaries
        self.daily_summary_generator = DailySummaryGenerator(vault_connection) if vault_connection else None
    
    def sync(self, start_date: Optional[date] = None, 
             end_date: Optional[date] = None) -> Dict[str, Any]:
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
            event for event in events 
            if not event.get('is_cancelled', False)
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
                    event_date = event['start_time'].date()
                    if event_date not in events_by_date:
                        events_by_date[event_date] = []
                    events_by_date[event_date].append(event)
                
                # Generate daily summaries
                summary_stats = self.daily_summary_generator.update_daily_summaries(events_by_date)
                daily_summaries_created = summary_stats['created']
                daily_summaries_updated = summary_stats['updated']
        
        # Return sync results
        return {
            'events_synced': len(active_events),
            'events': active_events,
            'sync_time': datetime.now(),
            'notes_created': notes_created,
            'notes_updated': notes_updated,
            'daily_summaries_created': daily_summaries_created,
            'daily_summaries_updated': daily_summaries_updated
        }
    
    def _process_event(self, event: Dict[str, Any]) -> tuple[bool, bool]:
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
        exists = self.vault_connection.note_exists(filename, 'calendar_events')
        
        # Format event as note
        content = self.formatter.format_event(event)
        
        # Write to vault
        self.vault_connection.write_note(content, filename, 'calendar_events')
        
        return (not exists, exists)  # (created, updated)


class ContinuousSyncManager:
    """Manager for continuous synchronization."""
    
    def __init__(self, sync_engine, interval_minutes=5):
        self.sync_engine = sync_engine
        self.interval_minutes = interval_minutes
    
    def start(self):
        """Start continuous synchronization."""
        pass