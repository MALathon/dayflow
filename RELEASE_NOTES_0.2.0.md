# Dayflow v0.2.0 Release Notes

## 🎉 Highlights

Dayflow v0.2.0 brings continuous synchronization and progress indicators, making it easier to keep your Obsidian vault in sync with your Microsoft 365 calendar throughout the workday.

## ✨ New Features

### Continuous Sync Mode
Run Dayflow in the background during your workday with automatic syncing:
```bash
# Start continuous sync with default 10-minute intervals
dayflow sync --continuous

# Custom sync interval (e.g., every 15 minutes)
dayflow sync --continuous --interval 15
```

**Features:**
- Configurable sync intervals
- Graceful shutdown with Ctrl+C
- Resume from previous session
- Automatic sync status tracking

### Progress Indicators
Get visual feedback during sync operations:
- "Fetching calendar events..." status
- "Processing event X of Y..." progress display
- Countdown timer showing time until next sync
- Use `--quiet` flag to suppress output for scripts

### Token Management Improvements
- Interactive prompt when token expires instead of auto-opening browser
- Better error messages and guidance for authentication
- Token expiry correctly documented as ~24 hours

### Sync Status Tracking
Check your sync status anytime:
```bash
dayflow status
```
Shows:
- Last sync time
- Total sync count
- Error count (if any)
- Current authentication status

## 🔧 Technical Improvements

- Added comprehensive test coverage for all new features (77% overall)
- Fixed Python 3.8/3.9 compatibility issues
- Improved error handling and recovery
- Better mocking in tests to prevent hanging

## 📦 Installation

### New Installation
```bash
pip install dayflow
```

### Upgrade from v0.1.0
```bash
pip install --upgrade dayflow
```

## 🚀 Quick Start

1. **One-time sync** (existing behavior):
   ```bash
   dayflow sync
   ```

2. **Continuous sync** (new!):
   ```bash
   dayflow sync --continuous
   ```

3. **Check sync status**:
   ```bash
   dayflow status
   ```

## ⚠️ Known Limitations

- Manual token refresh still required (tokens expire after ~24 hours)
- No automatic OAuth flow yet (uses Microsoft Graph Explorer tokens)
- Read-only calendar access
- Limited to primary calendar

## 🔄 Migration Notes

No breaking changes! All existing commands work exactly as before. The new features are purely additive.

## 🙏 Acknowledgments

Thanks to all contributors and users who provided feedback for this release!

## 📝 Full Changelog

See [CHANGELOG.md](CHANGELOG.md) for the complete list of changes.
