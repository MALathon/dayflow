"""Enhanced progress indicators and CLI prettification."""

import sys
from typing import Optional

import click


class PrettyProgress:
    """Pretty progress display for CLI operations."""

    def __init__(self, show_progress: bool = True):
        """Initialize progress display.

        Args:
            show_progress: Whether to show progress (False for --quiet mode)
        """
        self.show_progress = show_progress
        self.current_line = ""
        self.last_width = 0

    def clear_line(self):
        """Clear the current line."""
        if not self.show_progress:
            return
        # Move cursor to beginning of line and clear
        sys.stdout.write("\r" + " " * self.last_width + "\r")
        sys.stdout.flush()

    def update(self, message: str, newline: bool = False):
        """Update progress display.

        Args:
            message: Message to display
            newline: Whether to end with newline (for completion)
        """
        if not self.show_progress:
            return

        self.clear_line()

        # Truncate message if too long for terminal
        try:
            import shutil

            terminal_width = shutil.get_terminal_size().columns
        except Exception:
            terminal_width = 80

        if len(message) > terminal_width - 1:
            message = message[: terminal_width - 4] + "..."

        self.last_width = len(message)

        if newline:
            click.echo(message)
            self.last_width = 0
        else:
            sys.stdout.write(f"\r{message}")
            sys.stdout.flush()

    def complete(self, message: str, style: str = "green"):
        """Complete progress with final message.

        Args:
            message: Completion message
            style: Click style for the message
        """
        if not self.show_progress:
            return
        self.clear_line()
        click.echo(click.style(message, fg=style))

    def error(self, message: str):
        """Show error message.

        Args:
            message: Error message
        """
        self.clear_line()
        click.echo(click.style(f"✗ {message}", fg="red"), err=True)

    def info(self, message: str):
        """Show info message with newline.

        Args:
            message: Info message
        """
        if not self.show_progress:
            return
        self.clear_line()
        click.echo(message)


def create_progress_bar(current: int, total: int, width: int = 30) -> str:
    """Create a text-based progress bar.

    Args:
        current: Current item number
        total: Total number of items
        width: Width of progress bar

    Returns:
        Progress bar string
    """
    if total == 0:
        return "[" + "=" * width + "]"

    filled = int(width * current / total)
    bar = "[" + "=" * filled + ">" + " " * (width - filled - 1) + "]"
    percentage = int(100 * current / total)

    return f"{bar} {percentage}% ({current}/{total})"


