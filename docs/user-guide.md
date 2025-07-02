# Dayflow User Guide

## Installation

```bash
# Clone the repository
git clone https://github.com/malathon/dayflow.git
cd dayflow

# Install the package
pip install -e .
```

## Initial Setup

### 1. Vault Configuration

Run the interactive setup wizard:

```bash
dayflow vault setup
```

The wizard will:
- Automatically detect your Obsidian vaults
- Show your existing folder structure
- Suggest appropriate locations for calendar events
- Create necessary folders
- Test the configuration

#### Manual Configuration

If you prefer manual setup:

```bash
# Set vault path
dayflow vault set-path /path/to/your/vault

# Set specific folder locations
dayflow vault set-location calendar_events "Calendar Events"
dayflow vault set-location daily_notes "Daily Notes"
```

### 2. Authentication

Dayflow uses Microsoft Graph Explorer for authentication:

```bash
dayflow auth login
```

This will:
1. Open Microsoft Graph Explorer in your browser
2. Guide you to copy your access token
3. Store the token securely

**Note**: Tokens expire after ~24 hours and need to be refreshed manually.

## Daily Usage

### Syncing Calendar Events

```bash
# Sync today's events (default: yesterday to 7 days ahead)
dayflow sync

# Sync specific date range
dayflow sync --start 2024-01-01 --end 2024-01-31

# Skip daily summary generation
dayflow sync --no-daily-summary
```

### Creating Notes

```bash
# Create a quick note (auto-detects current meeting)
dayflow note -t "Meeting Notes"

# Use a specific template
dayflow note -t "Project Update" -T meeting

# Open in your default editor
dayflow note -t "Ideas" -e

# Don't link to current meeting
dayflow note -t "Personal Note" --no-link-meeting
```

### Available Templates
- `meeting` - Meeting notes with attendees, agenda, action items
- `idea` - Quick idea capture with context
- `task` - Task note with priority and due date
- `reference` - Reference material with source info

## Vault Organization

### Supported Structures

#### PARA Method
```
/
├── 1-Projects/
├── 2-Areas/
├── 3-Resources/
│   ├── Meeting Notes/      # Calendar events
│   └── Daily Notes/        # Daily summaries
└── 4-Archives/
```

#### GTD (Getting Things Done)
```
/
├── 00-Inbox/
├── 01-Next Actions/
├── 02-Projects/
├── 03-Waiting For/
├── 04-Someday Maybe/
└── 05-Reference/
    ├── Meeting Notes/      # Calendar events
    └── Daily Notes/        # Daily summaries
```

#### Time-Based
```
/
├── 2024/
│   ├── 01-January/
│   │   ├── Meetings/       # January meetings
│   │   └── Daily Notes/    # January daily summaries
│   └── 02-February/
│       ├── Meetings/
│       └── Daily Notes/
```

### Folder Organization Feature

Enable date-based folder organization by editing `~/.dayflow/config.yaml`:

```yaml
calendar:
  folder_organization: year/month/day  # or year/week, year/month
```

This creates:
- Year/month/day folder hierarchy
- Time-prefixed notes (e.g., "0900 - Team Meeting.md")
- "Current Meeting.md" shortcut in vault root
- Current meeting highlighting in daily summaries

## GTD Workflow

### Managing Your Inbox

```bash
# Add items to inbox
dayflow gtd inbox --add "Call Bob about project"
dayflow gtd inbox --add "Review Q4 budget"

# View inbox
dayflow gtd inbox

# Process inbox items interactively
dayflow gtd process
```

### Weekly Review

```bash
# Generate weekly review template
dayflow gtd review --generate

# View last week's completed items
dayflow gtd review
```

## Zettelkasten Features

### Creating Notes

```bash
# Create a permanent note
dayflow zettel new -t "Key insight about productivity"

# Create a literature note
dayflow zettel literature -t "Notes on Deep Work" -s "Deep Work" -a "Cal Newport"

# Create a fleeting note
dayflow zettel fleeting -t "Random thought about workflows"
```

### Finding Notes

```bash
# Search all Zettelkasten notes
dayflow zettel search "productivity"

# Find literature notes needing processing
dayflow zettel suggest
```

## Configuration Management

### Viewing Configuration

```bash
# Show full configuration
dayflow config show

# Get specific value
dayflow config get vault.path
dayflow config get calendar.folder_organization
```

### Editing Configuration

```bash
# Open in default editor
dayflow config edit

# Set specific value
dayflow config set calendar.folder_organization "year/month/day"
dayflow config set calendar.default_reminder 15
```

### Reset Configuration

```bash
# Reset to defaults (prompts for confirmation)
dayflow config reset

# Force reset without confirmation
dayflow config reset --force
```

## Troubleshooting

### Authentication Issues

```bash
# Check token status
dayflow auth status

# If expired, refresh token
dayflow auth login
```

### Vault Issues

```bash
# Validate vault configuration
dayflow vault validate

# Check current status
dayflow vault status
```

### Common Problems

**"Vault not found"**
- Ensure the path exists
- Check for `.obsidian` folder in vault root

**"Permission denied"**
- Check folder write permissions
- Run from a location with vault access

**"Token expired"**
- Tokens expire after ~24 hours
- Run `dayflow auth login` to refresh

## Best Practices

1. **Backup Your Vault**: Always backup before initial sync
2. **Start Small**: Test with a limited date range first
3. **Use Templates**: Leverage note templates for consistency
4. **Regular Syncs**: Run sync daily for best results
5. **Organize by Date**: Enable folder organization for better structure

## Advanced Usage

### Custom Date Ranges

```bash
# Sync just this week
dayflow sync --start monday --end friday

# Sync last month
dayflow sync --start "2024-01-01" --end "2024-01-31"
```

### Multiple Vaults

Switch between vaults:

```bash
# Check current vault
dayflow vault status

# Switch to different vault
dayflow vault setup
# Or directly set path
dayflow vault set-path /path/to/other/vault
```

## Need Help?

- Run `dayflow --help` for command list
- Run `dayflow <command> --help` for command details
- Check [ROADMAP.md](../ROADMAP.md) for upcoming features
- Report issues on [GitHub](https://github.com/malathon/dayflow/issues)
