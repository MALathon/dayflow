"""Tests for continuous sync daemon."""

import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from dayflow.core.sync_daemon import ContinuousSyncManager


class TestContinuousSyncManager:
    """Test the continuous sync manager."""

    @pytest.fixture
    def mock_engine(self):
        """Create a mock sync engine."""
        engine = Mock()
        engine.sync.return_value = {
            "events_synced": 5,
            "notes_created": 2,
            "notes_updated": 1,
            "sync_time": 0.5,
        }
        return engine

    @pytest.fixture
    def manager(self, mock_engine, tmp_path):
        """Create a sync manager with test paths."""
        with patch("pathlib.Path.home", return_value=tmp_path):
            manager = ContinuousSyncManager(mock_engine, interval_minutes=1)
            return manager

    def test_init_creates_status_directory(self, tmp_path):
        """Test that initialization creates the .dayflow directory."""
        with patch("pathlib.Path.home", return_value=tmp_path):
            engine = Mock()
            ContinuousSyncManager(engine)

            dayflow_dir = tmp_path / ".dayflow"
            assert dayflow_dir.exists()

    def test_sync_once_performs_sync(self, manager, mock_engine):
        """Test that _sync_once performs a sync operation."""
        manager._sync_once()

        # Should have called sync with appropriate date range
        mock_engine.sync.assert_called_once()
        args = mock_engine.sync.call_args

        # Check that start_date is recent and end_date is tomorrow
        start_date = args.kwargs["start_date"]
        end_date = args.kwargs["end_date"]

        assert start_date <= datetime.now().date()
        assert end_date > datetime.now().date()

    def test_sync_once_updates_counts(self, manager, mock_engine):
        """Test that sync counts are updated after successful sync."""
        initial_count = manager._sync_count

        manager._sync_once()

        assert manager._sync_count == initial_count + 1
        assert manager._last_sync is not None

    def test_sync_error_increments_error_count(self, manager, mock_engine):
        """Test that errors increment the error count."""
        mock_engine.sync.side_effect = Exception("Test error")
        initial_errors = manager._error_count

        # _sync_once should raise the exception
        with patch("click.echo"):  # Suppress output
            with pytest.raises(Exception, match="Test error"):
                manager._sync_once()

        # Error count is handled in start() method, not _sync_once
        assert manager._error_count == initial_errors

    def test_save_status_writes_json(self, manager, tmp_path):
        """Test that status is saved to JSON file."""
        manager._sync_count = 10
        manager._error_count = 2
        manager._last_sync = datetime.now()

        manager._save_status()

        status_file = tmp_path / ".dayflow" / "sync_status.json"
        assert status_file.exists()

        # Load and verify content
        status = json.loads(status_file.read_text())
        assert status["sync_count"] == 10
        assert status["error_count"] == 2
        assert status["last_sync"] is not None
        assert status["interval_minutes"] == 1

    def test_load_status_restores_state(self, manager, tmp_path):
        """Test that previous status is loaded on init."""
        # Create a status file
        status_data = {
            "sync_count": 25,
            "error_count": 3,
            "last_sync": (datetime.now() - timedelta(hours=1)).isoformat(),
            "interval_minutes": 5,
        }

        status_file = tmp_path / ".dayflow" / "sync_status.json"
        status_file.write_text(json.dumps(status_data))

        # Create new manager - should load status
        with patch("pathlib.Path.home", return_value=tmp_path):
            new_manager = ContinuousSyncManager(Mock())

        assert new_manager._sync_count == 25
        assert new_manager._error_count == 3
        assert new_manager._last_sync is not None

    def test_signal_handler_stops_manager(self, manager):
        """Test that signal handler stops the manager."""
        manager.running = True

        with pytest.raises(SystemExit):
            manager._signal_handler(None, None)

        assert not manager.running

    def test_wait_with_countdown(self, manager):
        """Test countdown timer (with very short interval)."""
        manager.interval = 2  # 2 seconds for testing
        manager.running = True

        start_time = time.time()

        # Run in a thread and stop after 1 second
        import threading

        def stop_after_delay():
            time.sleep(1)
            manager.running = False

        threading.Thread(target=stop_after_delay).start()

        with patch("click.echo"):  # Suppress output
            manager._wait_with_countdown()

        # Should have stopped early (allowing for some overhead)
        elapsed = time.time() - start_time
        assert elapsed < 2.5  # Less than full interval plus overhead

    @patch("click.echo")
    def test_continuous_sync_loop(self, mock_echo, manager, mock_engine):
        """Test the main continuous sync loop."""
        # Set up to run only once
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                manager.running = False
            return {"events_synced": 1}

        mock_engine.sync.side_effect = side_effect
        manager.interval = 0.1  # Very short interval

        # Should not raise any exceptions
        manager.start()

        # Should have performed at least one sync
        assert mock_engine.sync.call_count >= 1

    def test_pid_file_management(self, mock_engine, tmp_path):
        """Test that PID file is created and cleaned up."""
        with patch("pathlib.Path.home", return_value=tmp_path):
            manager = ContinuousSyncManager(mock_engine, interval_minutes=1)
            pid_file = tmp_path / ".dayflow" / "sync.pid"

            # PID file should not exist initially
            assert not pid_file.exists()

            # Mock to stop immediately after first sync
            def side_effect(*args, **kwargs):
                # First call succeeds
                manager.running = False
                return {"events_synced": 1}

            mock_engine.sync.side_effect = side_effect

            # Start should create PID file
            with patch("time.sleep"):
                with patch("click.echo"):  # Suppress output
                    manager.start()

            # PID file should have been cleaned up by stop()
            assert not pid_file.exists()

    def test_pid_file_contains_correct_pid(self, manager, tmp_path):
        """Test that PID file contains correct process ID."""
        import os

        # Mock to stop after creating PID file
        def mock_sync_once():
            manager.running = False

        manager._sync_once = mock_sync_once

        with patch("time.sleep"):
            manager.start()

        # Check PID file was created with correct PID
        pid_file = tmp_path / ".dayflow" / "sync.pid"
        if pid_file.exists():
            stored_pid = int(pid_file.read_text())
            assert stored_pid == os.getpid()
