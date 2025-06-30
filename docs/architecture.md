# Dayflow - Architecture

## Overview

The system synchronizes Microsoft 365 calendar events to an Obsidian vault, providing intelligent meeting detection and note management capabilities.

## Core Components

### 1. Graph API Client (`core/graph_client.py`)

Handles Microsoft Graph API communication:
- Fetches calendar events with pagination support
- Normalizes event data structure
- Handles authentication errors and rate limiting

```python
client = GraphAPIClient(access_token)
events = client.fetch_calendar_events(start_date, end_date)
```

### 2. Calendar Sync Engine (`core/sync.py`)

Orchestrates the synchronization process:
- Manages sync workflow
- Creates/updates meeting notes
- Generates daily summaries
- Tracks sync statistics

```python
engine = CalendarSyncEngine(access_token, vault_connection)
result = engine.sync(start_date, end_date)
```

### 3. Meeting Matcher (`core/meeting_matcher.py`)

Intelligent meeting detection based on time:
- Finds current meeting (happening now)
- Detects upcoming meetings (within 15 minutes)
- Identifies recent meetings (within 30 minutes)
- Parses meeting notes for time information

```python
matcher = MeetingMatcher(vault_path)
current = matcher.find_current_meeting(meeting_notes_path)
```

### 4. Daily Summary Generator (`core/daily_summary.py`)

Creates comprehensive daily overview notes:
- Groups meetings by time of day
- Links to individual meeting notes
- Creates action item summaries
- Provides daily reflection sections

### 5. Obsidian Note Formatter (`core/obsidian_formatter.py`)

Formats calendar events as Obsidian notes:
- YAML frontmatter with metadata
- Markdown formatting
- Wiki links for attendees
- Action item templates

## Vault Management

### Vault Configuration (`vault/config.py`)

Manages vault settings and folder structures:
- Supports multiple organization templates (PARA, GTD, time-based)
- Validates vault accessibility
- Provides location mapping

### Vault Connection (`vault/connection.py`)

Handles file operations:
- Creates folders as needed
- Writes notes with proper paths
- Checks for existing notes

### Vault Detector (`vault/detector.py`)

Automatically finds Obsidian vaults:
- Searches common locations
- Validates .obsidian folder presence

### Setup Wizard (`vault/setup_wizard.py`)

Interactive configuration:
- Guides through vault selection
- Maps folder structures
- Tests write permissions

## CLI Interface (`ui/cli.py`)

Command-line interface using Click:
- Modular command groups (auth, sync, vault, config)
- Interactive prompts and confirmations
- Rich output formatting
- Error handling and user guidance

## Data Flow

```
1. User Authentication
   └── Manual token from Graph Explorer
       └── Stored in .graph_token

2. Calendar Sync
   ├── Fetch events from Graph API
   ├── Filter active events
   ├── Format as Obsidian notes
   ├── Write to vault folders
   └── Generate daily summaries

3. Quick Note Creation
   ├── Detect current meeting context
   ├── Apply note template
   ├── Link to meeting if applicable
   └── Save to appropriate folder
```

## Authentication Design

Due to Mayo Clinic security restrictions, we use a manual token workflow:

1. User opens Microsoft Graph Explorer
2. Signs in with enterprise credentials
3. Runs a test query to generate token
4. Copies token from the UI
5. CLI reads from clipboard and stores

This approach works around:
- Azure CLI blocking
- MSAL device code flow restrictions
- Corporate proxy requirements

## File Structure Patterns

### Meeting Notes
```
Calendar Events/
├── 2024-01-15 Team Standup.md
├── 2024-01-15 Budget Review.md
└── 2024-01-16 Project Planning.md
```

### Daily Summaries
```
Daily Notes/
├── 2024-01-15 Daily Summary.md
└── 2024-01-16 Daily Summary.md
```

### Note Metadata (Frontmatter)
```yaml
---
title: Team Standup
date: 2024-01-15
start_time: 2024-01-15T09:00:00
end_time: 2024-01-15T09:30:00
type: meeting
location: Conference Room A
attendees: [John Doe, Jane Smith]
tags: [calendar-event, team-standup]
---
```

## Extension Points

The architecture supports extensions through:

1. **Custom Formatters**: Subclass `ObsidianNoteFormatter`
2. **Additional Sync Sources**: Implement sync engine interface
3. **Vault Templates**: Add new organization structures
4. **CLI Commands**: Add new command groups

## Testing Strategy

- **Unit Tests**: Core components in isolation
- **Integration Tests**: Vault operations
- **CLI Tests**: Command behavior and user interaction
- **Mock Strategy**: Graph API and file system operations

Total test coverage: 172 tests across all components.