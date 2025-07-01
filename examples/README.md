# Examples

This directory contains examples of using Dayflow.

## Available Examples

### [integration_example.py](integration_example.py)
Complete example showing:
- Authentication token loading
- Vault configuration
- Calendar synchronization
- Direct API usage
- Custom note creation
- Custom formatter implementation

Run it:
```bash
python examples/integration_example.py
```

## Quick Usage Examples

### Basic Sync
```python
from dayflow.core import CalendarSyncEngine
from dayflow.vault import VaultConfig, VaultConnection

# Load token
with open('.graph_token', 'r') as f:
    token_data = json.load(f)
access_token = token_data['access_token']

# Setup vault
config = VaultConfig()
vault_conn = VaultConnection(config)

# Sync calendar
engine = CalendarSyncEngine(access_token, vault_conn)
result = engine.sync()
print(f"Synced {result['events_synced']} events")
```

### Custom Note Creation
```python
from dayflow.vault import VaultConnection

vault_conn = VaultConnection(config)
content = """# My Custom Note
This is a custom note created programmatically.
"""
path = vault_conn.write_note(content, "Custom Note.md", "calendar_events")
```

### Meeting Detection
```python
from dayflow.core import MeetingMatcher

matcher = MeetingMatcher(vault_path)
current = matcher.find_current_meeting(meeting_notes_path)
if current:
    print(f"You're in: {current['title']}")
```

## Creating Your Own Examples

When adding examples:
1. Keep them self-contained
2. Add clear comments
3. Show error handling
4. Update this README
