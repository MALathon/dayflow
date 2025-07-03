"""Continuous sync daemon for Dayflow."""

import json
import os
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import click

from dayflow.core.sync import CalendarSyncEngine
from dayflow.ui.progress import PrettyProgress, create_progress_bar, create_summary_box


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
        self._progress = PrettyProgress()

        # Status file location
        self.status_file = Path.home() / ".dayflow" / "sync_status.json"
        self.pid_file = Path.home() / ".dayflow" / "sync.pid"
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

        # Write PID file
        self.pid_file.write_text(str(os.getpid()))

        # Show startup info box
        info_items = [
            ("Mode", "Continuous"),
            ("Interval", f"{self.interval // 60} minutes"),
            ("Total syncs", self._sync_count),
            (
                "Last sync",
                self._last_sync.strftime("%Y-%m-%d %H:%M")
                if self._last_sync
                else "Never",
            ),
        ]
        click.echo(create_summary_box("🔄 Continuous Sync Started", info_items))
        click.echo("\nPress Ctrl+C to stop\n")

        while self.running:
            try:
                # Perform sync
                self._sync_once()

                # Wait for next sync
                if self.running:
                    self._wait_with_countdown()

            except KeyboardInterrupt:
                break
            except Exception as e:
                self._error_count += 1
                self._progress.error(f"Sync error: {e}")
                click.echo(f"Will retry in {self.interval // 60} minutes...\n")

                if self.running:
                    self._wait_with_countdown()

        # Always call stop when exiting the loop
        self.stop()

    def stop(self):
        """Stop continuous sync."""
        self.running = False
        self._save_status()

        # Remove PID file
        if self.pid_file.exists():
            self.pid_file.unlink()

        # Show final summary
        summary_items = [
            ("Total syncs", self._sync_count),
            ("Errors", self._error_count),
            (
                "Last sync",
                self._last_sync.strftime("%Y-%m-%d %H:%M")
                if self._last_sync
                else "Never",
            ),
        ]
        click.echo(
            "\n" + create_summary_box("✅ Continuous Sync Stopped", summary_items)
        )

    def _sync_once(self):
        """Perform a single sync operation."""
        sync_start = datetime.now()

        # Show sync header
        sync_time = sync_start.strftime("%Y-%m-%d %H:%M:%S")
        click.echo(f"\n📅 Sync #{self._sync_count + 1} - {sync_time}")
        click.echo("─" * 60)

        # Sync last hour to current time + 1 day
        # This ensures we catch recently created/updated events
        start_date = (datetime.now() - timedelta(hours=1)).date()
        end_date = (datetime.now() + timedelta(days=1)).date()

        # Progress callback for continuous sync
        def progress_callback(action, **kwargs):
            if action == "fetch_start":
                self._progress.update("🔄 Fetching calendar events...")
            elif action == "fetch_complete":
                total = kwargs.get("total", 0)
                self._progress.complete(f"✓ Found {total} events to sync", "green")
            elif action == "process_event":
                current = kwargs.get("current", 0)
                total = kwargs.get("total", 0)
                bar = create_progress_bar(current, total)
                self._progress.update(f"📝 Syncing events: {bar}")

                if current == total:
                    self._progress.complete(
                        f"✓ Synced {total} events successfully", "green"
                    )

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
            daily_created = result.get("daily_summaries_created", 0)
            daily_updated = result.get("daily_summaries_updated", 0)

            sync_duration = (datetime.now() - sync_start).total_seconds()

            # Create summary box
            summary_items = [
                ("Events synced", events_synced),
                ("Notes created", notes_created),
                ("Notes updated", notes_updated),
            ]

            if daily_created + daily_updated > 0:
                summary_items.extend(
                    [
                        ("Daily summaries created", daily_created),
                        ("Daily summaries updated", daily_updated),
                    ]
                )

            summary_items.append(("Duration", f"{sync_duration:.1f}s"))

            click.echo("\n" + create_summary_box("✨ Sync Complete", summary_items))

            # Save status after successful sync
            self._save_status()

    def _wait_with_countdown(self):
        """Wait for the next sync with a countdown display."""
        next_sync = datetime.now() + timedelta(seconds=self.interval)
        click.echo(f"\n⏰ Next sync at {next_sync.strftime('%H:%M:%S')}")

        # Show countdown
        for remaining in range(int(self.interval), 0, -1):
            if not self.running:
                break

            if remaining <= 10:
                self._progress.update(f"⏳ Next sync in {remaining} seconds...")
            elif remaining % 60 == 0:
                minutes = remaining // 60
                self._progress.update(
                    f"⏳ Next sync in {minutes} minute{'s' if minutes != 1 else ''}..."
                )
            elif remaining % 10 == 0:  # Update every 10 seconds
                minutes = remaining // 60
                seconds = remaining % 60
                if minutes > 0:
                    self._progress.update(f"⏳ Next sync in {minutes}m {seconds}s...")
                else:
                    self._progress.update(f"⏳ Next sync in {seconds} seconds...")

            time.sleep(1)

        if self.running:
            self._progress.clear_line()  # Clear the countdown line

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
                    click.style(
                        f"📂 Resuming from previous session "
                        f"(last sync: {last_sync_str})",
                        fg="cyan",
                    )
                )

        except Exception as e:
            click.echo(f"Warning: Could not load sync status: {e}", err=True)
