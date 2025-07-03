---
name: Configurable Folder Display Format
about: Allow users to configure how date-based folders are displayed
title: 'feat: Add configurable folder display formats (numbers vs names)'
labels: enhancement, vault, ui
assignees: ''

---

## Description

Currently, date-based folder organization uses numeric formats (e.g., `2024/01/15`). Users should be able to configure how these folders are displayed, such as using month names, day names, or custom formats.

## Current Behavior

- Folders are always created with zero-padded numbers:
  - Year: `2024`
  - Month: `01`, `02`, ... `12`
  - Day: `01`, `02`, ... `31`
  - Week: `W01`, `W02`, ... `W52`

## Desired Behavior

Allow users to configure folder display formats:

### Month Formats
- Numeric: `01`, `02`, ... `12` (current)
- Short name: `Jan`, `Feb`, ... `Dec`
- Full name: `January`, `February`, ... `December`
- Custom prefix: `01-Jan`, `02-Feb`, etc.

### Day Formats
- Numeric: `01`, `02`, ... `31` (current)
- With weekday: `15-Mon`, `16-Tue`, etc.
- Ordinal: `1st`, `2nd`, `3rd`, ... `31st`

### Week Formats
- ISO week: `W01`, `W02`, ... `W52` (current)
- Week of: `Week-01`, `Week-02`, etc.
- Date range: `Jan-08-14`, `Jan-15-21`, etc.

## Proposed Implementation

### 1. New Configuration Settings

```yaml
calendar:
  folder_organization: "year/month/day"
  folder_display:
    month_format: "short_name"  # numeric, short_name, full_name, numeric_name
    day_format: "numeric"        # numeric, with_weekday, ordinal
    week_format: "iso"           # iso, prefixed, date_range
    locale: "en_US"              # For localized month/day names
```

### 2. CLI Commands

```bash
# View current folder display settings
dayflow config folder-display

# Set month format
dayflow config folder-display --month-format short_name

# Set all formats at once
dayflow config folder-display --month-format full_name --day-format with_weekday

# List available format options
dayflow config folder-display --list-formats
```

### 3. Interactive Configuration

Add to the setup wizard:
```
How would you like months to be displayed in folders?
1. Numbers (01, 02, ..., 12)
2. Short names (Jan, Feb, ..., Dec)
3. Full names (January, February, ..., December)
4. Number + Name (01-Jan, 02-Feb, ..., 12-Dec)
>
```

## Example Folder Structures

### Current (all numeric):
```
Calendar/
  2024/
    01/
      15/
        0900 - Team Meeting.md
```

### With short month names:
```
Calendar/
  2024/
    Jan/
      15/
        0900 - Team Meeting.md
```

### With full names and weekdays:
```
Calendar/
  2024/
    January/
      15-Mon/
        0900 - Team Meeting.md
```

### With week date ranges:
```
Calendar/
  2024/
    Jan-08-14/
      0900 - Team Meeting.md
```

## Technical Considerations

### 1. Localization Support
- Use Python's locale module for month/day names
- Support for different languages (e.g., "janvier" for January in French)
- Handle cultures with different calendar systems

### 2. Sorting Preservation
- Ensure folders still sort chronologically
- May need numeric prefixes for text-based formats

### 3. Migration Handling
- Changing display format should migrate existing folders
- Or support multiple format recognition for backwards compatibility

### 4. Path Length Limits
- Consider OS path length limits with longer names
- Provide warnings for potentially problematic configurations

## Benefits

1. **Better Readability**: Month/day names are more human-friendly than numbers
2. **Localization**: Support for international users
3. **Flexibility**: Users can choose what works best for their workflow
4. **Visual Organization**: Easier to navigate in file explorers

## Future Enhancements

- Custom format strings (e.g., strftime-like syntax)
- Conditional formatting based on date (e.g., different format for current month)
- Emoji support (e.g., 📅 prefix for current week)
