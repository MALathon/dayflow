---
name: Comprehensive Folder Organization Configuration
about: Create dedicated configuration section for all folder organization options
title: 'feat: Add comprehensive folder organization configuration section'
labels: enhancement, vault, configuration
assignees: ''

---

## Description

Create a dedicated configuration section for folder organization that consolidates all folder-related settings and adds new customization options. Currently, folder settings are scattered and limited.

## Current State

```yaml
calendar:
  folder_organization: year/month/day  # Only option, hardcoded format
```

## Proposed Configuration Structure

```yaml
folder_organization:
  # Enable/disable folder organization
  enabled: true

  # Organization patterns
  calendar_events:
    pattern: "year/month/day"
    formats:
      year: "YYYY"                    # 2024
      month: "MM-MMM"                 # 01-Jan
      day: "DD-ddd"                   # 15-Mon
      week: "week-WW"                 # week-03

  daily_notes:
    pattern: "year/month"
    formats:
      year: "YYYY"
      month: "MMMM"                   # January

  # Global format settings
  formats:
    locale: "en_US"                   # For month/day names
    week_start: "monday"              # or "sunday"
    timezone: "America/Chicago"       # For date calculations

  # File naming
  file_naming:
    time_prefix: true                 # Add HHMM prefix
    time_format: "24h"                # or "12h" for 09:00 AM
    separator: " - "                  # Between time and title
    date_in_filename: false           # Include date in filename

  # Note title format
  note_titles:
    include_date: true
    date_format: "YYYY-MM-DD"
    include_weekday: true             # "2024-01-15 (Monday)"

  # Migration settings
  migration:
    auto_migrate: false               # Auto-migrate on change
    backup_before_migrate: true
    preserve_old_structure: false     # Keep old files
```

## Format Tokens

Support standard date format tokens:

### Date Components
- `YYYY` - 4-digit year (2024)
- `YY` - 2-digit year (24)
- `MM` - 2-digit month (01-12)
- `M` - Month without padding (1-12)
- `MMM` - Short month name (Jan)
- `MMMM` - Full month name (January)
- `DD` - 2-digit day (01-31)
- `D` - Day without padding (1-31)
- `Do` - Day with ordinal (1st, 2nd, 3rd)
- `ddd` - Short weekday (Mon)
- `dddd` - Full weekday (Monday)
- `WW` - 2-digit week (01-52)
- `W` - Week without padding (1-52)

### Custom Combinations
- `MM-MMM` → "01-Jan"
- `MMMM YYYY` → "January 2024"
- `DD-ddd` → "15-Mon"
- `Week WW of YYYY` → "Week 03 of 2024"

## CLI Commands

```bash
# Show folder organization config
dayflow config folder-org show

# Enable folder organization
dayflow config folder-org enable

# Set pattern for calendar events
dayflow config folder-org set calendar_events.pattern "year/month/day"

# Set month format
dayflow config folder-org set calendar_events.formats.month "MMMM"

# Set multiple options
dayflow config folder-org set --json '{
  "calendar_events": {
    "pattern": "year/month",
    "formats": {
      "month": "MM-MMM"
    }
  }
}'

# Preview changes (dry run)
dayflow config folder-org preview

# Apply changes with migration
dayflow config folder-org apply --migrate

# Interactive configuration wizard
dayflow config folder-org setup
```

## Implementation Phases

### Phase 1: Core Configuration
- Create new config section
- Implement format token parser
- Update VaultConnection to use new settings

### Phase 2: Format Support
- Implement all date format tokens
- Add localization support
- Handle timezone conversions

### Phase 3: Migration Tools
- Implement folder migration logic
- Add dry-run preview
- Create backup/restore functionality

### Phase 4: CLI Interface
- Add all CLI commands
- Create interactive setup wizard
- Add validation and error handling

## Benefits

1. **Centralized Configuration**: All folder settings in one place
2. **Flexibility**: Support for any date format combination
3. **Consistency**: Same configuration approach for all content types
4. **Future-Proof**: Easy to add new options
5. **User-Friendly**: Interactive setup and preview options

## Example Use Cases

### Academic User
```yaml
folder_organization:
  calendar_events:
    pattern: "year/semester/week"
    formats:
      semester: "['Spring', 'Summer', 'Fall'][quarter]"
      week: "Week-WW"
```

### International User (French)
```yaml
folder_organization:
  formats:
    locale: "fr_FR"
  calendar_events:
    formats:
      month: "MMMM"  # "janvier", "février", etc.
```

### Project-Based Organization
```yaml
folder_organization:
  calendar_events:
    pattern: "year/quarter/project"
    formats:
      quarter: "Q[quarter]"
```

## Testing Requirements

- Unit tests for format token parsing
- Integration tests for folder creation
- Migration tests with various scenarios
- Localization tests for different locales
- Performance tests for large vaults
