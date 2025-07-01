"""
Microsoft Graph API client for calendar operations.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import requests

from dayflow.core.html_to_markdown import html_to_markdown, extract_meeting_url


class GraphAPIError(Exception):
    """Custom exception for Graph API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        retry_after: Optional[int] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after


class GraphAPIClient:
    """Client for Microsoft Graph API calendar operations."""

    BASE_URL = "https://graph.microsoft.com/v1.0"

    def __init__(self, access_token: str):
        """Initialize with an access token."""
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    def fetch_calendar_events(
        self, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        """Fetch calendar events for a date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of calendar events
        """
        # Build query parameters
        params = self._build_calendar_query_params(start_date, end_date)

        # Fetch events with pagination
        all_events = []
        url = f"{self.BASE_URL}/me/calendarView"

        try:
            while url:
                response = requests.get(url, headers=self.headers, params=params)
                self._handle_response_errors(response)

                data = response.json()
                events = data.get("value", [])
                all_events.extend(events)

                # Check for next page
                url = data.get("@odata.nextLink")
                params = None  # Parameters are included in nextLink

        except ConnectionError as e:
            raise GraphAPIError(f"Network error: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise GraphAPIError(f"Request failed: {str(e)}")

        # Normalize events
        return [self._normalize_event(event) for event in all_events]

    def _build_calendar_query_params(
        self, start_date: date, end_date: date
    ) -> Dict[str, str]:
        """Build query parameters for calendar view."""
        # Convert dates to ISO format with time
        # Start is inclusive (beginning of day)
        start_datetime = datetime.combine(start_date, datetime.min.time()).replace(
            tzinfo=timezone.utc
        )
        # End is exclusive (beginning of next day)
        end_datetime = datetime.combine(end_date, datetime.min.time()).replace(
            tzinfo=timezone.utc
        )

        return {
            "startDateTime": start_datetime.isoformat().replace("+00:00", "Z"),
            "endDateTime": end_datetime.isoformat().replace("+00:00", "Z"),
            "$select": "id,subject,start,end,location,attendees,body,isAllDay,isCancelled,organizer",
            "$orderby": "start/dateTime",
            "$top": "50",  # Page size
        }

    def _handle_response_errors(self, response: requests.Response):
        """Handle HTTP errors from Graph API."""
        if response.status_code == 200:
            return

        try:
            error_data = response.json()
            error_message = error_data.get("error", {}).get("message", "Unknown error")
        except:
            error_message = f"HTTP {response.status_code}"

        if response.status_code == 401:
            raise GraphAPIError(
                f"Authentication failed: {error_message}", status_code=401
            )
        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise GraphAPIError(
                f"Rate limit exceeded: {error_message}",
                status_code=429,
                retry_after=retry_after,
            )
        else:
            raise GraphAPIError(
                f"API error: {error_message}", status_code=response.status_code
            )

    def _normalize_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize event data for consistent format."""
        # Parse start and end times
        start_dt = self._parse_datetime(event.get("start", {}))
        end_dt = self._parse_datetime(event.get("end", {}))

        # Extract location display name if it's a dict
        location = event.get("location", {})
        if isinstance(location, dict):
            location_str = location.get("displayName", "")
        else:
            location_str = str(location) if location else ""
            
        # Extract and convert body content
        body = event.get("body", {})
        if isinstance(body, dict):
            content_type = body.get("contentType", "text")
            body_content = body.get("content", "")
            
            # Convert HTML to markdown if needed
            if content_type.lower() == "html" and body_content:
                body_content = html_to_markdown(body_content)
        else:
            body_content = str(body) if body else ""

        return {
            "id": event.get("id"),
            "subject": event.get("subject", "Untitled"),
            "start_time": start_dt,
            "end_time": end_dt,
            "location": location_str,
            "location_data": location,  # Keep full location data if needed
            "attendees": event.get("attendees", []),
            "body": body_content,
            "body_data": body,  # Keep full body data if needed
            "is_all_day": event.get("isAllDay", False),
            "is_cancelled": event.get("isCancelled", False),
            "organizer": event.get("organizer", {}),
            "is_online_meeting": event.get("isOnlineMeeting", False),
            "online_meeting_url": self._extract_online_meeting_url(event),
            "raw_event": event,  # Keep original for reference
        }

    def _parse_datetime(self, datetime_info: Dict[str, str]) -> Optional[datetime]:
        """Parse datetime from Graph API format."""
        if not datetime_info:
            return None

        dt_str = datetime_info.get("dateTime")
        tz_str = datetime_info.get("timeZone", "UTC")

        if not dt_str:
            return None

        # Parse the datetime string
        # Graph API format: "2024-01-15T10:00:00.0000000"
        dt = datetime.fromisoformat(dt_str.replace(".0000000", ""))

        # Handle timezone
        if tz_str == "UTC" and dt.tzinfo is None:
            # Add UTC timezone if not present
            dt = dt.replace(tzinfo=timezone.utc)

        return dt
    
    def _extract_online_meeting_url(self, event: Dict[str, Any]) -> Optional[str]:
        """Extract online meeting URL from event data.
        
        Args:
            event: Raw event data from Graph API
            
        Returns:
            Online meeting URL if found
        """
        # Check for onlineMeeting property first
        online_meeting = event.get("onlineMeeting")
        if online_meeting and isinstance(online_meeting, dict):
            join_url = online_meeting.get("joinUrl")
            if join_url:
                return join_url
                
        # Check in body content for meeting links
        body = event.get("body", {})
        if isinstance(body, dict):
            content = body.get("content", "")
            if content:
                # Use the dedicated function to extract meeting URLs
                meeting_url = extract_meeting_url(content)
                if meeting_url:
                    return meeting_url
                    
        return None
