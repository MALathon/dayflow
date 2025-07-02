# Roadmap

## Current Status (v0.1.0)

### ✅ Implemented Features

#### Authentication & Calendar Sync
- Manual token authentication via Microsoft Graph Explorer
- Token storage and validation
- Basic sync command with date range support
- Graph API client for fetching calendar events
- Sync engine with event filtering
- Support for custom date ranges

#### Vault Management
- Vault configuration system with YAML storage
- Vault detector for finding Obsidian vaults
- Vault structure templates (PARA, GTD, time-based, Zettelkasten, custom)
- Interactive setup wizard
- Vault validation
- Folder organization support (year/month/day, year/week, year/month)
- Time-prefixed note naming (HHMM format)

#### Note Creation
- Obsidian note formatter with frontmatter
- Calendar event notes with proper metadata
- Daily summary notes with current meeting highlighting
- Quick note command with automatic meeting context detection
- Note templates (meeting, idea, task, reference)
- HTML to Markdown conversion for meeting descriptions
- Current meeting tracking and management

#### GTD System
- GTD inbox management
- Process inbox items (basic interactive mode)
- Weekly review generator

#### Zettelkasten
- Create permanent, literature, and fleeting notes
- Unique ID generation
- Literature note processing
- Note search functionality
- Suggestions for permanent notes

#### Configuration & Commands
- Config show/edit/reset commands
- Get/set specific config values
- YAML-based configuration
- Status command showing system health
- Version command
- Help system

#### Test Coverage
- **Total Tests**: 249 passing
- **Code Coverage**: 75% overall
- **Core Modules**: High coverage (>90% for most)
- **Windows Compatibility**: Full UTF-8 encoding support

### 🚧 Current Limitations
- Manual token refresh required (~24 hour expiry)
- Read-only calendar access
- Limited to personal calendar
- No automated OAuth flow (manual token entry only)
- No conflict resolution
- No dry-run mode for sync
- No progress indicators for long operations

### 💡 Quick Start

```bash
# Initial setup
dayflow vault setup        # Interactive vault configuration
dayflow auth login         # Manual token authentication

# Daily usage
dayflow sync               # Sync today's events
dayflow sync --continuous  # Run continuous sync during workday (10 min intervals)
dayflow sync --start 2024-01-01 --end 2024-01-07  # Sync date range
dayflow note -t "Meeting notes"  # Create quick note with meeting context

# GTD workflow
dayflow gtd inbox --add "Call Bob about project"
dayflow gtd process        # Process inbox items
dayflow gtd review --generate  # Create weekly review

# Zettelkasten
dayflow zettel new -t "Key insight about X"
dayflow zettel literature -t "Notes on Article" -s "Article Title" -a "Author"
dayflow zettel suggest     # Find unprocessed literature notes
```

## Phase 2: Enhanced Sync (v0.2.0) - IN PROGRESS

### Continuous Sync - COMPLETED ✅
- [x] Implement sync daemon with graceful shutdown
- [x] Configurable sync intervals (default 10 minutes)
- [x] Sync status tracking and persistence
- [x] Show sync status in `dayflow status` command
- [x] Helpful prompt when token expires during sync

### Progress Indicators - COMPLETED ✅
- [x] Add progress messages for sync operations
- [x] Show "X of Y events" during sync
- [x] Add countdown timer for next sync in continuous mode
- [x] Add --quiet flag for scripts

## Phase 3: Enhanced Sync & Token Management (v0.3.0)

### Enhanced Manual Token Management
- [ ] Token expiry monitoring with proactive warnings
- [ ] Token refresh reminders (configurable alerts)
- [ ] Multiple token storage (work/personal accounts)
- [ ] Token validation on startup with clear error messages

### Pseudo-Continuous Sync
- [ ] Scheduled sync setup guides (cron/Task Scheduler)
- [ ] File watcher for manual sync triggers
- [ ] Incremental sync to minimize API calls
- [ ] Smart sync intervals based on calendar patterns

### Background Sync Service (Local)
- [ ] Local daemon for periodic syncs
- [ ] System tray application for sync status
- [ ] Offline change queue for later sync
- [ ] Conflict detection and resolution

### Sync Status Indicators
- [ ] `.sync_status` file tracking in vault
- [ ] Status badges in daily notes
- [ ] Comprehensive sync history log
- [ ] Error tracking with actionable messages

## Phase 4: GTD Integration (v0.4.0)

### Task Extraction
- [ ] Extract action items from meeting notes
- [ ] Create GTD inbox entries
- [ ] Parse due dates and contexts
- [ ] Link tasks to source meetings

### GTD Workflow Commands
- [ ] Complete `dayflow gtd process` implementation
- [ ] `dayflow gtd review` - Weekly review helper
- [ ] Project/task tracking
- [ ] Waiting-for automation

## Phase 4: Intelligence Features (v0.4.0)

### Meeting Intelligence
- [ ] Meeting preparation notes
- [ ] Agenda parsing
- [ ] Follow-up detection
- [ ] Meeting series handling

### Smart Suggestions
- [ ] Related notes discovery
- [ ] Participant history
- [ ] Topic clustering
- [ ] Meeting insights

## Phase 5: Collaboration (v0.5.0)

### Team Features
- [ ] Shared calendar support
- [ ] Team member note linking
- [ ] Collaborative summaries
- [ ] Permission management

### Integration
- [ ] Microsoft Teams integration
- [ ] Email thread linking
- [ ] Document attachment handling
- [ ] OneNote migration tools

## Phase 6: Advanced Features (v1.0.0)

### Voice & AI
- [ ] Meeting transcription
- [ ] Voice note capture
- [ ] AI-powered summaries
- [ ] Smart action extraction

### Analytics
- [ ] Meeting time analytics
- [ ] Productivity insights
- [ ] Calendar optimization
- [ ] Time tracking

## Technical Debt & Improvements

### Code Quality
- [ ] Add type hints throughout
- [ ] Improve error messages
- [ ] Add logging framework
- [ ] Performance optimization

### Testing
- [ ] Integration test suite
- [ ] End-to-end tests
- [ ] Performance benchmarks
- [ ] Security testing

### Documentation
- [ ] API documentation
- [ ] Video tutorials
- [ ] Migration guides
- [ ] Troubleshooting guide

### Platform Support
- [ ] Windows testing and fixes
- [ ] Linux compatibility
- [ ] Package for Homebrew
- [ ] Docker image for containerized deployment

## Community Features

### Extensibility
- [ ] Plugin architecture
- [ ] Custom formatter API
- [ ] Webhook support
- [ ] Template marketplace

### Integrations
- [ ] Google Calendar support
- [ ] Notion export
- [ ] Roam Research sync
- [ ] CalDAV protocol

## Research & Exploration

### Potential Features
- Voice command interface
- Mobile companion app
- Browser extension
- Obsidian plugin version
- Multi-language support

### Enterprise Features
- SSO integration
- Audit logging
- Compliance tools
- Bulk provisioning

## Release Schedule

- **v0.1.0** - Current release (basic sync)
- **v0.2.0** - Q1 2024 (enhanced sync)
- **v0.3.0** - Q2 2024 (GTD integration)
- **v0.4.0** - Q3 2024 (intelligence)
- **v0.5.0** - Q4 2024 (collaboration)
- **v1.0.0** - 2025 (full feature set)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to contribute to these goals.
