"""Test edge cases for sync daemon."""

import json
import signal
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from dayflow.core.sync_daemon import ContinuousSyncManager


class TestSyncDaemonEdgeCases:
    """Test edge cases and error scenarios for sync daemon."""

    @pytest.fixture
    def mock_engine(self):
        """Create a mock sync engine."""
        engine = Mock()
        engine.sync.return_value = {
            "events_synced": 5,
            "notes_created": 2,
            "notes_updated": 1,
            "sync_time": datetime.now(),
        }
        return engine

    def test_keyboard_interrupt_during_sync(self, mock_engine, tmp_path):
        """Test that KeyboardInterrupt properly stops the sync loop."""
        with patch("pathlib.Path.home", return_value=tmp_path):
            manager = ContinuousSyncManager(mock_engine, interval_minutes=1)

            # Mock the sync to raise KeyboardInterrupt on second call
            call_count = 0

            def mock_sync(**kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 2:
                    raise KeyboardInterrupt()
                return {
                    "events_synced": 3,
                    "notes_created": 1,
                    "notes_updated": 0,
                    "sync_time": datetime.now(),
                }

            mock_engine.sync.side_effect = mock_sync

            # Start should handle KeyboardInterrupt gracefully
            with patch("time.sleep"):
                with patch("click.echo") as mock_echo:
                    manager.start()

                    # Verify it stopped properly
                    assert not manager.running
                    assert manager._sync_count == 1  # Only one successful sync
                    # Check for the new summary box output
                    assert any(
                        "Continuous Sync Stopped" in str(call)
                        for call in mock_echo.call_args_list
                    )

    def test_exception_during_sync_with_retry(self, mock_engine, tmp_path):
        """Test error handling and retry logic during sync."""
        with patch("pathlib.Path.home", return_value=tmp_path):
            manager = ContinuousSyncManager(mock_engine, interval_minutes=1)

            # First sync fails, second succeeds
            mock_engine.sync.side_effect = [
                Exception("Network error"),
                {
                    "events_synced": 3,
                    "notes_created": 1,
                    "notes_updated": 0,
                    "sync_time": datetime.now(),
                },
            ]

            # Run two sync cycles
            with patch("time.sleep"):
                with patch("click.echo") as mock_echo:
                    # Override running to stop after 2 iterations
                    original_sync_once = manager._sync_once
                    sync_count = 0

                    def mock_sync_once():
                        nonlocal sync_count
                        sync_count += 1
                        original_sync_once()
                        if sync_count >= 2:
                            manager.running = False

                    manager._sync_once = mock_sync_once
                    manager.start()

                    # Verify error was shown
                    # The new error handling uses PrettyProgress
                    # Just verify the manager tried to sync twice
                    assert mock_engine.sync.call_count == 2
                    # Verify retry message
                    assert any(
                        "Will retry in" in str(call)
                        for call in mock_echo.call_args_list
                    )
                    # Verify we completed one successful sync after the error
                    assert manager._sync_count == 1
                    assert manager._error_count == 1

    def test_status_file_permission_error(self, mock_engine, tmp_path):
        """Test handling when status file cannot be written due to permissions."""
        # Create the .dayflow directory
        dayflow_dir = tmp_path / ".dayflow"
        dayflow_dir.mkdir()

        with patch("pathlib.Path.home", return_value=tmp_path):
            manager = ContinuousSyncManager(mock_engine, interval_minutes=1)

            # Patch the Path class write_text method to simulate permission error
            original_write_text = Path.write_text

            def failing_write_text(self, *args, **kwargs):
                if "sync_status.json" in str(self):
                    raise PermissionError("Access denied")
                return original_write_text(self, *args, **kwargs)

            with patch("pathlib.Path.write_text", new=failing_write_text):
                with patch("click.echo") as mock_echo:
                    # Try to save status
                    manager._save_status()

                    # Should show warning but not crash
                    # The warning is sent to stderr with err=True
                    assert mock_echo.called
                    error_calls = [
                        call
                        for call in mock_echo.call_args_list
                        if (
                            len(call[0]) > 0
                            and "Warning: Could not save sync status" in call[0][0]
                            and call[1].get("err") is True
                        )
                    ]
                    assert len(error_calls) > 0

    def test_corrupted_status_file(self, mock_engine, tmp_path):
        """Test loading from a corrupted status file."""
        # Create corrupted status file
        dayflow_dir = tmp_path / ".dayflow"
        dayflow_dir.mkdir()
        status_file = dayflow_dir / "sync_status.json"
        status_file.write_text("{ invalid json content }", encoding="utf-8")

        with patch("pathlib.Path.home", return_value=tmp_path):
            with patch("click.echo") as mock_echo:
                manager = ContinuousSyncManager(mock_engine, interval_minutes=1)

                # Should show warning but initialize successfully
                warning_calls = [
                    call
                    for call in mock_echo.call_args_list
                    if "Warning: Could not load sync status" in str(call)
                ]
                assert len(warning_calls) > 0
                # Should start with zero counts
                assert manager._sync_count == 0
                assert manager._error_count == 0

    def test_invalid_iso_format_in_status(self, mock_engine, tmp_path):
        """Test handling invalid ISO format in last_sync field."""
        # Create status file with invalid ISO format
        dayflow_dir = tmp_path / ".dayflow"
        dayflow_dir.mkdir()
        status_file = dayflow_dir / "sync_status.json"
        status_data = {
            "last_sync": "not-a-valid-date",
            "sync_count": 5,
            "error_count": 1,
        }
        status_file.write_text(json.dumps(status_data), encoding="utf-8")

        with patch("pathlib.Path.home", return_value=tmp_path):
            with patch("click.echo"):
                manager = ContinuousSyncManager(mock_engine, interval_minutes=1)

                # Should handle gracefully
                # Should load counts but not crash on date
                assert manager._sync_count == 5
                assert manager._error_count == 1
                assert manager._last_sync is None

    def test_sync_result_none_handling(self, mock_engine, tmp_path):
        """Test handling when sync returns None."""
        with patch("pathlib.Path.home", return_value=tmp_path):
            manager = ContinuousSyncManager(mock_engine, interval_minutes=1)

            # Make sync return None
            mock_engine.sync.return_value = None

            with patch("click.echo"):
                # Should not crash or update counts
                manager._sync_once()
                assert manager._sync_count == 0
                assert manager._last_sync is None

    def test_signal_handler_during_sync(self, mock_engine, tmp_path):
        """Test SIGTERM handling during sync operation."""
        with patch("pathlib.Path.home", return_value=tmp_path):
            manager = ContinuousSyncManager(mock_engine, interval_minutes=1)

            # Make sync take time
            def slow_sync(**kwargs):
                # Simulate SIGTERM arriving during sync
                manager._signal_handler(signal.SIGTERM, None)
                return {
                    "events_synced": 3,
                    "notes_created": 1,
                    "notes_updated": 0,
                    "sync_time": datetime.now(),
                }

            mock_engine.sync.side_effect = slow_sync

            with patch("sys.exit") as mock_exit:
                with patch("click.echo"):
                    # Start sync - should exit after signal
                    try:
                        manager._sync_once()
                    except SystemExit:
                        pass

                    # Verify signal was handled
                    assert not manager.running
                    mock_exit.assert_called_once_with(0)
