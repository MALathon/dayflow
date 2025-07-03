---
name: Feature Request - Daily Notes Organization
about: Add folder organization support for daily notes
title: 'feat: Add folder organization for daily notes'
labels: enhancement
assignees: ''
---

## Problem
Currently, daily notes are all stored in a flat "Daily Notes" folder, while calendar events can be organized by date (year/month/day). This inconsistency makes it harder to navigate daily summaries over time.

## Proposed Solution
Add a configuration option to organize daily notes using the same folder patterns as calendar events:

```yaml
calendar:
  folder_organization: year/month/day
  daily_notes_organization: year/month  # New option
```

## Implementation Notes
1. Update `VaultConnection.write_note()` to check if the note type is "daily_notes" and apply folder organization
2. Add new config option `calendar.daily_notes_organization`
3. Support the same patterns: `year/month/day`, `year/week`, `year/month`
4. Default to flat structure for backward compatibility

## Example Structure
```
Daily Notes/
├── 2025/
│   ├── 01/
│   │   ├── 2025-01-15 Daily Summary.md
│   │   ├── 2025-01-16 Daily Summary.md
│   │   └── 2025-01-17 Daily Summary.md
│   └── 02/
│       ├── 2025-02-01 Daily Summary.md
│       └── 2025-02-02 Daily Summary.md
```

## Benefits
- Consistent organization between calendar events and daily notes
- Easier navigation for historical summaries
- Scalable for long-term use
