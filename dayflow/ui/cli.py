"""Command Line Interface for Dayflow."""

import base64
import json
import subprocess
import webbrowser
from datetime import datetime, timedelta, timezone
from pathlib import Path

import click

from dayflow import __version__


def get_token_info():
    """Get information about the current token."""
    token_file = Path(".graph_token")

    if not token_file.exists():
        return None

    try:
        with open(token_file, "r") as f:
            token_data = json.load(f)

        expires_at = datetime.fromisoformat(token_data.get("expires_at", ""))
        now = datetime.now()

        return {
            "valid": now <= expires_at,
            "expires_at": expires_at,
            "age_minutes": int(
                (
                    now - datetime.fromisoformat(token_data.get("acquired_at", ""))
                ).total_seconds()
                / 60
            ),
        }
    except Exception:
        return None


def has_valid_token():
    """Check if a valid token exists."""
    token_info = get_token_info()
    return token_info is not None and token_info["valid"]


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="dayflow")
@click.pass_context
def cli(ctx):
    """Dayflow CLI."""
    if ctx.invoked_subcommand is None:
        # Show welcome message when no command is provided
        click.echo("Dayflow")
        click.echo("Usage: dayflow [OPTIONS] COMMAND [ARGS]...")
        click.echo("Try 'dayflow --help' for help.")


@cli.group()
def auth():
    """Manage authentication and tokens."""
    pass


@auth.command(name="status")
def auth_status():
    """Check authentication status."""
    token_info = get_token_info()

    if not token_info:
        click.echo("No valid token found.")
        click.echo("Please run 'dayflow auth login' to authenticate.")
        return

    if not token_info["valid"]:
        click.echo("Token has expired.")
        click.echo("Please run 'dayflow auth login' to get a new token.")
    else:
        time_left = token_info["expires_at"] - datetime.now()
        minutes_left = int(time_left.total_seconds() / 60)
        hours_left = time_left.total_seconds() / 3600

        click.echo("Token is valid.")

        # Show time in appropriate units
        if hours_left > 2:
            expires_at = token_info['expires_at'].strftime('%Y-%m-%d %H:%M:%S')
            click.echo(f"Expires in {hours_left:.1f} hours ({expires_at})")
        else:
            click.echo(f"Expires in {minutes_left} minutes.")

        # Show warning if expiring soon
        if minutes_left < 10:
            click.echo("⚠️  Token expires soon! Consider refreshing.")


