# Changelog

All notable changes to this project will be documented in this file.

## [0.1.1] - 2025-01-02

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

## [0.1.0] - 2024-01-16

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
- Manual token refresh required (tokens expire ~1 hour)
- Read-only calendar access
- No continuous sync
- Limited to primary calendar
