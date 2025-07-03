"""Test CLI progress indicator functions."""

from datetime import date, datetime
from unittest.mock import Mock, patch

import pytest

from dayflow.ui.cli import format_progress_message, sync_with_progress


class TestCLIProgressFunctions:
    """Test progress indicator functions in CLI."""

    def test_format_progress_message(self):
        """Test progress message formatting."""
        assert format_progress_message(1, 10) == "Processing event 1 of 10..."
        assert format_progress_message(5, 10) == "Processing event 5 of 10..."
        assert format_progress_message(10, 10) == "Processing event 10 of 10..."
        assert format_progress_message(1, 1) == "Processing event 1 of 1..."
        assert format_progress_message(0, 0) == "Processing event 0 of 0..."

    def test_sync_with_progress_normal_flow(self):
        """Test sync_with_progress with normal flow."""
        # Mock sync engine
        mock_engine = Mock()
        mock_result = {
            "events_synced": 5,
            "notes_created": 2,
            "notes_updated": 3,
            "sync_time": datetime.now(),
        }

        def mock_sync(**kwargs):
            # Capture the progress callback
            if "progress_callback" in kwargs:
                callback = kwargs["progress_callback"]
                # Simulate sync progress
                callback("fetch_start")
                callback("fetch_complete", total=5)
                for i in range(5):
                    callback("process_event", current=i + 1, total=5)
                callback("sync_complete", total=5)
            return mock_result

        mock_engine.sync.side_effect = mock_sync

        with patch("dayflow.ui.cli.click.echo") as mock_echo:
            result = sync_with_progress(mock_engine, date.today(), date.today())

            # Verify result
            assert result == mock_result

            # Verify progress messages
            mock_echo.assert_any_call("Fetching calendar events...")
            mock_echo.assert_any_call("Found 5 events to sync")
            mock_echo.assert_any_call("Processing event 1 of 5...")
            mock_echo.assert_any_call("Processing event 5 of 5...")
            mock_echo.assert_any_call("\nSync complete!")

    def test_sync_with_progress_zero_events(self):
        """Test sync_with_progress when no events found."""
        mock_engine = Mock()
        mock_result = {
            "events_synced": 0,
            "notes_created": 0,
            "notes_updated": 0,
            "sync_time": datetime.now(),
        }

        def mock_sync(**kwargs):
            if "progress_callback" in kwargs:
                callback = kwargs["progress_callback"]
                callback("fetch_start")
                callback("fetch_complete", total=0)
                callback("sync_complete", total=0)
            return mock_result

        mock_engine.sync.side_effect = mock_sync

        with patch("dayflow.ui.cli.click.echo") as mock_echo:
            result = sync_with_progress(mock_engine, date.today(), date.today())

            assert result == mock_result
            mock_echo.assert_any_call("Found 0 events to sync")
            mock_echo.assert_any_call("\nSync complete!")

    def test_sync_with_progress_error_handling(self):
        """Test sync_with_progress error handling."""
        mock_engine = Mock()

        def mock_sync(**kwargs):
            if "progress_callback" in kwargs:
                callback = kwargs["progress_callback"]
                callback("fetch_start")
                callback("fetch_error", error="Network timeout")
            raise Exception("Network timeout")

        mock_engine.sync.side_effect = mock_sync

        with patch("dayflow.ui.cli.click.echo") as mock_echo:
            with pytest.raises(Exception, match="Network timeout"):
                sync_with_progress(mock_engine, date.today(), date.today())

            # Verify error was shown
            mock_echo.assert_any_call(
                "\nError fetching events: Network timeout", err=True
            )

    def test_sync_with_progress_callback_exception(self):
        """Test that exceptions in progress display don't crash sync."""
        mock_engine = Mock()
        mock_result = {
            "events_synced": 3,
            "notes_created": 1,
            "notes_updated": 1,
            "sync_time": datetime.now(),
        }

        def mock_sync(**kwargs):
            # Return result regardless of callback errors
            return mock_result

        mock_engine.sync.side_effect = mock_sync

        # Make click.echo raise exception
        with patch("dayflow.ui.cli.click.echo") as mock_echo:
            mock_echo.side_effect = Exception("Terminal error")

            # Should still return result despite display errors
            result = sync_with_progress(mock_engine, date.today(), date.today())
            assert result == mock_result

    def test_sync_with_progress_large_event_count(self):
        """Test progress display with large number of events."""
        mock_engine = Mock()
        mock_result = {
            "events_synced": 1000,
            "notes_created": 500,
            "notes_updated": 500,
            "sync_time": datetime.now(),
        }

        def mock_sync(**kwargs):
            if "progress_callback" in kwargs:
                callback = kwargs["progress_callback"]
                callback("fetch_start")
                callback("fetch_complete", total=1000)
                # Simulate processing some events
                for i in [1, 100, 500, 1000]:
                    callback("process_event", current=i, total=1000)
                callback("sync_complete", total=1000)
            return mock_result

        mock_engine.sync.side_effect = mock_sync

        with patch("dayflow.ui.cli.click.echo") as mock_echo:
            result = sync_with_progress(mock_engine, date.today(), date.today())

            assert result == mock_result
            mock_echo.assert_any_call("Found 1000 events to sync")
            mock_echo.assert_any_call("Processing event 1 of 1000...")
            mock_echo.assert_any_call("Processing event 1000 of 1000...")