@auth.command(name="login")
@click.option(
    "--no-interactive",
    is_flag=True,
    hidden=True,
    help="Non-interactive mode for testing",
)
def auth_login(no_interactive):
    """Authenticate using Microsoft Graph Explorer (manual token workflow)."""
    # Open Graph Explorer
    graph_explorer_url = "https://developer.microsoft.com/en-us/graph/graph-explorer"
    webbrowser.open(graph_explorer_url)

    if not no_interactive:
        click.echo("Opening Microsoft Graph Explorer in your browser...")
        click.echo("Please follow these steps:")
        click.echo("1. Sign in with your Mayo Clinic credentials")
        click.echo("2. Run a test query to get a token")
        click.echo("3. Copy the Access Token from the 'Access token' tab")
        click.echo("4. The token will be automatically read from your clipboard")
        click.pause("Press any key when you've copied the token...")

    # Read token from clipboard
    try:
        token = subprocess.check_output(["pbpaste"]).decode("utf-8").strip()
    except Exception as e:
        click.echo(f"Error reading from clipboard: {e}")
        return

    # Validate token
    if len(token) < 100:
        click.echo(
            "Invalid token (too short). Please make sure you copied the access token."
        )
        return

    # Decode JWT to get actual expiry time
    try:
        parts = token.split(".")
        if len(parts) >= 2:
            # Decode the payload (second part)
            payload = parts[1]
            # Add padding if needed
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += "=" * padding

            decoded = base64.b64decode(payload)
            payload_json = json.loads(decoded)

            # Get actual expiry time from token
            if "exp" in payload_json:
                expires_at = datetime.fromtimestamp(payload_json["exp"])
            else:
                # Fallback to 1 hour if we can't decode
                expires_at = datetime.now() + timedelta(hours=1)
        else:
            # Fallback if not a JWT
            expires_at = datetime.now() + timedelta(hours=1)
    except Exception as e:
        click.echo(f"Warning: Could not decode token expiry, assuming 1 hour: {e}")
        expires_at = datetime.now() + timedelta(hours=1)

    # Store token with metadata
    token_data = {
        "access_token": token,
        "acquired_at": datetime.now().isoformat(),
        "expires_at": expires_at.isoformat(),
        "source": "graph_explorer_manual",
    }

    # Save to file
    token_file = Path(".graph_token")
    with open(token_file, "w") as f:
        json.dump(token_data, f, indent=2)

    # Calculate time remaining
    time_remaining = expires_at - datetime.now()
    hours_remaining = time_remaining.total_seconds() / 3600

    click.echo("Token saved successfully!")
    click.echo(f"Token expires at: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
    click.echo(f"Time remaining: {hours_remaining:.1f} hours")


@auth.command(name="logout")
def auth_logout():
    """Remove stored authentication token."""
    token_file = Path(".graph_token")
    if token_file.exists():
        token_file.unlink()
        click.echo("Logged out successfully.")
    else:
        click.echo("No token found. Already logged out.")


@cli.command()
@click.option(
    "--start", type=click.DateTime(formats=["%Y-%m-%d"]), help="Start date (YYYY-MM-DD)"
)
@click.option(
    "--end", type=click.DateTime(formats=["%Y-%m-%d"]), help="End date (YYYY-MM-DD)"
)
@click.option("--continuous", is_flag=True, help="Run continuously until token expires")
@click.option(
    "--interval",
    type=int,
    default=5,
    help="Sync interval in minutes (for continuous mode)",
)
@click.option(
    "--no-daily-summary", is_flag=True, help="Skip creating daily summary notes"
)
def sync(start, end, continuous, interval, no_daily_summary):
    """Synchronize calendar events to Obsidian."""
    # Check if authenticated
    if not has_valid_token():
        click.echo("Error: Not authenticated or token has expired.")
        click.echo("Please run 'dayflow auth login' to authenticate.")
        raise click.Abort()

    # Import here to avoid circular imports
    from dayflow.core.graph_client import GraphAPIError
    from dayflow.core.sync import CalendarSyncEngine
    from dayflow.vault import VaultConfig, VaultConfigError, VaultConnection

    # Load the access token
    token_file = Path(".graph_token")
    try:
        with open(token_file, "r") as f:
            token_data = json.load(f)
        access_token = token_data.get("access_token")
    except Exception as e:
        click.echo(f"Error loading token: {e}")
        raise click.Abort()

    # Check vault configuration
    vault_connection = None
    try:
        config = VaultConfig()
        config.validate()
        vault_connection = VaultConnection(config)
        click.echo(f"Using vault: {config.vault_path}")
    except VaultConfigError as e:
        click.echo(f"⚠️  No vault configured: {e}")
        click.echo("Notes will not be created. Run 'dayflow vault setup' to configure.")
        if not click.confirm("Continue without writing notes?"):
            raise click.Abort()

    # Create sync engine with access token and vault connection
    engine = CalendarSyncEngine(
        access_token, vault_connection, create_daily_summaries=not no_daily_summary
    )

    if continuous:
        # Continuous sync mode
        click.echo("Continuous sync not yet implemented.")
        # manager = ContinuousSyncManager(engine, interval)
        # manager.start()
    else:
        # Single sync
        try:
            # Convert click.DateTime to date objects if provided
            start_date = start.date() if start else None
            end_date = end.date() if end else None

            # Show what we're syncing
            if start_date and end_date:
                click.echo(f"Syncing events from {start_date} to {end_date}...")
            else:
                click.echo("Syncing events with default date range...")

            # Perform sync
            result = engine.sync(start_date=start_date, end_date=end_date)

            # Display results
            if result:
                events_synced = result.get("events_synced", 0)
                notes_created = result.get("notes_created", 0)
                notes_updated = result.get("notes_updated", 0)
                daily_created = result.get("daily_summaries_created", 0)
                daily_updated = result.get("daily_summaries_updated", 0)
                # sync_time = result.get("sync_time")  # TODO: Use for display

                click.echo(f"\n✓ Synced {events_synced} active events")

                if vault_connection:
                    if notes_created > 0:
                        click.echo(f"✓ Created {notes_created} new meeting notes")
                    if notes_updated > 0:
                        click.echo(f"✓ Updated {notes_updated} existing meeting notes")
                    if notes_created == 0 and notes_updated == 0 and events_synced > 0:
                        click.echo("  (All events already have notes)")

                    # Daily summary info
                    if daily_created > 0 or daily_updated > 0:
                        click.echo("")
                        if daily_created > 0:
                            click.echo(
                                f"📅 Created {daily_created} daily summary note{
                                    's' if daily_created != 1 else ''}")
                        if daily_updated > 0:
                            click.echo(
                                f"📅 Updated {daily_updated} daily summary note{
                                    's' if daily_updated != 1 else ''}")
                else:
                    click.echo("  (No notes created - vault not configured)")

                if events_synced > 0:
                    click.echo("\nEvents synced:")
                    for event in result.get("events", [])[:5]:  # Show first 5
                        subject = event.get("subject", "Untitled")
                        start_time = event.get("start_time")
                        if start_time:
                            time_str = start_time.strftime("%Y-%m-%d %H:%M")
                            click.echo(f"  - {subject} ({time_str})")
                    if events_synced > 5:
                        click.echo(f"  ... and {events_synced - 5} more")

        except GraphAPIError as e:
            if e.status_code == 401:
                click.echo("Error: Authentication failed. Token may have expired.")
                click.echo("Please run 'dayflow auth login' to get a new token.")
            else:
                click.echo(f"Error: {e}")
            raise click.Abort()
        except Exception as e:
            click.echo(f"Error during sync: {e}")
            raise click.Abort()


@cli.group()
def gtd():
    """GTD (Getting Things Done) operations."""
    pass


@gtd.command("inbox")
@click.option("--add", "-a", help="Add item to inbox")
@click.option("--list", "-l", "show_list", is_flag=True, help="List inbox items")
def gtd_inbox(add, show_list):
    """Manage GTD inbox."""
    from dayflow.core.gtd import GTDSystem
    from dayflow.vault import VaultConfig, VaultConnection

    # Check vault configuration
    try:
        config = VaultConfig()
        config.validate()
        vault_conn = VaultConnection(config)
    except Exception as e:
        click.echo(f"Error: Vault not configured - {e}")
        click.echo("Run 'dayflow vault setup' first")
        raise click.Abort()

    gtd = GTDSystem(vault_conn)

    if add:
        # Add to inbox
        try:
            path = gtd.add_to_inbox(add)
            click.echo(f"✅ Added to inbox: {path.name}")
        except Exception as e:
            click.echo(f"Error adding to inbox: {e}")
            raise click.Abort()
    else:
        # List inbox (default)
        items = gtd.get_inbox_items()
        if items:
            click.echo(f"📥 Inbox ({len(items)} items):")
            for item in items:
                click.echo(f"  {item['id']}. {item['content']}")
                if item.get("source"):
                    click.echo(f"     Source: {item['source']}")
        else:
            click.echo("📥 Inbox is empty")


@gtd.command("process")
@click.option(
    "--interactive/--no-interactive", default=True, help="Interactive processing mode"
)
def gtd_process(interactive):
    """Process GTD inbox items."""
    from dayflow.core.gtd import GTDSystem
    from dayflow.vault import VaultConfig, VaultConnection

    try:
        config = VaultConfig()
        config.validate()
        vault_conn = VaultConnection(config)
    except Exception as e:
        click.echo(f"Error: Vault not configured - {e}")
        return

    gtd = GTDSystem(vault_conn)
    items = gtd.get_inbox_items()

    if not items:
        click.echo("📥 Inbox is empty - nothing to process!")
        return

    click.echo(f"📥 Processing {len(items)} inbox items...")

    if interactive:
        for item in items:
            click.echo(f"\n📄 {item['content']}")
            if item.get("source"):
                click.echo(f"   Source: {item['source']}")

            # Show options
            click.echo("\nWhat would you like to do?")
            click.echo("  1. Make it a Next Action")
            click.echo("  2. Make it a Project")
            click.echo("  3. Add to Waiting For")
            click.echo("  4. Add to Someday/Maybe")
            click.echo("  5. File as Reference")
            click.echo("  6. Delete")
            click.echo("  s. Skip")
            click.echo("  q. Quit")

            choice = click.prompt("Choice", type=str, default="s")

            if choice == "q":
                break
            elif choice == "s":
                continue
            # In a real implementation, we'd process based on choice

            click.echo("✅ Processed")
    else:
        click.echo("Non-interactive processing not implemented yet")


@gtd.command("review")
@click.option("--generate", is_flag=True, help="Generate weekly review template")
@click.option(
    "--week", type=click.DateTime(formats=["%Y-%m-%d"]), help="Week start date"
)
def gtd_review(generate, week):
    """Weekly review operations."""
    from dayflow.core.gtd import WeeklyReviewGenerator
    from dayflow.vault import VaultConfig, VaultConnection

    try:
        config = VaultConfig()
        config.validate()
        vault_conn = VaultConnection(config)
    except Exception as e:
        click.echo(f"Error: Vault not configured - {e}")
        return

    if generate:
        generator = WeeklyReviewGenerator(vault_conn)
        try:
            week_start = week.date() if week else None
            path = generator.create_review(week_start)
            click.echo(f"✅ Weekly review generated: {path.name}")

            # Offer to open in Obsidian
            if click.confirm("Open in Obsidian?", default=False):
                import webbrowser

                vault_name = config.vault_path.name
                relative_path = path.relative_to(config.vault_path)
                obsidian_url = (
                    f"obsidian://open?vault={vault_name}&file={relative_path}"
                )
                webbrowser.open(obsidian_url)
        except Exception as e:
            click.echo(f"Error generating review: {e}")
    else:
        click.echo("Use --generate to create a weekly review template")


@cli.group()
def zettel():
    """Zettelkasten note management."""
    pass


@zettel.command("new")
@click.option("--title", "-t", prompt=True, help="Note title")
@click.option(
    "--type",
    "-T",
    "note_type",
    type=click.Choice(["permanent", "literature", "fleeting"]),
    default="permanent",
    help="Type of note",
)
@click.option("--content", "-c", help="Note content (or use editor)")
@click.option("--editor", "-e", is_flag=True, help="Open editor for content")
@click.option("--tags", help="Comma-separated tags")
@click.option("--refs", help="Comma-separated reference IDs")
def zettel_new(title, note_type, content, editor, tags, refs):
    """Create new Zettelkasten note."""
    from dayflow.core.zettel import ZettelkastenEngine
    from dayflow.vault import VaultConfig, VaultConnection

    try:
        config = VaultConfig()
        config.validate()
        vault_conn = VaultConnection(config)
    except Exception as e:
        click.echo(f"Error: Vault not configured - {e}")
        return

    # Get content
    if editor or not content:
        initial_content = (
            content or "## Key Insight\n\n\n## Elaboration\n\n\n## Connections\n\n"
        )
        content = click.edit(initial_content, require_save=True, extension=".md")
        if not content:
            click.echo("Note creation cancelled.")
            return

    # Parse tags and refs
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    ref_list = [r.strip() for r in refs.split(",")] if refs else None

    # Create note
    engine = ZettelkastenEngine(vault_conn)
    try:
        path = engine.create_zettel(
            title=title,
            content=content,
            zettel_type=note_type,
            tags=tag_list,
            references=ref_list,
        )
        click.echo(f"✅ Created note: {path.name}")

        # Extract ID from filename
        zettel_id = path.name.split()[0]
        click.echo(f"   ID: {zettel_id}")
    except Exception as e:
        click.echo(f"Error creating note: {e}")


@zettel.command("literature")
@click.option("--title", "-t", prompt=True, help="Note title")
@click.option("--source", "-s", prompt=True, help="Source (book/article title)")
@click.option("--author", "-a", help="Author name")
@click.option("--content", "-c", help="Initial notes")
def zettel_literature(title, source, author, content):
    """Create literature note from source material."""
    from dayflow.core.zettel import ZettelkastenEngine
    from dayflow.vault import VaultConfig, VaultConnection

    try:
        config = VaultConfig()
        config.validate()
        vault_conn = VaultConnection(config)
    except Exception as e:
        click.echo(f"Error: Vault not configured - {e}")
        return

    engine = ZettelkastenEngine(vault_conn)
    try:
        path = engine.create_literature_note(
            title=title, source=source, author=author, content=content or ""
        )
        click.echo(f"✅ Created literature note: {path.name}")
    except Exception as e:
        click.echo(f"Error creating note: {e}")


@zettel.command("suggest")
@click.option("--process", "-p", help="Path to literature note to process")
def zettel_suggest(process):
    """Suggest permanent notes from literature notes."""
    from dayflow.core.zettel import ZettelkastenEngine
    from dayflow.vault import VaultConfig, VaultConnection

    try:
        config = VaultConfig()
        config.validate()
        vault_conn = VaultConnection(config)
    except Exception as e:
        click.echo(f"Error: Vault not configured - {e}")
        return

    engine = ZettelkastenEngine(vault_conn)

    if process:
        # Process specific literature note
        path = Path(process)
        if not path.exists():
            # Try to find in literature folder
            lit_path = config.get_location("zettel_literature")
            if lit_path:
                path = lit_path / process

        if path.exists():
            suggestions = engine.suggest_permanent_notes(path)
            if suggestions:
                click.echo(f"💡 Suggested permanent notes from {path.name}:")
                for i, suggestion in enumerate(suggestions, 1):
                    click.echo(f"\n{i}. {suggestion['title']}")
                    click.echo(f"   Reason: {suggestion['reason']}")
            else:
                click.echo("No suggestions found.")
        else:
            click.echo(f"Literature note not found: {process}")
    else:
        # Find all unprocessed literature notes
        unprocessed = engine.find_unprocessed_literature_notes()
        if unprocessed:
            click.echo(f"📚 Found {len(unprocessed)} unprocessed literature notes:")
            for note in unprocessed[:10]:
                click.echo(f"  - {note.name}")
            if len(unprocessed) > 10:
                click.echo(f"  ... and {len(unprocessed) - 10} more")
            click.echo(
                "\nUse --process <filename> to get suggestions for a specific note"
            )
        else:
            click.echo("No unprocessed literature notes found.")


@zettel.command("search")
@click.argument("query")
def zettel_search(query):
    """Search Zettelkasten notes."""
    from dayflow.core.zettel import ZettelkastenEngine
    from dayflow.vault import VaultConfig, VaultConnection

    try:
        config = VaultConfig()
        config.validate()
        vault_conn = VaultConnection(config)
    except Exception as e:
        click.echo(f"Error: Vault not configured - {e}")
        return

    engine = ZettelkastenEngine(vault_conn)
    results = engine.search_zettels(query)

    if results:
        click.echo(f"🔍 Found {len(results)} matches for '{query}':")
        for path, line in results:
            click.echo(f"\n📄 {path.name}")
            click.echo(f"   {line}")
    else:
        click.echo(f"No matches found for '{query}'")


@cli.command()
@click.option("--title", "-t", prompt="Note title", help="Title for the quick note")
@click.option(
    "--link-meeting/--no-link-meeting", default=True, help="Link to current meeting"
)
@click.option(
    "--editor/--no-editor",
    "-e/-E",
    default=False,
    help="Open in editor for full content",
)
@click.option(
    "--template",
    "-T",
    type=click.Choice(["meeting", "idea", "task", "reference"]),
    help="Use a note template",
)
def note(title, link_meeting, editor, template):
    """Create a note with optional meeting context and templates."""
    from datetime import datetime

    from dayflow.core.meeting_matcher import MeetingMatcher
    from dayflow.vault import VaultConfig, VaultConnection

    # Check vault configuration
    try:
        config = VaultConfig()
        config.validate()
        vault_conn = VaultConnection(config)
    except Exception as e:
        click.echo(f"Error: Vault not configured - {e}")
        click.echo("Run 'dayflow vault setup' first")
        raise click.Abort()

    # Build note content
    timestamp = datetime.now()

    frontmatter_lines = [
        "---",
        f"title: {title}",
        f'date: {timestamp.strftime("%Y-%m-%d")}',
        f"created: {timestamp.isoformat()}",
        "type: note",
        "tags: [quick-note]",
    ]

    content_lines = [
        f"# {title}",
        "",
        f'Created: {timestamp.strftime("%Y-%m-%d %H:%M")}',
        "",
    ]

    # Check for current meeting
    if link_meeting:
        try:
            matcher = MeetingMatcher(config.vault_path)
            meeting_path = config.get_location("calendar_events")

            if meeting_path and meeting_path.exists():
                current = matcher.find_current_meeting(meeting_path)
                if current:
                    # Add meeting link to frontmatter
                    meeting_note_name = current["file_path"].stem
                    frontmatter_lines.append(f'meeting: "[[{meeting_note_name}]]"')

                    # Add context to content
                    content_lines.extend(
                        [
                            "## Meeting Context",
                            f"This note was created during: [[{meeting_note_name}]]",
                            "",
                        ]
                    )

                    click.echo(f"✅ Linked to meeting: {current['title']}")
                else:
                    # Check for upcoming meeting
                    upcoming = matcher.find_upcoming_meeting(
                        meeting_path, lookahead_minutes=5
                    )
                    if upcoming:
                        meeting_note_name = upcoming["file_path"].stem
                        frontmatter_lines.append(f'meeting: "[[{meeting_note_name}]]"')
                        content_lines.extend(
                            [
                                "## Meeting Context",
                                f"This note was created before: [[{meeting_note_name}]]",
                                "",
                            ]
                        )
                        click.echo(
                            f"✅ Linked to upcoming meeting: {upcoming['title']}"
                        )
        except Exception as e:
            click.echo(f"Warning: Could not check for meetings - {e}")

    # Add template content based on type
    if template == "meeting":
        content_lines.extend(
            [
                "## Key Points",
                "",
                "- ",
                "",
                "## Decisions",
                "",
                "- ",
                "",
                "## Action Items",
                "",
                "- [ ] ",
                "",
                "## Follow-up Required",
                "",
                "- ",
                "",
            ]
        )
    elif template == "idea":
        content_lines.extend(
            [
                "## The Idea",
                "",
                "",
                "## Why It Matters",
                "",
                "",
                "## Next Steps",
                "",
                "- [ ] ",
                "",
                "## Related Concepts",
                "",
                "- ",
                "",
            ]
        )
    elif template == "task":
        content_lines.extend(
            [
                "## Task Description",
                "",
                "",
                "## Success Criteria",
                "",
                "- [ ] ",
                "",
                "## Resources Needed",
                "",
                "- ",
                "",
                "## Notes",
                "",
                "",
            ]
        )
    elif template == "reference":
        content_lines.extend(
            [
                "## Source",
                "",
                "",
                "## Key Information",
                "",
                "",
                "## My Notes",
                "",
                "",
                "## How This Applies",
                "",
                "",
            ]
        )
    else:
        # Default template
        content_lines.extend(
            [
                "## Notes",
                "",
                "",
                "## Key Points",
                "",
                "- ",
                "",
                "## Action Items",
                "",
                "- [ ] ",
                "",
            ]
        )

    # Close frontmatter
    frontmatter_lines.append("---")

    # Combine frontmatter and content
    full_content = "\n".join(frontmatter_lines) + "\n\n" + "\n".join(content_lines)

    # If editor mode, let user edit before saving
    if editor:
        edited_content = click.edit(full_content, require_save=True, extension=".md")
        if edited_content is None:
            click.echo("Note creation cancelled.")
            return
        full_content = edited_content
    else:
        # Interactive mode - let user add content
        click.echo("\n📝 Add your note content (press Ctrl+D when done):")
        click.echo("   Tip: Use Markdown formatting")
        click.echo("")

        additional_lines = []
        try:
            # Collect lines until EOF (Ctrl+D)
            while True:
                line = click.prompt(
                    "", default="", show_default=False, prompt_suffix=""
                )
                additional_lines.append(line)
        except (click.Abort, EOFError, KeyboardInterrupt):
            # User pressed Ctrl+D or Ctrl+C
            pass

        if additional_lines and additional_lines != [""]:
            # Find where to insert the content (before first empty heading)
            lines = full_content.split("\n")
            insert_pos = None

            # Look for first section with empty content
            for i, line in enumerate(lines):
                if line.startswith("## ") and i + 2 < len(lines) and lines[i + 2] == "":
                    insert_pos = i + 2
                    break

            if insert_pos:
                # Insert the user's content
                lines[insert_pos:insert_pos] = additional_lines + [""]
                full_content = "\n".join(lines)
            else:
                # Append at the end
                full_content += "\n" + "\n".join(additional_lines)

    # Generate filename
    safe_title = title.replace("/", "-").replace(":", "-")
    filename = f'{timestamp.strftime("%Y-%m-%d-%H%M")} {safe_title}.md'

    # Write note (to daily notes location if configured, otherwise calendar events)
    folder_type = (
        "daily_notes" if config.get_location("daily_notes") else "calendar_events"
    )

    try:
        note_path = vault_conn.write_note(full_content, filename, folder_type)
        click.echo(f"✅ Created note: {note_path.name}")
        click.echo(f"   Location: {note_path.parent}")
    except Exception as e:
        click.echo(f"Error creating note: {e}")
        import traceback

        traceback.print_exc()
        raise click.Abort()

    # Offer to open in Obsidian (only in interactive mode)
    try:
        if click.confirm("Open in Obsidian?", default=False):
            vault_name = config.vault_path.name
            relative_path = note_path.relative_to(config.vault_path)
            obsidian_url = f"obsidian://open?vault={vault_name}&file={relative_path}"
            webbrowser.open(obsidian_url)
    except Exception:
        # Don't fail if opening in Obsidian fails
        pass


@cli.group()
def vault():
    """Vault management commands."""
    pass


@vault.command("init")
@click.option("--path", help="Path to Obsidian vault")
@click.option(
    "--template",
    type=click.Choice(["para", "gtd", "time_based", "zettelkasten"]),
    help="Organization template to apply",
)
@click.option(
    "--interactive/--no-interactive", default=True, help="Run interactive setup wizard"
)
def vault_init(path, template, interactive):
    """Initialize Obsidian vault configuration."""
    # Use interactive wizard by default
    if interactive and not path and not template:
        from dayflow.vault.setup_wizard import VaultSetupWizard

        wizard = VaultSetupWizard()
        if not wizard.run():
            raise click.Abort()
        return

    # Fall back to original implementation for non-interactive mode
    from dayflow.vault import VaultConfig, VaultDetector

    detector = VaultDetector()

    # If no path provided, try to detect or prompt
    if not path:
        click.echo("🔍 Searching for Obsidian vaults...")
        vaults = detector.find_obsidian_vaults()

        if vaults:
            click.echo(f"\nFound {len(vaults)} Obsidian vault(s):")
            for i, vault in enumerate(vaults, 1):
                click.echo(f"  {i}. {vault}")
            click.echo(f"  {len(vaults) + 1}. Enter custom path")

            choice = click.prompt("Select vault", type=int)
            if choice <= len(vaults):
                path = str(vaults[choice - 1])
            else:
                path = click.prompt("Enter vault path")
        else:
            path = click.prompt("No vaults found. Enter vault path")

    # Validate path
    vault_path = Path(path)
    if not vault_path.exists():
        click.echo(f"Error: Path does not exist: {path}")
        raise click.Abort()

    if not (vault_path / ".obsidian").exists():
        if not click.confirm(
            f"'{path}' doesn't appear to be an Obsidian vault. Continue anyway?"
        ):
            raise click.Abort()

    # Create/update config
    config = VaultConfig()
    config.set_vault_path(path)

    # Apply template if specified
    if template:
        config.apply_template(template)
        click.echo(f"Applied {template.upper()} template")
    else:
        # Ask about template
        templates = config.list_templates()
        click.echo("\nAvailable templates:")
        for i, tmpl in enumerate(templates, 1):
            click.echo(f"  {i}. {tmpl}")
        click.echo(f"  {len(templates) + 1}. No template (custom structure)")

        choice = click.prompt("Select template", type=int)
        if choice <= len(templates):
            template = templates[choice - 1]
            config.apply_template(template)
            click.echo(f"Applied {template.upper()} template")

    click.echo("\n✅ Vault initialization complete!")
    click.echo(f"Configuration saved to: {config.config_path}")


@vault.command("set-path")
@click.argument("path")
def vault_set_path(path):
    """Set the vault path."""
    from dayflow.vault import VaultConfig

    vault_path = Path(path)
    if not vault_path.exists():
        click.echo(f"Error: Path does not exist: {path}")
        raise click.Abort()

    config = VaultConfig()
    config.set_vault_path(path)
    click.echo(f"✅ Vault path updated to: {path}")


@vault.command("set-location")
@click.argument("location_type")
@click.argument("path")
def vault_set_location(location_type, path):
    """Set path for a specific location type."""
    from dayflow.vault import VaultConfig

    config = VaultConfig()
    config.set_location(location_type, path)
    click.echo(f"✅ Location updated: {location_type} -> {path}")


@vault.command("list-templates")
def vault_list_templates():
    """List available vault templates."""
    from dayflow.vault import VaultConfig

    config = VaultConfig()
    templates = config.list_templates()

    click.echo("Available templates:")
    for template in templates:
        click.echo(f"  - {template}")


@vault.command("apply-template")
@click.argument(
    "template", type=click.Choice(["para", "gtd", "time_based", "zettelkasten"])
)
def vault_apply_template(template):
    """Apply an organization template."""
    from dayflow.vault import VaultConfig

    config = VaultConfig()
    config.apply_template(template)
    click.echo(f"✅ Applied {template.upper()} template")


@vault.command("status")
def vault_status():
    """Show current vault configuration."""
    from dayflow.vault import VaultConfig, VaultConfigError

    try:
        config = VaultConfig()

        click.echo("Vault Status")
        click.echo("=" * 40)
        click.echo(f"Path: {config.vault_path}")
        click.echo("\nLocations:")

        locations = config.config.get("vault", {}).get("locations", {})
        for loc_type, loc_path in locations.items():
            click.echo(f"  {loc_type}: {loc_path}")

        # Try to validate
        try:
            config.validate()
            click.echo("\n✅ Vault is valid and accessible")
        except VaultConfigError as e:
            click.echo(f"\n⚠️  Validation warning: {e}")

    except VaultConfigError as e:
        click.echo(f"Error: {e}")
        click.echo("Run 'dayflow vault init' to set up vault configuration")


@vault.command("validate")
def vault_validate():
    """Validate vault configuration."""
    from dayflow.vault import VaultConfig, VaultConfigError

    try:
        config = VaultConfig()
        config.validate()
        click.echo("✅ Vault configuration is valid")
    except VaultConfigError as e:
        click.echo(f"❌ Validation failed: {e}")
        raise click.Abort()


@vault.command("setup")
def vault_setup():
    """Run interactive vault setup wizard (recommended).

    This user-friendly wizard will:
    - Find your Obsidian vaults automatically
    - Show your existing folder structure
    - Suggest appropriate locations for calendar events
    - Create folders as needed
    - Test the setup with a sample file

    No manual path typing required!
    """
    from dayflow.vault.setup_wizard import VaultSetupWizard

    wizard = VaultSetupWizard()
    if not wizard.run():
        raise click.Abort()


@vault.command("detect")
def vault_detect():
    """Detect Obsidian vaults on system."""
    from dayflow.vault import VaultDetector

    detector = VaultDetector()
    click.echo("🔍 Searching for Obsidian vaults...")

    vaults = detector.find_obsidian_vaults()

    if vaults:
        click.echo(f"\nFound {len(vaults)} Obsidian vault(s):")
        for vault in vaults:
            click.echo(f"  - {vault}")
    else:
        click.echo("No Obsidian vaults found in common locations")


@cli.group()
def config():
    """Configuration management."""
    pass


@config.command("show")
def config_show():
    """Show current configuration."""
    from dayflow.vault import VaultConfig

    try:
        config = VaultConfig()

        if config.config_path.exists():
            click.echo("Current Configuration")
            click.echo("=" * 40)
            click.echo(config.config_path.read_text())
        else:
            click.echo("No configuration found")
            click.echo("Run 'dayflow vault init' to create configuration")
    except Exception as e:
        click.echo(f"Error reading configuration: {e}")


@config.command("path")
def config_path():
    """Show configuration file path."""
    from dayflow.vault import VaultConfig

    config = VaultConfig()
    click.echo(f"Configuration file: {config.config_path}")


@config.command("edit")
def config_edit():
    """Edit configuration in your editor."""
    from dayflow.vault import VaultConfig

    config = VaultConfig()

    # Read current content
    if config.config_path.exists():
        content = config.config_path.read_text()
    else:
        content = "# Dayflow Configuration\n"

    # Open in editor
    edited = click.edit(content)

    if edited is not None and edited != content:
        # Save changes
        config.config_path.parent.mkdir(parents=True, exist_ok=True)
        config.config_path.write_text(edited)
        click.echo("✅ Configuration updated")
    else:
        click.echo("No changes made")


@config.command("reset")
def config_reset():
    """Reset configuration to defaults."""
    from dayflow.vault import VaultConfig

    if click.confirm("Are you sure you want to reset configuration to defaults?"):
        config = VaultConfig()
        config.config_path.parent.mkdir(parents=True, exist_ok=True)

        import yaml

        with open(config.config_path, "w") as f:
            yaml.dump(VaultConfig.DEFAULT_CONFIG, f, default_flow_style=False)

        click.echo("✅ Configuration reset to defaults")


@config.command("get")
@click.argument("key")
def config_get(key):
    """Get a specific configuration value."""
    from dayflow.vault import VaultConfig

    config = VaultConfig()

    # Navigate the config dict
    value = config.config
    for part in key.split("."):
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            click.echo(f"Key not found: {key}")
            raise click.Abort()

    click.echo(value)


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key, value):
    """Set a specific configuration value."""
    import yaml

    from dayflow.vault import VaultConfig

    config = VaultConfig()

    # Navigate and set the value
    parts = key.split(".")
    data = config.config

    # Navigate to parent
    for part in parts[:-1]:
        if part not in data:
            data[part] = {}
        data = data[part]

    # Set the value
    data[parts[-1]] = value

    # Save
    with open(config.config_path, "w") as f:
        yaml.dump(config.config, f, default_flow_style=False)

    click.echo("✅ Configuration updated")


