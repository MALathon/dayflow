# Dayflow Architecture

## Overview

Dayflow is a modular calendar workflow system designed to bridge Microsoft 365 calendar with Obsidian vaults. The architecture prioritizes flexibility, extensibility, and clean separation of concerns.

## Core Components

### 1. Core Module (`dayflow.core`)

The core module handles all calendar and note processing logic:

#### CalendarSyncEngine (`sync.py`)
- Central orchestrator for calendar synchronization
- Fetches events from Microsoft Graph API
- Coordinates note creation and daily summaries
- Integrates folder organization and current meeting tracking

#### GraphAPIClient (`graph_client.py`)
- Interfaces with Microsoft Graph API
- Handles authentication and API calls
- Normalizes event data into consistent format

#### ObsidianNoteFormatter (`obsidian_formatter.py`)
- Converts calendar events to Obsidian-compatible markdown
- Generates YAML frontmatter with event metadata
- Supports time-prefixed filenames for folder organization

#### DailySummaryGenerator (`daily_summary.py`)
- Creates daily overview notes
- Links to individual meeting notes
- Highlights current meetings with special indicators

#### CurrentMeetingManager (`current_meeting.py`)
- Identifies currently active meetings
- Maintains "Current Meeting.md" shortcut in vault root
- Provides meeting status (past, current, soon, future)

### 2. Vault Module (`dayflow.vault`)

Manages Obsidian vault configuration and file operations:

#### VaultConnection (`connection.py`)
- Abstracts file system operations
- Handles note reading/writing
- Implements folder organization logic
- Supports multiple vault structures

#### VaultConfig (`config.py`)
- Manages configuration file (~/.dayflow/config.yaml)
- Provides settings access with dot notation
- Supports vault location mappings

#### Structure Detector (`detector.py`)
- Analyzes existing vault structure
- Detects PARA, GTD, or time-based organization
- Suggests appropriate folder mappings

### 3. UI Module (`dayflow.ui`)

Command-line interface implementation:

#### CLI (`cli.py`)
- Click-based command structure
- Commands for auth, sync, note creation, vault management
- Rich terminal output with progress indicators

## Data Flow

```
Microsoft Graph API
        ↓
GraphAPIClient
        ↓
CalendarSyncEngine
        ↓
    ┌───┴───┐
    ↓       ↓
ObsidianNoteFormatter  DailySummaryGenerator
    ↓       ↓
VaultConnection ← CurrentMeetingManager
    ↓
Obsidian Vault
```

## Key Design Decisions

### 1. Folder Organization

The system supports multiple organization patterns:
- **Flat Structure**: All notes in single folder with date prefixes
- **Date Hierarchy**: Year/month/day folders with time-prefixed files
- **Weekly Organization**: Year/week folders
- **Monthly Organization**: Year/month folders

This is configured via `calendar.folder_organization` setting.

### 2. Current Meeting Tracking

The CurrentMeetingManager maintains a live link to the active meeting:
- Checks event start/end times against current time
- Updates "Current Meeting.md" shortcut during sync
- Integrates with daily summaries for visual indicators

### 3. Token Management

Due to Microsoft Graph Explorer limitations:
- Tokens must be manually obtained
- Tokens expire after ~24 hours
- Future versions will implement OAuth flow

### 4. Extensibility Points

The architecture provides several extension points:
- Custom vault structures via templates
- Additional note processors (GTD, Zettelkasten)
- Alternative calendar sources
- Plugin system for note templates

## Testing Strategy

### Unit Tests
- Individual component testing
- Mocked dependencies
- Edge case coverage

### Integration Tests
- End-to-end sync workflow
- Vault structure validation
- Current meeting identification

### Test-Driven Development
All features follow TDD methodology:
1. Write failing tests
2. Implement minimal code to pass
3. Refactor for clarity

## Future Architecture Considerations

### Continuous Sync
- Background service architecture
- Token refresh mechanism
- Event-driven updates

### Multi-Vault Support
- Vault profiles
- Per-vault configurations
- Cross-vault linking

### Plugin System
- Template marketplace
- Custom processors
- Third-party integrations