def format_time_remaining(seconds: int) -> str:
    """Format seconds into human-readable time.

    Args:
        seconds: Number of seconds

    Returns:
        Formatted time string
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s" if secs > 0 else f"{minutes}m"
    else:
        hours = seconds // 3600
        remaining = seconds % 3600
        minutes = remaining // 60
        return f"{hours}h {minutes}m"


def sync_with_pretty_progress(engine, start_date, end_date, quiet: bool = False):
    """Perform sync with pretty progress indicators.

    Args:
        engine: Sync engine instance
        start_date: Start date for sync
        end_date: End date for sync
        quiet: Suppress progress output

    Returns:
        Sync result dictionary
    """
    progress = PrettyProgress(show_progress=not quiet)
    events_synced = 0
    total_events = 0

    def progress_callback(action, **kwargs):
        nonlocal events_synced, total_events

        if action == "fetch_start":
            progress.update("🔄 Fetching calendar events...")
        elif action == "fetch_complete":
            total_events = kwargs.get("total", 0)
            progress.complete(f"✓ Found {total_events} events to sync", "green")
        elif action == "process_event":
            current = kwargs.get("current", 0)
            total = kwargs.get("total", 0)
            events_synced = current

            # Create progress bar
            bar = create_progress_bar(current, total)
            progress.update(f"📝 Syncing events: {bar}")

            # Complete on last event
            if current == total:
                progress.complete(f"✓ Synced {total} events successfully", "green")
        elif action == "sync_complete":
            # Final summary is handled by the sync command
            pass
        elif action == "fetch_error":
            error = kwargs.get("error", "Unknown error")
            progress.error(f"Error fetching events: {error}")

    # Perform sync with progress callback
    result = engine.sync(
        start_date=start_date,
        end_date=end_date,
        progress_callback=progress_callback,
    )

    return result


def create_summary_box(title: str, items: list, width: Optional[int] = None) -> str:
    """Create a pretty box with summary information.

    Args:
        title: Box title
        items: List of (label, value) tuples
        width: Box width (auto if None)

    Returns:
        Formatted box string
    """
    if width is None:
        # Calculate width based on content
        max_label_len = max(len(label) for label, _ in items) if items else 0
        max_value_len = max(len(str(value)) for _, value in items) if items else 0
        width = max(len(title) + 4, max_label_len + max_value_len + 7, 40)

    lines = []

    # Top border
    lines.append("╭" + "─" * (width - 2) + "╮")

    # Title
    title_padding = (width - len(title) - 2) // 2
    lines.append(
        "│"
        + " " * title_padding
        + title
        + " " * (width - len(title) - title_padding - 2)
        + "│"
    )

    # Separator
    lines.append("├" + "─" * (width - 2) + "┤")

    # Items
    for label, value in items:
        value_str = str(value)
        padding = width - len(label) - len(value_str) - 5
        lines.append(f"│ {label}: {' ' * padding}{value_str} │")

    # Bottom border
    lines.append("╰" + "─" * (width - 2) + "╯")

    return "\n".join(lines)


def pretty_print_status(status_info: dict):
    """Pretty print status information.

    Args:
        status_info: Dictionary with status information
    """
    # Authentication status
    if status_info.get("auth_valid"):
        auth_icon = "🔐"
        auth_status = "Valid"
        auth_color = "green"

        token_info = status_info.get("token_info", {})
        expires_in = token_info.get("expires_in_hours", 0)

        if expires_in < 1:
            auth_details = f"(expires in {int(expires_in * 60)} minutes)"
            auth_color = "yellow"
        else:
            auth_details = f"(expires in {expires_in:.1f} hours)"
    else:
        auth_icon = "🔓"
        auth_status = "Not authenticated"
        auth_color = "red"
        auth_details = ""

    click.echo(
        click.style(
            f"\n{auth_icon} Authentication: {auth_status} {auth_details}", fg=auth_color
        )
    )

    # Vault status
    if status_info.get("vault_configured"):
        vault_icon = "📁"
        vault_status = "Configured"
        vault_color = "green"
        vault_path = status_info.get("vault_path", "Unknown")
        vault_details = f"\n   Path: {vault_path}"
    else:
        vault_icon = "📂"
        vault_status = "Not configured"
        vault_color = "red"
        vault_details = ""

    click.echo(
        click.style(
            f"\n{vault_icon} Vault: {vault_status}{vault_details}", fg=vault_color
        )
    )

    # Sync status
    if status_info.get("sync_status"):
        sync_data = status_info["sync_status"]
        last_sync = sync_data.get("last_sync_display", "Never")
        sync_count = sync_data.get("sync_count", 0)
        error_count = sync_data.get("error_count", 0)

        sync_items = [
            ("Last sync", last_sync),
            ("Total syncs", sync_count),
            ("Errors", error_count),
        ]

        click.echo("\n" + create_summary_box("📊 Sync Status", sync_items))

    # Meeting context
    if status_info.get("meeting_context"):
        context = status_info["meeting_context"]

        if context.get("current_meeting"):
            meeting = context["current_meeting"]
            click.echo(
                click.style(
                    f"\n⏰ Current Meeting: {meeting['subject']}", fg="cyan", bold=True
                )
            )
            if meeting.get("location"):
                click.echo(f"   📍 {meeting['location']}")
            click.echo(f"   ⏱️  {meeting['start_time']} - {meeting['end_time']}")

        if context.get("next_meeting"):
            meeting = context["next_meeting"]
            click.echo(
                click.style(f"\n📅 Next Meeting: {meeting['subject']}", fg="blue")
            )
            click.echo(f"   ⏰ {meeting['start_time']} ({meeting['time_until']})")
            if meeting.get("location"):
                click.echo(f"   📍 {meeting['location']}")
