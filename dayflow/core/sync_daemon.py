"""Continuous sync daemon for Dayflow."""

import json
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import click

from dayflow.core.sync import CalendarSyncEngine


class ContinuousSyncManager:
    """Manages continuous syncing of calendar events."""

    def __init__(self, engine: CalendarSyncEngine, interval_minutes: int = 5):
        """Initialize the continuous sync manager.

        Args:
            engine: The calendar sync engine to use
            interval_minutes: Minutes between sync operations
        """
        self.engine = engine
        self.interval = interval_minutes * 60  # Convert to seconds
        self.running = False
        self._last_sync: Optional[datetime] = None
        self._sync_count = 0
        self._error_count = 0

        # Status file location
        self.status_file = Path.home() / ".dayflow" / "sync_status.json"
        self.status_file.parent.mkdir(exist_ok=True)

        # Load previous status if exists
        self._load_status()

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        click.echo("\n\nReceived shutdown signal. Stopping continuous sync...")
        self.stop()
        sys.exit(0)

    def start(self):
        """Start continuous sync."""
        self.running = True
        click.echo(
            f"Starting continuous sync (interval: {self.interval // 60} minutes)"
        )
        click.echo("Press Ctrl+C to stop\n")

        while self.running:
            try:
                # Perform sync
                self._sync_once()

                # Wait for next sync
                if self.running:
                    self._wait_with_countdown()

            except KeyboardInterrupt:
                self.stop()
                break
            except Exception as e:
                self._error_count += 1
                click.echo(f"\n❌ Sync error: {e}", err=True)
                click.echo(f"Will retry in {self.interval // 60} minutes...\n")

                if self.running:
                    self._wait_with_countdown()

    def stop(self):
        """Stop continuous sync."""
        self.running = False
        self._save_status()
        click.echo("\nContinuous sync stopped.")
        click.echo(f"Total syncs: {self._sync_count}, Errors: {self._error_count}")

    def _sync_once(self):
        """Perform a single sync operation."""
        sync_start = datetime.now()

        # Show sync header
        click.echo(f"\n{'='*60}")
        click.echo(
            f"Sync #{self._sync_count + 1} - {sync_start.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        click.echo(f"{'='*60}")

        # Sync last hour to current time + 1 day
        # This ensures we catch recently created/updated events
        start_date = (datetime.now() - timedelta(hours=1)).date()
        end_date = (datetime.now() + timedelta(days=1)).date()

        # Progress callback for continuous sync
        def progress_callback(action, **kwargs):
            if action == "fetch_start":
                click.echo("Fetching calendar events...")
            elif action == "process_event":
                current = kwargs.get("current", 0)
                total = kwargs.get("total", 0)
                click.echo(f"Processing event {current} of {total}...")

        try:
            result = self.engine.sync(
                start_date=start_date,
                end_date=end_date,
                progress_callback=progress_callback,
            )
        except Exception:
            # Re-raise to be handled by caller
            raise

        if result:
            self._sync_count += 1
            self._last_sync = sync_start

            # Display results
            events_synced = result.get("events_synced", 0)
            notes_created = result.get("notes_created", 0)
            notes_updated = result.get("notes_updated", 0)

            click.echo(f"✓ Synced {events_synced} events")
            if notes_created > 0:
                click.echo(f"✓ Created {notes_created} new notes")
            if notes_updated > 0:
                click.echo(f"✓ Updated {notes_updated} existing notes")

            sync_duration = (datetime.now() - sync_start).total_seconds()
            click.echo(f"\nSync completed in {sync_duration:.1f} seconds")

            # Save status after successful sync
            self._save_status()

    def _wait_with_countdown(self):
        """Wait for the next sync with a countdown display."""
        next_sync = datetime.now() + timedelta(seconds=self.interval)
        click.echo(f"\nNext sync at {next_sync.strftime('%H:%M:%S')}")

        # Show countdown in the last 10 seconds
        for remaining in range(int(self.interval), 0, -1):
            if not self.running:
                break

            if remaining <= 10:
                click.echo(f"\rNext sync in {remaining} seconds...", nl=False)
            elif remaining % 60 == 0:
                minutes = remaining // 60
                click.echo(f"\rNext sync in {minutes} minutes...    ", nl=False)

            time.sleep(1)

        if self.running:
            click.echo("\r" + " " * 50 + "\r", nl=False)  # Clear the line

    def _save_status(self):
        """Save sync status to file."""
        status = {
            "last_sync": self._last_sync.isoformat() if self._last_sync else None,
            "sync_count": self._sync_count,
            "error_count": self._error_count,
            "interval_minutes": self.interval // 60,
            "updated_at": datetime.now().isoformat(),
        }

        try:
            self.status_file.write_text(json.dumps(status, indent=2), encoding="utf-8")
        except Exception as e:
            click.echo(f"Warning: Could not save sync status: {e}", err=True)

    def _load_status(self):
        """Load previous sync status from file."""
        if not self.status_file.exists():
            return

        try:
            status = json.loads(self.status_file.read_text(encoding="utf-8"))

            # Restore counts from previous session
            self._sync_count = status.get("sync_count", 0)
            self._error_count = status.get("error_count", 0)

            if status.get("last_sync"):
                self._last_sync = datetime.fromisoformat(status["last_sync"])
                last_sync_str = self._last_sync.strftime("%Y-%m-%d %H:%M")
                click.echo(
                    f"Resuming from previous session (last sync: {last_sync_str})"
                )

        except Exception as e:
            click.echo(f"Warning: Could not load sync status: {e}", err=True)
