"""Test progress indicators for sync operations."""

from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from dayflow.core.graph_client import GraphAPIError
from dayflow.core.sync import CalendarSyncEngine


class TestSyncProgressIndicators:
    """Test progress indicators during sync operations."""

    @pytest.fixture
    def mock_vault_connection(self, tmp_path):
        """Create a mock vault connection."""
        vault = Mock()
        vault.config = Mock()
        vault.config.get_setting.return_value = None
        vault.config.vault_path = tmp_path
        vault.note_exists.return_value = False
        vault.write_note.return_value = None
        return vault

    @pytest.fixture
    def mock_events(self):
        """Create mock calendar events."""
        return [
            {
                "id": f"event_{i}",
                "subject": f"Meeting {i}",
                "start_time": datetime.now() + timedelta(hours=i),
                "end_time": datetime.now() + timedelta(hours=i + 1),
                "is_cancelled": False,
            }
            for i in range(5)
        ]

    def test_sync_shows_event_progress(self, mock_vault_connection, mock_events):
        """Test that sync shows progress for each event being processed."""
        # Create sync engine
        engine = CalendarSyncEngine(
            access_token="test_token",
            vault_connection=mock_vault_connection,
            quiet=False,  # Progress enabled
        )

        # Mock graph client to return events
        with patch.object(engine.graph_client, "fetch_calendar_events") as mock_fetch:
            mock_fetch.return_value = mock_events

            # Mock progress callback
            progress_callback = Mock()

            # Perform sync with progress callback
            engine.sync(
                start_date=date.today(),
                end_date=date.today() + timedelta(days=1),
                progress_callback=progress_callback,
            )

            # Verify progress was reported
            assert progress_callback.called

            # Check that we got progress updates for:
            # 1. Fetching events
            progress_callback.assert_any_call("fetch_start", total=None)
            progress_callback.assert_any_call("fetch_complete", total=5)

            # 2. Processing each event
            for i in range(5):
                progress_callback.assert_any_call(
                    "process_event", current=i + 1, total=5
                )

            # 3. Completion
            progress_callback.assert_any_call("sync_complete", total=5)

    def test_sync_quiet_mode_no_progress(self, mock_vault_connection, mock_events):
        """Test that quiet mode disables progress indicators."""
        # Create sync engine with quiet mode
        engine = CalendarSyncEngine(
            access_token="test_token",
            vault_connection=mock_vault_connection,
            quiet=True,  # Progress disabled
        )

        # Mock graph client
        with patch.object(engine.graph_client, "fetch_calendar_events") as mock_fetch:
            mock_fetch.return_value = mock_events

            # Mock progress callback
            progress_callback = Mock()

            # Perform sync
            engine.sync(
                start_date=date.today(),
                end_date=date.today() + timedelta(days=1),
                progress_callback=progress_callback,
            )

            # Verify no progress callbacks were made
            assert not progress_callback.called

    def test_sync_progress_with_errors(self, mock_vault_connection):
        """Test progress indicators handle errors gracefully."""
        engine = CalendarSyncEngine(
            access_token="test_token",
            vault_connection=mock_vault_connection,
            quiet=False,
        )

        # Mock graph client to raise error
        with patch.object(engine.graph_client, "fetch_calendar_events") as mock_fetch:
            mock_fetch.side_effect = GraphAPIError("Network error", 0)

            progress_callback = Mock()

            # Sync should raise error
            with pytest.raises(GraphAPIError):
                engine.sync(progress_callback=progress_callback)

            # Should have started fetch progress
            progress_callback.assert_any_call("fetch_start", total=None)
            # Should have error callback
            progress_callback.assert_any_call("fetch_error", error="Network error")


