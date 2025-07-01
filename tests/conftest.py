"""Shared test fixtures and configuration."""

import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_vault_config(temp_dir):
    """Create a mock vault configuration."""
    from dayflow.vault.config import VaultConfig

    config = Mock(spec=VaultConfig)
    config.vault_path = temp_dir
    config.get_location.return_value = temp_dir / "Calendar Events"
    config.config = {
        "vault": {
            "path": str(temp_dir),
            "locations": {
                "calendar_events": "Calendar Events",
                "daily_notes": "Daily Notes",
            },
        }
    }
    return config


@pytest.fixture
def sample_event():
    """Create a sample calendar event."""
    return {
        "subject": "Test Meeting",
        "start_time": datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
        "end_time": datetime(2024, 1, 15, 11, 0, tzinfo=timezone.utc),
        "location": "Conference Room A",
        "is_all_day": False,
        "attendees": [
            {"name": "John Doe", "email": "john@example.com"},
            {"name": "Jane Smith", "email": "jane@example.com"},
        ],
    }


@pytest.fixture
def mock_token_file(temp_dir):
    """Create a mock token file."""
    token_file = temp_dir / ".graph_token"
    token_data = {
        "access_token": "fake-token-12345",
        "expires_at": "2024-12-31T23:59:59",
        "acquired_at": "2024-01-01T00:00:00",
    }

    import json

    with open(token_file, "w") as f:
        json.dump(token_data, f)

    return token_file
