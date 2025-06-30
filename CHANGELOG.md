# Changelog

All notable changes to this project will be documented in this file.

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