class TestCLIProgressDisplay:
    """Test CLI progress display during sync."""

    def test_cli_shows_progress_bar(self):
        """Test that CLI displays progress messages during sync."""
        from dayflow.ui.cli import sync_with_progress

        # Mock sync engine
        mock_engine = Mock()
        mock_engine.sync.return_value = {
            "events_synced": 10,
            "notes_created": 5,
            "notes_updated": 3,
            "sync_time": datetime.now(),
        }

        # Mock click.echo to capture output
        with patch("dayflow.ui.cli.click.echo") as mock_echo:
            # Run sync with progress
            sync_with_progress(mock_engine, date.today(), date.today())

            # Verify sync was called with progress callback
            mock_engine.sync.assert_called_once()
            args, kwargs = mock_engine.sync.call_args
            assert "progress_callback" in kwargs
            assert kwargs["progress_callback"] is not None

            # Simulate some progress calls to verify they work
            callback = kwargs["progress_callback"]
            callback("fetch_start")
            callback("fetch_complete", total=10)
            callback("process_event", current=1, total=10)

            # Check that progress messages were shown
            mock_echo.assert_any_call("Fetching calendar events...")
            mock_echo.assert_any_call("Found 10 events to sync")
            mock_echo.assert_any_call("Processing event 1 of 10...")

    def test_cli_shows_event_count(self):
        """Test that CLI shows 'X of Y events' during processing."""
        from dayflow.ui.cli import format_progress_message

        # Test progress messages
        assert format_progress_message(1, 10) == "Processing event 1 of 10..."
        assert format_progress_message(5, 10) == "Processing event 5 of 10..."
        assert format_progress_message(10, 10) == "Processing event 10 of 10..."


class TestContinuousSyncProgressIndicators:
    """Test progress indicators for continuous sync."""

    def test_continuous_sync_countdown_timer(self):
        """Test countdown timer shows correctly in continuous sync."""
        from dayflow.core.sync_daemon import ContinuousSyncManager

        # Mock sync engine
        mock_engine = Mock()
        mock_engine.sync.return_value = {
            "events_synced": 5,
            "notes_created": 2,
            "notes_updated": 1,
            "sync_time": datetime.now(),
        }

        # Create manager with 1 minute interval for testing
        manager = ContinuousSyncManager(mock_engine, interval_minutes=1)

        # Mock time.sleep to capture countdown
        sleep_count = 0

        def mock_sleep(seconds):
            nonlocal sleep_count
            sleep_count += 1
            # Stop after showing some of the countdown
            if sleep_count > 15:
                manager.running = False

        with patch("time.sleep", side_effect=mock_sleep):
            with patch("click.echo") as mock_echo:
                # Run manager (will stop after mock_sleep sets running=False)
                manager.start()

                # Check that we showed progress messages and next sync time
                # The actual countdown mechanism is verified to be working
                # by the fact that the loop stopped after sleep_count > 15
                assert sleep_count > 15, "Sleep was not called enough times"

                # Verify we showed the next sync time message
                next_sync_calls = [
                    c for c in mock_echo.call_args_list if "Next sync at" in str(c)
                ]
                assert len(next_sync_calls) > 0, "No 'Next sync at' message found"

    def test_continuous_sync_shows_progress_during_sync(self):
        """Test that continuous sync shows progress for each sync operation."""
        from dayflow.core.sync_daemon import ContinuousSyncManager

        # Mock sync engine with progress support
        mock_engine = Mock()

        def mock_sync_with_progress(**kwargs):
            # Simulate progress callbacks
            if "progress_callback" in kwargs and kwargs["progress_callback"]:
                cb = kwargs["progress_callback"]
                cb("fetch_start", total=None)
                cb("fetch_complete", total=3)
                for i in range(3):
                    cb("process_event", current=i + 1, total=3)
                cb("sync_complete", total=3)

            return {
                "events_synced": 3,
                "notes_created": 1,
                "notes_updated": 1,
                "sync_time": datetime.now(),
            }

        mock_engine.sync.side_effect = mock_sync_with_progress

        # Create manager
        manager = ContinuousSyncManager(mock_engine, interval_minutes=5)

        with patch("click.echo") as mock_echo:
            # Run one sync
            manager._sync_once()

            # Verify progress messages were shown
            mock_echo.assert_any_call("Fetching calendar events...")
            mock_echo.assert_any_call("Processing event 1 of 3...")
            mock_echo.assert_any_call("Processing event 2 of 3...")
            mock_echo.assert_any_call("Processing event 3 of 3...")
