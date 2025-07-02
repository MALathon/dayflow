# Roadmap

## Current Status (v0.1.0)

### ✅ Implemented
- Basic calendar synchronization from Microsoft 365
- Manual authentication workflow (Graph Explorer)
- Intelligent meeting detection and linking
- Quick note creation with templates
- Daily summary generation
- Flexible vault configuration
- Comprehensive test suite (172 tests)

### 🚧 Limitations
- Manual token refresh required (~1 hour expiry)
- Read-only calendar access
- No continuous sync
- Limited to personal calendar

## Phase 2: Enhanced Sync (v0.2.0)

### Automatic Token Management
- [ ] Implement token refresh mechanism
- [ ] Store refresh tokens securely
- [ ] Background token renewal
- [ ] Token expiry notifications

### Continuous Sync
- [ ] Implement sync daemon/service
- [ ] Configurable sync intervals
- [ ] Change detection to avoid duplicates
- [ ] System tray integration (optional)

### Sync Improvements
- [ ] Incremental sync (only changes)
- [ ] Conflict resolution
- [ ] Sync status reporting
- [ ] Multiple calendar support

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
- [ ] Docker container

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
