# Dayflow v0.1.0 - First Official Release 🎉

We're excited to announce the first official release of Dayflow, an intelligent calendar workflow system that bridges Microsoft 365 and Obsidian.

## 🚀 What is Dayflow?

Dayflow synchronizes your Microsoft 365 calendar events to your Obsidian vault, enabling you to:
- Keep meeting notes linked to calendar events
- Generate daily summaries with all your meetings
- Create quick notes that automatically link to current meetings
- Organize your vault with time-based folders

## ✨ Key Features

### Calendar Sync
- Sync Microsoft 365 calendar events to Obsidian
- Manual token authentication via Microsoft Graph Explorer
- Date range support for targeted syncing
- HTML to Markdown conversion for meeting descriptions

### Smart Meeting Detection
- Automatically detects current meeting based on time
- Links quick notes to meetings in progress
- Tracks upcoming meetings (5-minute lookahead)
- Highlights current meeting in daily summaries

### Vault Organization
- Support for PARA, GTD, and time-based structures
- Interactive setup wizard
- Date-based folder organization (year/month/day)
- Time-prefixed note naming (HHMM format)

### Note Creation
- Quick note command with meeting context
- Multiple templates (meeting, idea, task, reference)
- Rich frontmatter with metadata
- Automatic backlinking

### GTD & Zettelkasten
- Basic GTD workflow support
- Zettelkasten note management
- Literature note processing
- Weekly review generator

## 💻 Technical Details

- **Platforms**: Windows, macOS, Linux
- **Python**: 3.8, 3.9, 3.10, 3.11, 3.12
- **Coverage**: 75% test coverage with 249 tests
- **Encoding**: Full UTF-8 support

## 📦 Installation

```bash
# Clone and install
git clone https://github.com/MALathon/dayflow.git
cd dayflow
pip install -e .

# Or install from release
pip install https://github.com/MALathon/dayflow/releases/download/v0.1.0/dayflow-0.1.0-py3-none-any.whl
```

## 🚀 Quick Start

```bash
# Set up your vault
dayflow vault setup

# Authenticate with Microsoft
dayflow auth login

# Sync today's events
dayflow sync

# Create a quick note
dayflow note -t "Meeting notes"
```

## ⚠️ Known Limitations

- Manual token refresh required (~24 hour expiry)
- No OAuth flow (uses Microsoft Graph Explorer tokens)
- Read-only calendar access
- No background sync service

## 📋 What's Next?

Version 0.2.0 will focus on:
- Automatic token refresh
- Continuous sync daemon
- Multiple calendar support
- Progress indicators

## 🙏 Acknowledgments

Thank you to all early testers and contributors who helped shape this release.

---

**Full Changelog**: https://github.com/MALathon/dayflow/blob/main/CHANGELOG.md
