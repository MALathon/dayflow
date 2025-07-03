# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Pretty CLI Output**: Enhanced visual feedback throughout the application
  - Progress bars that update in place instead of creating new lines
  - Unicode box drawing for status summaries
  - Color-coded status indicators
  - Terminal width detection with graceful fallback
  - Pretty sync summaries with emoji indicators

### Changed
- Continuous sync mode now uses pretty progress indicators
- Status command displays information in structured boxes
- Sync progress shows visual progress bars with percentages
- Error messages are displayed with proper formatting

### Fixed
- Progress bars no longer create multiple lines of output
- Fixed import error for `read_sync_status` in CLI status command

## [0.1.0] - 2025-07-02

### Added
- **Calendar Sync**: Sync Microsoft 365 calendar events to Obsidian vault
  - Manual token authentication via Microsoft Graph Explorer
  - Date range support for targeted syncing
  - Event filtering and deduplication
  - HTML to Markdown conversion for meeting descriptions

- **Vault Management**: Flexible Obsidian vault configuration
  - Auto-detection of existing Obsidian vaults
  - Support for multiple vault structures (PARA, GTD, time-based, Zettelkasten)
  - Interactive setup wizard
  - Configurable folder organization (year/month/day, year/week, year/month)
  - Time-prefixed note naming (HHMM format)

- **Note Creation**: Smart note generation with meeting context
  - Quick note command with automatic meeting linking
  - Multiple note templates (meeting, idea, task, reference)
  - Current meeting detection and tracking
  - Upcoming meeting awareness (5-minute lookahead)
  - Rich frontmatter with metadata

- **Daily Summaries**: Automatic daily overview generation
  - All meetings for the day with times and durations
  - Current meeting highlighting
  - Action items extraction
  - Key decisions summary
  - Time-ordered meeting list

- **GTD System**: Getting Things Done workflow support
  - Inbox management for capturing tasks
  - Basic processing workflow
  - Weekly review generator
  - Project and context support

- **Zettelkasten**: Knowledge management system
  - Permanent, literature, and fleeting notes
  - Unique ID generation
  - Literature note processing
  - Note search functionality
  - Suggestions for unprocessed notes

### Technical
- Cross-platform support (Windows, macOS, Linux)
- Python 3.8-3.12 compatibility
- UTF-8 encoding throughout for international support
- Comprehensive test suite with 75% coverage
- CI/CD pipeline with GitHub Actions
- Pre-commit hooks for code quality

### Changed
- Repository moved to MALathon/dayflow
- Updated all badges and URLs
- Fixed Python 3.8/3.9 compatibility issues

### Known Limitations
- Manual token refresh required (~24 hour expiry)
- No OAuth flow (uses Microsoft Graph Explorer tokens)
- Read-only calendar access
- No background sync service
- Limited to primary calendar

## [0.2.0] - 2025-07-02

### Added
- **Continuous Sync Mode**: Run `dayflow sync --continuous` for automatic background syncing
  - Configurable sync intervals (default: 10 minutes)
  - Graceful shutdown with Ctrl+C
  - Sync status persistence across sessions
  - Resume from previous session on restart

- **Progress Indicators**: Visual feedback during sync operations
  - "X of Y events" display during processing
  - Progress messages for each sync phase
  - Countdown timer for next sync in continuous mode
  - `--quiet` flag to suppress progress output for scripts

- **Enhanced Token Management**:
  - Token refresh prompt when expired (instead of auto-opening browser)
  - Helpful guidance for authentication flow

- **Sync Status Tracking**:
  - Show last sync time in `dayflow status` command
  - Track sync count and error count
  - Persistent status file (`~/.dayflow/sync_status.json`)

### Changed
- Default sync interval changed from 5 to 10 minutes for continuous mode
- Token expiration documentation updated from ~1 hour to ~24 hours
- CalendarSyncEngine now supports progress callbacks

### Fixed
- Python 3.8/3.9 compatibility issues in tests
- Test hanging issues with proper mocking
- CLI test mocking for continuous sync functionality

## [0.0.9] - 2025-07-02 (Pre-release)

### Added
- Date-based folder organization for calendar events
- Time-prefixed filenames for chronological ordering within folders
- Current meeting identification and tracking
- Live "Current Meeting.md" shortcut in vault root
- Visual indicators for current meetings in daily summaries
- Configurable folder patterns (year/month/day, year/week, year/month)
- Local GitHub Actions testing with `act`
- Comprehensive testing documentation

### Changed
- Repository structure cleaned up to professional standards
- Documentation reorganized and consolidated
- Removed test file creation from vault setup wizard
- Improved Windows compatibility with UTF-8 encoding throughout

### Enhanced
- Daily summaries now highlight current meetings with "⏰ **NOW**" indicator
- ObsidianNoteFormatter supports both flat and hierarchical file organization
- VaultConnection handles dynamic folder creation based on event dates
- Current meeting detection prioritizes non-all-day events
- Test suite performance improvements with proper mocking

### Fixed
- Attendee names showing as "Unknown" in daily summaries
- Proper handling of Microsoft Graph API attendee structure
- Test isolation issues in config commands
- Current meeting selection logic for all-day vs regular events
- Windows path compatibility in tests

## [0.0.1] - 2024-01-16 (Initial development)

### Added
- Initial release with basic calendar synchronization
- Manual authentication via Microsoft Graph Explorer
- Calendar event sync from Microsoft 365 to Obsidian
- Meeting detection based on current time
- Quick note creation with automatic meeting linking
- Note templates (meeting, idea, task, reference)
- Daily summary generation with meeting overview
- Interactive vault setup wizard
- Support for PARA, GTD, and time-based folder structures
- Comprehensive test suite (172 tests)

### Features
- `dayflow auth login/logout/status` - Authentication management
- `dayflow sync` - Sync calendar events with date range options
- `dayflow note` - Create notes with meeting context
- `dayflow vault setup` - Interactive vault configuration
- `dayflow status` - System health and meeting context

### Technical
- Graph API client with pagination and error handling
- Flexible vault configuration system
- Meeting matcher for intelligent time-based linking
- Daily summary generator with backlinks
- Timezone-aware datetime handling

### Known Limitations
- Manual token refresh required (tokens expire ~24 hours)
- Read-only calendar access
- No continuous sync
- Limited to primary calendar
