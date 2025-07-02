# Dayflow

[![Tests](https://github.com/MALathon/dayflow/actions/workflows/tests.yml/badge.svg)](https://github.com/MALathon/dayflow/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/MALathon/dayflow/branch/main/graph/badge.svg)](https://codecov.io/gh/MALathon/dayflow)
[![Python Version](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)

An intelligent calendar workflow system that synchronizes Microsoft 365 calendar events to Obsidian notes, with smart meeting detection and daily summaries.

## Features

- 📅 **Calendar Sync**: Automatically sync Microsoft 365 calendar events to Obsidian
- 🔍 **Smart Meeting Detection**: Links notes to current/upcoming meetings based on time
- 📝 **Quick Notes**: Create notes with templates and automatic meeting context
- 📊 **Daily Summaries**: Automatic daily overview with all meetings and action items
- 🏗️ **Flexible Vault Structure**: Support for PARA, GTD, time-based, and custom folder structures
- 📁 **Date-Based Organization**: Optional year/month/day folder hierarchy for calendar events
- ⏰ **Current Meeting Tracking**: Live shortcut to current meeting with status updates
- 🕐 **Time-Ordered Notes**: Meeting notes sorted by time within day folders

## Quick Start

### Prerequisites

- Python 3.8+
- Obsidian vault
- Microsoft 365 account (works with enterprise environments where admin access is difficult to obtain or unwanted)

### Installation

```bash
# Clone the repository
git clone https://github.com/MALathon/dayflow.git
cd dayflow

# Install the package
pip install -e .
```

### Basic Usage

1. **Set up your vault**:
   ```bash
   dayflow vault setup
   ```

2. **Authenticate** (uses Microsoft Graph Explorer):
   ```bash
   dayflow auth login
   ```

3. **Sync your calendar**:
   ```bash
   dayflow sync
   ```

4. **Create a quick note**:
   ```bash
   dayflow note -t "Meeting Notes"
   ```

### Enable Folder Organization (Optional)

To organize calendar events by date, add to your config:

```bash
# Edit ~/.dayflow/config.yaml
calendar:
  folder_organization: year/month/day
```

This will:
- Create year/month/day folders automatically
- Prefix notes with time (e.g., "0900 - Team Meeting.md")
- Maintain a "Current Meeting.md" shortcut in your vault root
- Highlight current meetings in daily summaries

## Documentation

- [User Guide](docs/user-guide.md) - Complete usage instructions
- [Architecture](docs/ARCHITECTURE.md) - Technical architecture overview
- [Contributing](CONTRIBUTING.md) - Development setup and guidelines
- [Roadmap](ROADMAP.md) - Future features and development plans
- [Examples](docs/examples/) - Code examples and integration guides

## Quick Command Reference

### Authentication
- `dayflow auth login` - Authenticate with Microsoft Graph
- `dayflow auth status` - Check authentication status
- `dayflow auth logout` - Remove stored token

### Calendar Sync
- `dayflow sync` - Sync calendar events (default: yesterday to 7 days ahead)
- `dayflow sync --start 2024-01-01 --end 2024-01-31` - Sync specific date range
- `dayflow sync --no-daily-summary` - Skip daily summary generation

### Note Creation
- `dayflow note -t "Title"` - Create a quick note
- `dayflow note -t "Title" -T meeting` - Use meeting template
- `dayflow note -t "Title" -e` - Open in editor
- `dayflow note -t "Title" --no-link-meeting` - Don't link to current meeting

### Vault Management
- `dayflow vault setup` - Interactive vault setup wizard
- `dayflow vault status` - Show current configuration
- `dayflow config show` - Display full configuration

### System Status
- `dayflow status` - Show authentication, vault, and meeting context

## Configuration

Configuration is stored in `~/.dayflow/config.yaml`:

```yaml
vault:
  path: /path/to/your/obsidian/vault
  locations:
    calendar_events: Calendar Events
    daily_notes: Daily Notes

# Optional: Enable folder organization
calendar:
  folder_organization: year/month/day  # Options: year/month/day, year/week, year/month
```

## Folder Organization

When `folder_organization` is configured, calendar events are organized into date-based folders:

### Year/Month/Day Structure
```
Calendar Events/
├── 2025/
│   ├── 01/
│   │   ├── 15/
│   │   │   ├── 0900 - Morning Standup.md
│   │   │   ├── 1100 - Project Review.md
│   │   │   └── 1400 - Team Workshop.md
│   │   └── 16/
│   │       └── 1000 - Planning Session.md
```

### Features
- **Time Prefixes**: Notes are prefixed with HHMM for chronological ordering
- **All-Day Events**: Prefixed with "0000" to appear first
- **Current Meeting Shortcut**: A "Current Meeting.md" file in vault root links to the active meeting
- **Daily Summaries**: Highlight current meetings with "⏰ **NOW**" indicator

### Configuration Options
- `year/month/day`: Full date hierarchy (recommended)
- `year/week`: Weekly folders (e.g., 2025/W03)
- `year/month`: Monthly folders without day separation

## Architecture

The system consists of three main components:

1. **Core**: Handles calendar sync, meeting detection, and note formatting
2. **Vault**: Manages Obsidian vault configuration and file operations
3. **UI**: Provides the command-line interface

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed technical information.

## Development

### Running Tests

```bash
# Quick test run (excludes TDD tests)
make test

# Run full CI/CD checks locally (exactly as GitHub Actions)
make test-ci

# Run all checks: format, lint, type, and tests
make test-all

# Test with GitHub Actions locally using act
make test-act           # Ubuntu + Python 3.11
make test-act-windows   # Windows + Python 3.11
make test-act-macos     # macOS + Python 3.11

# Run specific test categories
make test-unit          # Unit tests only
make test-integration   # Integration tests
make test-cli          # CLI tests

# Run with coverage
make test-cov
```

See `make help` for all available commands.

### Project Structure

```
dayflow/
├── core/           # Calendar sync and processing
├── vault/          # Obsidian vault management
└── ui/             # CLI interface

tests/              # Comprehensive test suite
docs/               # Documentation and examples
```

## Limitations

- Requires manual token refresh (tokens expire after ~1 hour)
- Read-only calendar access (cannot create/modify events)
- Mayo Clinic: Requires manual token workflow due to security policies

## Future Roadmap

- Continuous sync with automatic token refresh
- GTD task processing
- Zettelkasten note management
- Team collaboration features

See [ROADMAP.md](ROADMAP.md) for detailed plans.

## License

This project is proprietary software. See [LICENSE](LICENSE) for details.
