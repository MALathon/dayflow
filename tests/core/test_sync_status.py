"""Tests for sync status utilities."""

import json
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from dayflow.core.sync_status import get_sync_status


class TestSyncStatus:
    """Test sync status utilities."""

    @pytest.fixture
    def status_data(self):
        """Sample status data."""
        return {
            "last_sync": (datetime.now() - timedelta(minutes=30)).isoformat(),
            "sync_count": 15,
            "error_count": 1,
            "interval_minutes": 5,
            "updated_at": datetime.now().isoformat(),
        }

    def test_get_sync_status_no_file(self, tmp_path):
        """Test getting status when no file exists."""
        with patch("pathlib.Path.home", return_value=tmp_path):
            status = get_sync_status()
            assert status is None

    def test_get_sync_status_valid_file(self, tmp_path, status_data):
        """Test getting status from valid file."""
        # Create status file
        dayflow_dir = tmp_path / ".dayflow"
        dayflow_dir.mkdir()
        status_file = dayflow_dir / "sync_status.json"
        status_file.write_text(json.dumps(status_data))

        with patch("pathlib.Path.home", return_value=tmp_path):
            status = get_sync_status()

        assert status is not None
        assert status["sync_count"] == 15
        assert status["error_count"] == 1
        assert "last_sync_datetime" in status
        assert "time_since_last_sync" in status

    def test_get_sync_status_invalid_json(self, tmp_path):
        """Test getting status from corrupted file."""
        dayflow_dir = tmp_path / ".dayflow"
        dayflow_dir.mkdir()
        status_file = dayflow_dir / "sync_status.json"
        status_file.write_text("invalid json")

        with patch("pathlib.Path.home", return_value=tmp_path):
            status = get_sync_status()
            assert status is None

    def test_get_sync_status_missing_last_sync(self, tmp_path):
        """Test status file without last_sync field."""
        data = {"sync_count": 5, "error_count": 0}

        dayflow_dir = tmp_path / ".dayflow"
        dayflow_dir.mkdir()
        status_file = dayflow_dir / "sync_status.json"
        status_file.write_text(json.dumps(data))

        with patch("pathlib.Path.home", return_value=tmp_path):
            status = get_sync_status()

        assert status is not None
        assert status["sync_count"] == 5
        assert "last_sync_datetime" not in status
        assert "time_since_last_sync" not in status

    def test_time_since_last_sync_calculation(self, tmp_path):
        """Test that time since last sync is calculated correctly."""
        # Set last sync to exactly 1 hour ago
        one_hour_ago = datetime.now() - timedelta(hours=1)
        data = {"last_sync": one_hour_ago.isoformat(), "sync_count": 10}

        dayflow_dir = tmp_path / ".dayflow"
        dayflow_dir.mkdir()
        status_file = dayflow_dir / "sync_status.json"
        status_file.write_text(json.dumps(data))

        with patch("pathlib.Path.home", return_value=tmp_path):
            status = get_sync_status()

        time_since = status["time_since_last_sync"]
        # Should be approximately 1 hour (allowing for test execution time)
        assert 59 <= time_since.total_seconds() / 60 <= 61
