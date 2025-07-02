# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dayflow is an intelligent calendar workflow system that synchronizes Microsoft 365 calendar events to Obsidian notes. It bridges enterprise calendar systems with personal knowledge management, supporting multiple vault organization structures (PARA, GTD, time-based).

## Development Commands

### Setup and Installation
```bash
# Install in development mode with all dependencies
pip install -e .
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Testing
```bash
# Quick test run (excludes TDD tests)
make test

# Run full CI/CD checks locally (exactly matches GitHub Actions)
make test-ci

# Run all checks: format, lint, type, and tests
make test-all

# Run specific test categories
make test-unit          # Unit tests (core + vault)
make test-integration   # Integration tests
make test-cli          # CLI tests
make test-cov          # With coverage report

# Test with GitHub Actions locally using act
make test-act          # Ubuntu + Python 3.11
make test-act-windows  # Windows + Python 3.11
make test-act-macos    # macOS + Python 3.11

# Run tests for all Python versions on specific OS
make test-act-all-ubuntu   # All Python versions on Ubuntu
make test-act-all-windows  # All Python versions on Windows
make test-act-all-macos    # All Python versions on macOS

# Direct pytest commands (if needed)
pytest -m "not tdd"                    # Exclude TDD tests
pytest -m ""                           # Include TDD tests
pytest -m integration                  # Only integration tests
pytest -v --durations=10               # Verbose with timing
pytest tests/core/test_sync_engine.py  # Single file
pytest tests/core/test_daily_summary.py::TestDailySummary::test_generate_basic_summary  # Single test
```

### Code Quality
```bash
# Format code with Black (auto-formats on save in VS Code)
black dayflow tests

# Sort imports
isort dayflow tests

# Run linting
flake8 dayflow tests --max-line-length=88 --extend-ignore=E203,W503

# Type checking
mypy dayflow --ignore-missing-imports

# Run all pre-commit hooks manually
pre-commit run --all-files
```

### Building and Distribution
```bash
# Build package
python -m build

# Upload to PyPI (when ready)
twine upload dist/*
```

## Architecture Overview

### Core Design Principles
1. **Modular Architecture**: Three main modules (core, vault, ui) with clear separation of concerns
2. **Cross-Platform Compatibility**: All file operations use UTF-8 encoding, path operations handle both Unix and Windows separators
3. **Flexible Vault Support**: Detects and adapts to existing vault structures (PARA, GTD, time-based, custom)
4. **Manual Token Flow**: Due to enterprise security constraints, uses Microsoft Graph Explorer tokens

### Key Components and Data Flow

```
Microsoft Graph API → GraphAPIClient → CalendarSyncEngine
                                              ↓
                                    ┌─────────┴──────────┐
                                    ↓                    ↓
                          ObsidianNoteFormatter  DailySummaryGenerator
                                    ↓                    ↓
                          VaultConnection ← CurrentMeetingManager
                                    ↓
                              Obsidian Vault
```

### Module Responsibilities

**dayflow.core**: Business logic and calendar processing
- `sync.py`: Orchestrates the entire sync workflow
- `graph_client.py`: Microsoft Graph API interface
- `obsidian_formatter.py`: Event-to-markdown conversion
- `daily_summary.py`: Daily overview generation
- `current_meeting.py`: Live meeting tracking
- `meeting_matcher.py`: Links notes to meetings by time
- `html_to_markdown.py`: Converts HTML meeting descriptions

**dayflow.vault**: Obsidian vault interactions
- `connection.py`: File I/O abstraction with folder organization support
- `config.py`: Configuration management (~/.dayflow/config.yaml)
- `detector.py`: Analyzes and detects vault structure
- `setup_wizard.py`: Interactive vault configuration

**dayflow.ui**: Command-line interface
- `cli.py`: All CLI commands and user interactions

### Configuration System

Configuration stored in `~/.dayflow/config.yaml`:
- Vault path and location mappings
- Optional folder organization (year/month/day, year/week, year/month)
- Calendar sync settings

### Folder Organization Feature

When enabled via `calendar.folder_organization`:
- Creates date-based folder hierarchy
- Prefixes notes with time (HHMM format)
- Maintains "Current Meeting.md" shortcut in vault root
- Highlights current meetings in daily summaries

## Important Implementation Details

### Windows Compatibility
- All `read_text()` and `write_text()` calls must specify `encoding='utf-8'`
- Path assertions in tests must handle both `/` and `\` separators
- The vault detector normalizes paths to forward slashes for consistency

### Test Markers
- `@pytest.mark.tdd`: Test-Driven Development tests for unimplemented features (skipped by default)
- `@pytest.mark.integration`: Integration tests requiring full system setup
- `@pytest.mark.slow`: Long-running tests
- `@pytest.mark.requires_token`: Tests needing valid Microsoft Graph token

### Pre-commit Hooks
The project uses pre-commit hooks that automatically:
- Fix trailing whitespace
- Ensure files end with newline
- Format code with Black
- Sort imports with isort
- Run flake8 linting
- Run mypy type checking

### Token Management
Currently uses manual token flow:
1. User gets token from Microsoft Graph Explorer
2. Token stored in `.graph_token` file
3. Tokens expire after ~24 hours
4. Future versions will implement proper OAuth flow

### VS Code Integration
The project includes `.vscode/settings.json` with:
- Python interpreter path configuration
- Black formatting on save
- Import sorting on save
- Flake8 and mypy integration

## Common Workflows

### Adding a New Feature
1. Write tests first (TDD approach)
2. Implement feature to pass tests
3. Update documentation if needed
4. Ensure all tests pass including Windows CI/CD
5. Run pre-commit hooks before committing

### Debugging Calendar Sync
1. Check token validity: `dayflow auth status`
2. Verify vault config: `dayflow vault status`
3. Run sync with specific date range for testing
4. Check logs for Microsoft Graph API errors

### Modifying Vault Structure Support
1. Update `detector.py` to recognize new structure
2. Add location mappings in `setup_wizard.py`
3. Update `connection.py` if new folder organization needed
4. Add tests for the new structure

## CI/CD Pipeline

GitHub Actions runs on push/PR:
- Tests on Ubuntu, Windows, and macOS
- Python versions 3.8 through 3.12
- Linting, formatting, and type checking
- Coverage reporting to Codecov
- TDD tests excluded by default
