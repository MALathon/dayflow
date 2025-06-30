"""
Test cases for Microsoft Graph API client.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date, timedelta
import json

# These imports will fail initially - expected in TDD
from dayflow.core.graph_client import GraphAPIClient, GraphAPIError


class TestGraphAPIClient:
    """Test Graph API client functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6..." + "x" * 1000
        self.client = GraphAPIClient(self.mock_token)
    
    @patch('requests.get')
    def test_fetch_calendar_events_basic(self, mock_get):
        """Test fetching calendar events for a date range."""
        # Mock response data
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "value": [
                {
                    "id": "event1",
                    "subject": "Team Meeting",
                    "start": {
                        "dateTime": "2024-01-15T10:00:00.0000000",
                        "timeZone": "UTC"
                    },
                    "end": {
                        "dateTime": "2024-01-15T11:00:00.0000000",
                        "timeZone": "UTC"
                    },
                    "location": {
                        "displayName": "Conference Room A"
                    },
                    "attendees": [
                        {
                            "emailAddress": {
                                "name": "John Doe",
                                "address": "john@example.com"
                            },
                            "status": {
                                "response": "accepted"
                            }
                        }
                    ],
                    "body": {
                        "contentType": "html",
                        "content": "<p>Discuss Q1 goals</p>"
                    }
                }
            ],
            "@odata.nextLink": None
        }
        mock_get.return_value = mock_response
        
        # Test fetching events
        start_date = date(2024, 1, 15)
        end_date = date(2024, 1, 16)
        events = self.client.fetch_calendar_events(start_date, end_date)
        
        # Verify request
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        
        # Check URL
        assert "https://graph.microsoft.com/v1.0/me/calendarView" in call_args[0][0]
        
        # Check query parameters
        params = call_args[1]['params']
        assert params['startDateTime'] == '2024-01-15T00:00:00Z'
        assert params['endDateTime'] == '2024-01-16T00:00:00Z'
        
        # Check headers
        headers = call_args[1]['headers']
        assert headers['Authorization'] == f'Bearer {self.mock_token}'
        
        # Verify returned events
        assert len(events) == 1
        assert events[0]['subject'] == 'Team Meeting'
        assert events[0]['location']['displayName'] == 'Conference Room A'
    
    @patch('requests.get')
    def test_handle_pagination(self, mock_get):
        """Test handling paginated responses."""
        # First page response
        page1 = Mock()
        page1.status_code = 200
        page1.json.return_value = {
            "value": [{"id": "event1", "subject": "Meeting 1"}],
            "@odata.nextLink": "https://graph.microsoft.com/v1.0/me/calendarView?$skip=10"
        }
        
        # Second page response
        page2 = Mock()
        page2.status_code = 200
        page2.json.return_value = {
            "value": [{"id": "event2", "subject": "Meeting 2"}],
            "@odata.nextLink": None
        }
        
        mock_get.side_effect = [page1, page2]
        
        # Fetch events
        events = self.client.fetch_calendar_events(date(2024, 1, 1), date(2024, 1, 2))
        
        # Should make 2 requests
        assert mock_get.call_count == 2
        
        # Should return all events
        assert len(events) == 2
        assert events[0]['subject'] == 'Meeting 1'
        assert events[1]['subject'] == 'Meeting 2'
    
    @patch('requests.get')
    def test_handle_utc_timezone_without_z(self, mock_get):
        """Test handling UTC times that don't have 'Z' suffix."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "value": [{
                "id": "event1",
                "subject": "Test Meeting",
                "start": {
                    "dateTime": "2024-01-15T10:00:00.0000000",
                    "timeZone": "UTC"  # UTC but no 'Z' in dateTime
                }
            }]
        }
        mock_get.return_value = mock_response
        
        events = self.client.fetch_calendar_events(date(2024, 1, 15), date(2024, 1, 16))
        
        # Should handle UTC timezone correctly
        assert len(events) == 1
        # The client should normalize this to include timezone info
    
    @patch('requests.get')
    def test_handle_401_unauthorized(self, mock_get):
        """Test handling 401 unauthorized (token expired)."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": {
                "code": "InvalidAuthenticationToken",
                "message": "Access token has expired."
            }
        }
        mock_get.return_value = mock_response
        
        with pytest.raises(GraphAPIError) as exc_info:
            self.client.fetch_calendar_events(date(2024, 1, 1), date(2024, 1, 2))
        
        assert "expired" in str(exc_info.value).lower()
        assert exc_info.value.status_code == 401
    
    @patch('requests.get')
    def test_handle_rate_limiting(self, mock_get):
        """Test handling 429 rate limit responses."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'Retry-After': '60'}
        mock_response.json.return_value = {
            "error": {
                "code": "TooManyRequests",
                "message": "Too many requests"
            }
        }
        mock_get.return_value = mock_response
        
        with pytest.raises(GraphAPIError) as exc_info:
            self.client.fetch_calendar_events(date(2024, 1, 1), date(2024, 1, 2))
        
        assert exc_info.value.status_code == 429
        assert exc_info.value.retry_after == 60
    
    @patch('requests.get')
    def test_network_error_handling(self, mock_get):
        """Test handling network errors."""
        mock_get.side_effect = ConnectionError("Network is unreachable")
        
        with pytest.raises(GraphAPIError) as exc_info:
            self.client.fetch_calendar_events(date(2024, 1, 1), date(2024, 1, 2))
        
        assert "network" in str(exc_info.value).lower()
    
    def test_build_query_parameters(self):
        """Test building query parameters for calendar view."""
        params = self.client._build_calendar_query_params(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 20)
        )
        
        assert params['startDateTime'] == '2024-01-15T00:00:00Z'
        assert params['endDateTime'] == '2024-01-20T00:00:00Z'
        assert '$select' in params
        assert 'subject' in params['$select']
        assert '$orderby' in params
        assert '$top' in params  # Pagination size
    
    def test_normalize_event_data(self):
        """Test normalizing event data for consistent format."""
        raw_event = {
            "id": "123",
            "subject": "Test Meeting",
            "start": {
                "dateTime": "2024-01-15T10:00:00.0000000",
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": "2024-01-15T11:00:00.0000000",
                "timeZone": "America/Chicago"
            },
            "isAllDay": False,
            "isCancelled": False
        }
        
        normalized = self.client._normalize_event(raw_event)
        
        # Should have parsed datetime objects
        assert isinstance(normalized['start_time'], datetime)
        assert isinstance(normalized['end_time'], datetime)
        
        # Should preserve important fields
        assert normalized['subject'] == 'Test Meeting'
        assert normalized['id'] == '123'
        
        # Should handle missing fields gracefully
        assert 'location' in normalized
        assert 'attendees' in normalized