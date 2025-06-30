# Vault Setup Guide

This guide covers all scenarios for setting up Dayflow with your vault.

## Quick Setup (Recommended)

Run the interactive setup wizard:

```bash
dayflow vault setup
```

The wizard will:
1. Automatically detect your Obsidian vaults
2. Show your existing folder structure
3. Suggest appropriate locations for calendar events
4. Create necessary folders
5. Test the configuration

## Manual Setup

If you prefer manual configuration:

```bash
# Set vault path
dayflow vault set-path /path/to/your/vault

# Set specific folder locations
dayflow vault set-location calendar_events "Calendar Events"
dayflow vault set-location daily_notes "Daily Notes"
```

## Organization Templates

### PARA Method
```
/
├── 1-Projects/
├── 2-Areas/
├── 3-Resources/
│   ├── Meeting Notes/      # Calendar events go here
│   └── Daily Notes/        # Daily summaries
└── 4-Archives/
```

### GTD (Getting Things Done)
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

### Time-Based
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

### Custom Structure
Use any folder structure you prefer:

```bash
dayflow vault setup
# Select "Custom" when prompted
# Navigate and select your preferred folders
```

## For Existing Vaults

### Scenario 1: Clean Vault
If your vault has few folders, the wizard will:
- Show your current structure
- Suggest creating new folders
- Let you choose locations

### Scenario 2: Organized Vault
If you already have many folders:
- The wizard shows your folder tree
- You select where calendar events should go
- You select where daily summaries should go

### Scenario 3: Mixed Content
If you have calendar-related content:
- Put meeting notes in a dedicated subfolder
- Keep daily notes separate from calendar summaries
- Use tags to distinguish: `#calendar-sync`

## Configuration File

Settings are stored in `~/.dayflow/config.yaml`:

```yaml
vault:
  path: /Users/you/Documents/ObsidianVault
  locations:
    calendar_events: Calendar Events
    daily_notes: Daily Notes
    # Optional locations for future features:
    gtd_inbox: 00-Inbox
    gtd_projects: 02-Projects
```

## Folder Creation

The system will create folders as needed:
- Calendar events folder when first sync runs
- Daily notes folder when first summary is created
- Subfolders are created automatically

## Best Practices

1. **Dedicated Folders**: Keep calendar events in their own folder
2. **Consistent Naming**: Use the suggested naming patterns
3. **Backup First**: Always backup your vault before initial sync
4. **Start Small**: Test with a limited date range first

## Troubleshooting

### "Vault not found"
- Ensure the path exists
- Check for `.obsidian` folder in the vault root

### "Permission denied"
- Check folder write permissions
- Run from a location with vault access

### "Path does not exist"
- Use absolute paths, not relative
- Expand `~` to full home directory path

## Multiple Vaults

To switch between vaults:

```bash
# Check current vault
dayflow vault status

# Switch to different vault
dayflow vault setup
# Or
dayflow vault set-path /path/to/other/vault
```

## Validation

Always validate after setup:

```bash
dayflow vault validate
```

This checks:
- Vault path exists
- `.obsidian` folder present
- Configured folders accessible
- Write permissions available