@cli.command()
def status():
    """Show system status and health."""
    click.echo("System Status")
    click.echo("=" * 40)

    # Check authentication
    token_info = get_token_info()
    if token_info and token_info["valid"]:
        hours_left = (token_info["expires_at"] - datetime.now()).total_seconds() / 3600
        click.echo(f"✅ Authentication: Valid ({hours_left:.1f} hours remaining)")
    else:
        click.echo("❌ Authentication: No valid token")

    # Check vault configuration
    try:
        from dayflow.vault import VaultConfig

        config = VaultConfig()
        config.validate()
        click.echo(f"✅ Vault: {config.vault_path}")
    except Exception as e:
        click.echo(f"❌ Vault: Not configured ({e})")

    # Check current meeting context
    click.echo("\nMeeting Context")
    click.echo("-" * 40)

    try:
        from dayflow.core.meeting_matcher import MeetingMatcher
        from dayflow.vault import VaultConfig

        config = VaultConfig()
        matcher = MeetingMatcher(config.vault_path)
        meeting_path = config.get_location("calendar_events")

        if meeting_path and meeting_path.exists():
            # Current meeting
            current = matcher.find_current_meeting(meeting_path)
            if current:
                click.echo(f"📍 Current: {current['title']}")
                click.echo(f"   Started: {current['start_time'].strftime('%H:%M')}")
                if current.get("location"):
                    click.echo(f"   Location: {current['location']}")
            else:
                click.echo("📍 Current: No active meeting")

            # Upcoming meeting
            upcoming = matcher.find_upcoming_meeting(meeting_path)
            if upcoming:
                mins_until = (
                    upcoming["start_time"] - datetime.now(timezone.utc)
                ).total_seconds() / 60
                click.echo(
                    f"🔜 Next: {upcoming['title']} (in {int(mins_until)} minutes)"
                )

            # Recent meeting
            recent = matcher.find_recent_meeting(meeting_path)
            if recent:
                click.echo(f"🕐 Recent: {recent['title']}")
        else:
            click.echo("No meeting notes found")
    except Exception as e:
        click.echo(f"Unable to check meetings: {e}")


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
