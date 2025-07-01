"""
Test cases for Calendar Sync Engine.
"""

from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from dayflow.core.graph_client import GraphAPIError
from dayflow.core.sync import CalendarSyncEngine


class TestCalendarSyncEngine:
    """Test calendar sync engine functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_token = "fake_token_12345"
        self.engine = CalendarSyncEngine(self.mock_token)

    @patch("dayflow.core.sync.GraphAPIClient")
    def test_sync_basic(self, mock_graph_client_class):
        """Test basic sync operation."""
        # Mock the GraphAPIClient instance
        mock_client = Mock()
        mock_graph_client_class.return_value = mock_client

        # Mock events returned from API
        mock_events = [
            {
                "id": "1",
                "subject": "Team Meeting",
                "start_time": datetime(2024, 1, 15, 10, 0),
                "end_time": datetime(2024, 1, 15, 11, 0),
                "location": {"displayName": "Room A"},
                "attendees": [],
            },
            {
                "id": "2",
                "subject": "Project Review",
                "start_time": datetime(2024, 1, 15, 14, 0),
                "end_time": datetime(2024, 1, 15, 15, 0),
                "location": {},
                "attendees": [],
            },
        ]
        mock_client.fetch_calendar_events.return_value = mock_events

        # Create new engine (to use mocked client)
        engine = CalendarSyncEngine(self.mock_token)

        # Perform sync
        result = engine.sync(date(2024, 1, 15), date(2024, 1, 15))

        # Verify GraphAPIClient was created with token
        mock_graph_client_class.assert_called_once_with(self.mock_token)

        # Verify fetch was called with correct dates
        mock_client.fetch_calendar_events.assert_called_once_with(
            date(2024, 1, 15), date(2024, 1, 15)
        )

        # Verify result
        assert result is not None
        assert result["events_synced"] == 2
        assert result["events"] == mock_events
        assert "sync_time" in result

    @patch("dayflow.core.sync.GraphAPIClient")
    def test_sync_with_no_events(self, mock_graph_client_class):
        """Test sync when no events are found."""
        mock_client = Mock()
        mock_graph_client_class.return_value = mock_client
        mock_client.fetch_calendar_events.return_value = []

        engine = CalendarSyncEngine(self.mock_token)
        result = engine.sync(date(2024, 1, 15), date(2024, 1, 15))

        assert result["events_synced"] == 0
        assert result["events"] == []

    @patch("dayflow.core.sync.GraphAPIClient")
    def test_sync_handles_api_errors(self, mock_graph_client_class):
        """Test sync handles Graph API errors gracefully."""
        mock_client = Mock()
        mock_graph_client_class.return_value = mock_client
        mock_client.fetch_calendar_events.side_effect = GraphAPIError(
            "Token expired", status_code=401
        )

        engine = CalendarSyncEngine(self.mock_token)

        with pytest.raises(GraphAPIError) as exc_info:
            engine.sync(date(2024, 1, 15), date(2024, 1, 15))

        assert exc_info.value.status_code == 401

    @patch("dayflow.core.sync.GraphAPIClient")
    def test_sync_default_date_range(self, mock_graph_client_class):
        """Test sync with default date range (yesterday to 7 days ahead)."""
        # Mock the client
        mock_client = Mock()
        mock_graph_client_class.return_value = mock_client
        mock_client.fetch_calendar_events.return_value = []

        # Create engine with mocked client
        engine = CalendarSyncEngine(self.mock_token)

        # The sync method should have a default date range if none provided
        result = engine.sync()

        # Should have called fetch with default date range
        mock_client.fetch_calendar_events.assert_called_once()
        call_args = mock_client.fetch_calendar_events.call_args[0]

        # Check that dates are reasonable (yesterday to 7 days ahead)
        start_date, end_date = call_args
        today = date.today()
        assert start_date == today - timedelta(days=1)
        assert end_date == today + timedelta(days=7)

        # Should not fail (even if it returns empty due to mock)
        assert result is not None

    @patch("dayflow.core.sync.GraphAPIClient")
    def test_sync_filters_cancelled_events(self, mock_graph_client_class):
        """Test that cancelled events are filtered out."""
        mock_client = Mock()
        mock_graph_client_class.return_value = mock_client

        # Include a cancelled event
        mock_events = [
            {
                "id": "1",
                "subject": "Active Meeting",
                "is_cancelled": False,
                "start_time": datetime(2024, 1, 15, 10, 0),
                "end_time": datetime(2024, 1, 15, 11, 0),
            },
            {
                "id": "2",
                "subject": "Cancelled Meeting",
                "is_cancelled": True,
                "start_time": datetime(2024, 1, 15, 14, 0),
                "end_time": datetime(2024, 1, 15, 15, 0),
            },
        ]
        mock_client.fetch_calendar_events.return_value = mock_events

        engine = CalendarSyncEngine(self.mock_token)
        result = engine.sync(date(2024, 1, 15), date(2024, 1, 15))

        # Should only include non-cancelled event
        assert result["events_synced"] == 1
        assert len(result["events"]) == 1
        assert result["events"][0]["subject"] == "Active Meeting"
