"""
Test cases for Microsoft Graph API client.
"""

import json
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest

# These imports will fail initially - expected in TDD
from dayflow.core.graph_client import GraphAPIClient, GraphAPIError


class TestGraphAPIClient:
    """Test Graph API client functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6..." + "x" * 1000
        self.client = GraphAPIClient(self.mock_token)

    @patch("requests.get")
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
                        "timeZone": "UTC",
                    },
                    "end": {
                        "dateTime": "2024-01-15T11:00:00.0000000",
                        "timeZone": "UTC",
                    },
                    "location": {"displayName": "Conference Room A"},
                    "attendees": [
                        {
                            "emailAddress": {
                                "name": "John Doe",
                                "address": "john@example.com",
                            },
                            "status": {"response": "accepted"},
                        }
                    ],
                    "body": {
                        "contentType": "html",
                        "content": "<p>Discuss Q1 goals</p>",
                    },
                }
            ],
            "@odata.nextLink": None,
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
        params = call_args[1]["params"]
        assert params["startDateTime"] == "2024-01-15T00:00:00Z"
        assert params["endDateTime"] == "2024-01-16T00:00:00Z"

        # Check headers
        headers = call_args[1]["headers"]
        assert headers["Authorization"] == f"Bearer {self.mock_token}"

        # Verify returned events
        assert len(events) == 1
        assert events[0]["subject"] == "Team Meeting"
        # Location should be normalized to a string, not a dict
        assert events[0]["location"] == "Conference Room A"
        assert isinstance(events[0]["location"], str)

    @patch("requests.get")
    def test_handle_pagination(self, mock_get):
        """Test handling paginated responses."""
        # First page response
        page1 = Mock()
        page1.status_code = 200
        page1.json.return_value = {
            "value": [{"id": "event1", "subject": "Meeting 1"}],
            "@odata.nextLink": "https://graph.microsoft.com/v1.0/me/calendarView?$skip=10",
        }

        # Second page response
        page2 = Mock()
        page2.status_code = 200
        page2.json.return_value = {
            "value": [{"id": "event2", "subject": "Meeting 2"}],
            "@odata.nextLink": None,
        }

        mock_get.side_effect = [page1, page2]

        # Fetch events
        events = self.client.fetch_calendar_events(date(2024, 1, 1), date(2024, 1, 2))

        # Should make 2 requests
        assert mock_get.call_count == 2

        # Should return all events
        assert len(events) == 2
        assert events[0]["subject"] == "Meeting 1"
        assert events[1]["subject"] == "Meeting 2"

    @patch("requests.get")
    def test_handle_utc_timezone_without_z(self, mock_get):
        """Test handling UTC times that don't have 'Z' suffix."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "value": [
                {
                    "id": "event1",
                    "subject": "Test Meeting",
                    "start": {
                        "dateTime": "2024-01-15T10:00:00.0000000",
                        "timeZone": "UTC",  # UTC but no 'Z' in dateTime
                    },
                }
            ]
        }
        mock_get.return_value = mock_response

        events = self.client.fetch_calendar_events(date(2024, 1, 15), date(2024, 1, 16))

        # Should handle UTC timezone correctly
        assert len(events) == 1
        # The client should normalize this to include timezone info

    @patch("requests.get")
    def test_handle_401_unauthorized(self, mock_get):
        """Test handling 401 unauthorized (token expired)."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": {
                "code": "InvalidAuthenticationToken",
                "message": "Access token has expired.",
            }
        }
        mock_get.return_value = mock_response

        with pytest.raises(GraphAPIError) as exc_info:
            self.client.fetch_calendar_events(date(2024, 1, 1), date(2024, 1, 2))

        assert "expired" in str(exc_info.value).lower()
        assert exc_info.value.status_code == 401

    @patch("requests.get")
    def test_handle_rate_limiting(self, mock_get):
        """Test handling 429 rate limit responses."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_response.json.return_value = {
            "error": {"code": "TooManyRequests", "message": "Too many requests"}
        }
        mock_get.return_value = mock_response

        with pytest.raises(GraphAPIError) as exc_info:
            self.client.fetch_calendar_events(date(2024, 1, 1), date(2024, 1, 2))

        assert exc_info.value.status_code == 429
        assert exc_info.value.retry_after == 60

    @patch("requests.get")
    def test_network_error_handling(self, mock_get):
        """Test handling network errors."""
        mock_get.side_effect = ConnectionError("Network is unreachable")

        with pytest.raises(GraphAPIError) as exc_info:
            self.client.fetch_calendar_events(date(2024, 1, 1), date(2024, 1, 2))

        assert "network" in str(exc_info.value).lower()

    def test_build_query_parameters(self):
        """Test building query parameters for calendar view."""
        params = self.client._build_calendar_query_params(
            start_date=date(2024, 1, 15), end_date=date(2024, 1, 20)
        )

        assert params["startDateTime"] == "2024-01-15T00:00:00Z"
        assert params["endDateTime"] == "2024-01-20T00:00:00Z"
        assert "$select" in params
        assert "subject" in params["$select"]
        assert "$orderby" in params
        assert "$top" in params  # Pagination size

    def test_normalize_event_data(self):
        """Test normalizing event data for consistent format."""
        raw_event = {
            "id": "123",
            "subject": "Test Meeting",
            "start": {"dateTime": "2024-01-15T10:00:00.0000000", "timeZone": "UTC"},
            "end": {
                "dateTime": "2024-01-15T11:00:00.0000000",
                "timeZone": "America/Chicago",
            },
            "isAllDay": False,
            "isCancelled": False,
        }

        normalized = self.client._normalize_event(raw_event)

        # Should have parsed datetime objects
        assert isinstance(normalized["start_time"], datetime)
        assert isinstance(normalized["end_time"], datetime)

        # Should preserve important fields
        assert normalized["subject"] == "Test Meeting"
        assert normalized["id"] == "123"

        # Should handle missing fields gracefully
        assert "location" in normalized
        assert "attendees" in normalized

    def test_normalize_event_with_dict_location(self):
        """Test normalizing event with location as dict (Graph API format).
        
        This test ensures we don't get 'expected str instance, dict found' errors.
        """
        raw_event = {
            "id": "123",
            "subject": "Test Meeting",
            "start": {"dateTime": "2024-01-15T10:00:00", "timeZone": "UTC"},
            "end": {"dateTime": "2024-01-15T11:00:00", "timeZone": "UTC"},
            "location": {
                "displayName": "Conference Room A",
                "address": {"street": "123 Main St"},
                "coordinates": {"latitude": 40.7128, "longitude": -74.0060}
            },
            "isAllDay": False,
            "isCancelled": False,
        }

        normalized = self.client._normalize_event(raw_event)
        
        # Location should be extracted as string, not dict
        assert normalized["location"] == "Conference Room A"
        assert isinstance(normalized["location"], str)
        # Full location data should be preserved
        assert normalized["location_data"]["displayName"] == "Conference Room A"

    def test_normalize_event_with_empty_location_dict(self):
        """Test normalizing event with empty location dict."""
        raw_event = {
            "id": "123",
            "subject": "Test Meeting",
            "start": {"dateTime": "2024-01-15T10:00:00", "timeZone": "UTC"},
            "end": {"dateTime": "2024-01-15T11:00:00", "timeZone": "UTC"},
            "location": {},  # Empty dict
            "isAllDay": False,
            "isCancelled": False,
        }

        normalized = self.client._normalize_event(raw_event)
        
        # Should handle empty dict gracefully
        assert normalized["location"] == ""
        assert isinstance(normalized["location"], str)

    def test_normalize_event_with_dict_body(self):
        """Test normalizing event with body as dict (Graph API format)."""
        raw_event = {
            "id": "123",
            "subject": "Test Meeting",
            "start": {"dateTime": "2024-01-15T10:00:00", "timeZone": "UTC"},
            "end": {"dateTime": "2024-01-15T11:00:00", "timeZone": "UTC"},
            "body": {
                "contentType": "HTML",
                "content": "<p>Meeting agenda details</p>"
            },
            "isAllDay": False,
            "isCancelled": False,
        }

        normalized = self.client._normalize_event(raw_event)
        
        # Body content should be extracted and converted to markdown
        assert normalized["body"] == "Meeting agenda details"
        assert isinstance(normalized["body"], str)
        # Full body data should be preserved
        assert normalized["body_data"]["contentType"] == "HTML"

    def test_normalize_event_with_attendees_shows_names_not_unknown(self):
        """Test that attendee names are properly extracted, not showing as 'Unknown'.
        
        This test ensures the formatter can extract names from the Graph API structure.
        """
        raw_event = {
            "id": "123",
            "subject": "Test Meeting",
            "start": {"dateTime": "2024-01-15T10:00:00", "timeZone": "UTC"},
            "end": {"dateTime": "2024-01-15T11:00:00", "timeZone": "UTC"},
            "attendees": [
                {
                    "type": "required",
                    "status": {"response": "none"},
                    "emailAddress": {
                        "name": "John Doe",
                        "address": "john.doe@example.com"
                    }
                },
                {
                    "type": "optional",
                    "status": {"response": "accepted"},
                    "emailAddress": {
                        "name": "Jane Smith",
                        "address": "jane.smith@example.com"
                    }
                },
                {
                    "type": "required",
                    "emailAddress": {
                        # No name, only email
                        "address": "noname@example.com"
                    }
                }
            ],
            "isAllDay": False,
            "isCancelled": False,
        }

        normalized = self.client._normalize_event(raw_event)
        
        # Attendees structure should be preserved for formatter
        assert len(normalized["attendees"]) == 3
        assert normalized["attendees"][0]["emailAddress"]["name"] == "John Doe"
        assert normalized["attendees"][1]["emailAddress"]["name"] == "Jane Smith"
        # Third attendee has no name, only address
        assert "name" not in normalized["attendees"][2]["emailAddress"]
        assert normalized["attendees"][2]["emailAddress"]["address"] == "noname@example.com"

    def test_extract_online_meeting_url_from_online_meeting(self):
        """Test extracting Teams meeting URL from onlineMeeting property."""
        event = {
            "subject": "Team Meeting",
            "isOnlineMeeting": True,
            "onlineMeeting": {
                "joinUrl": "https://teams.microsoft.com/l/meetup-join/19%3ameeting_123"
            }
        }

        url = self.client._extract_online_meeting_url(event)
        
        assert url == "https://teams.microsoft.com/l/meetup-join/19%3ameeting_123"

    def test_extract_online_meeting_url_from_body(self):
        """Test extracting Teams meeting URL from body content."""
        event = {
            "subject": "Team Meeting",
            "body": {
                "contentType": "HTML",
                "content": '''<p>Join the meeting:</p>
                <a href="https://teams.microsoft.com/l/meetup-join/19%3ameeting_456">
                Click here to join</a>'''
            }
        }

        url = self.client._extract_online_meeting_url(event)
        
        assert url == "https://teams.microsoft.com/l/meetup-join/19%3ameeting_456"

    @patch('requests.get')
    def test_full_integration_complex_graph_response(self, mock_get):
        """Test full integration with complex Graph API response.
        
        This test ensures we handle all the complex data structures from a real
        Graph API response without errors.
        """
        # Mock a realistic Graph API response with all complex structures
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "value": [
                {
                    "id": "event1",
                    "subject": "Team Standup",
                    "start": {"dateTime": "2024-01-15T09:00:00", "timeZone": "UTC"},
                    "end": {"dateTime": "2024-01-15T09:30:00", "timeZone": "UTC"},
                    "location": {"displayName": "Teams Meeting"},
                    "body": {"contentType": "HTML", "content": "<p>Daily standup</p>"},
                    "attendees": [
                        {
                            "type": "required",
                            "emailAddress": {
                                "name": "John Doe",
                                "address": "john@mayo.edu"
                            }
                        },
                        {
                            "type": "optional", 
                            "emailAddress": {
                                "name": "Jane Smith",
                                "address": "jane@mayo.edu"
                            }
                        }
                    ],
                    "isOnlineMeeting": True,
                    "onlineMeeting": {
                        "joinUrl": "https://teams.microsoft.com/l/meetup-join/123"
                    },
                    "isAllDay": False,
                    "isCancelled": False,
                    "organizer": {
                        "emailAddress": {
                            "name": "Meeting Organizer",
                            "address": "organizer@mayo.edu"
                        }
                    }
                }
            ]
        }
        mock_get.return_value = mock_response

        events = self.client.fetch_calendar_events(date(2024, 1, 15), date(2024, 1, 16))
        
        assert len(events) == 1
        event = events[0]
        
        # Verify all fields are properly normalized and no dicts where strings expected
        assert isinstance(event["location"], str)
        assert event["location"] == "Teams Meeting"
        assert isinstance(event["body"], str)
        assert event["body"] == "Daily standup"  # HTML should be converted to plain text
        assert event["online_meeting_url"] == "https://teams.microsoft.com/l/meetup-join/123"
        assert event["is_online_meeting"] is True
        
        # Verify attendees are preserved with structure
        assert len(event["attendees"]) == 2
        assert event["attendees"][0]["emailAddress"]["name"] == "John Doe"
        assert event["attendees"][1]["emailAddress"]["name"] == "Jane Smith"
        
        # No field should cause "expected str instance, dict found" error
    
    def test_normalize_event_with_complex_teams_html(self):
        """Test normalizing event with complex Teams meeting HTML."""
        raw_event = {
            "id": "123",
            "subject": "Project Review",
            "start": {"dateTime": "2024-01-15T10:00:00", "timeZone": "UTC"},
            "end": {"dateTime": "2024-01-15T11:00:00", "timeZone": "UTC"},
            "body": {
                "contentType": "html",
                "content": """
                <html>
                <head>
                <style>
                @font-face { font-family: 'Segoe UI'; src: url('fonts/segoeui.ttf'); }
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
                .meeting-info { background-color: #f0f0f0; padding: 10px; }
                </style>
                </head>
                <body>
                <p>Please join us for the quarterly project review.</p>
                <p>We'll be discussing:</p>
                <ul>
                    <li>Q4 accomplishments</li>
                    <li>Q1 goals and objectives</li>
                    <li>Resource allocation</li>
                </ul>
                <div class="meeting-info">
                    <p><strong>Join on your computer, mobile app or room device</strong></p>
                    <a href="https://teams.microsoft.com/l/meetup-join/19%3ameeting_ABC123XYZ">
                    Click here to join the meeting
                    </a>
                    <p>Meeting ID: 123 456 789 012</p>
                    <p>Phone Conference ID: 987-654-321</p>
                </div>
                <p>Looking forward to seeing everyone!</p>
                </body>
                </html>
                """
            },
            "isOnlineMeeting": True,
            "isAllDay": False,
            "isCancelled": False,
        }
        
        normalized = self.client._normalize_event(raw_event)
        
        # Body should be converted to clean markdown
        assert "Please join us for the quarterly project review" in normalized["body"]
        assert "- Q4 accomplishments" in normalized["body"]
        assert "- Q1 goals and objectives" in normalized["body"]
        assert "- Resource allocation" in normalized["body"]
        assert "Looking forward to seeing everyone!" in normalized["body"]
        
        # HTML and CSS should be stripped
        assert "@font-face" not in normalized["body"]
        assert "Segoe UI" not in normalized["body"]
        assert "<style>" not in normalized["body"]
        assert "<div>" not in normalized["body"]
        
        # Teams boilerplate should be simplified
        assert "Microsoft Teams meeting" in normalized["body"]
        assert "Meeting ID: 123 456 789" not in normalized["body"]
        assert "Phone Conference ID:" not in normalized["body"]
        
        # Meeting URL should be extracted
        assert normalized["online_meeting_url"] == "https://teams.microsoft.com/l/meetup-join/19%3ameeting_ABC123XYZ"
