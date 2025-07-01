"""Integration test for HTML cleanup in calendar events."""

import pytest
from datetime import datetime, timezone

from dayflow.core.graph_client import GraphAPIClient
from dayflow.core.obsidian_formatter import ObsidianNoteFormatter


class TestHTMLCleanupIntegration:
    """Test the full integration of HTML cleanup from Graph API to Obsidian notes."""
    
    def test_complex_teams_meeting_full_flow(self):
        """Test processing a complex Teams meeting with HTML content."""
        # Create a mock GraphAPIClient and normalize an event
        client = GraphAPIClient("mock-token")
        
        # Raw event as it would come from Graph API
        raw_event = {
            "id": "AAMkAGI2TjA",
            "subject": "Weekly Team Sync",
            "start": {
                "dateTime": "2024-01-15T14:00:00.0000000",
                "timeZone": "Eastern Standard Time"
            },
            "end": {
                "dateTime": "2024-01-15T15:00:00.0000000",
                "timeZone": "Eastern Standard Time"
            },
            "location": {
                "displayName": "Microsoft Teams Meeting",
                "locationType": "default"
            },
            "body": {
                "contentType": "html",
                "content": """
                <html>
                <head>
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
                <style>
                @font-face {
                    font-family: 'Segoe UI';
                    src: url('chrome-extension://fonts/segoeui.ttf');
                }
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    font-size: 14px;
                    color: #333333;
                }
                .meeting-container {
                    background-color: #f4f4f4;
                    padding: 20px;
                    border-radius: 5px;
                }
                </style>
                </head>
                <body>
                <div class="meeting-container">
                <h2>Weekly Team Sync</h2>
                <p>Hello team,</p>
                <p>Please join us for our weekly sync meeting where we'll cover:</p>
                <ul>
                    <li><strong>Project Updates</strong>: Review progress on current initiatives</li>
                    <li><strong>Blockers</strong>: Discuss any issues or impediments</li>
                    <li><strong>Planning</strong>: Look ahead to next week's priorities</li>
                </ul>
                <p>Please come prepared with your updates!</p>
                <hr>
                <div style="width:100%;background-color:#e5e5e5;padding:10px;">
                    <p style="margin:0;"><strong>Join on your computer, mobile app or room device</strong></p>
                    <p style="margin:5px 0;">
                        <a href="https://teams.microsoft.com/l/meetup-join/19%3ameeting_NjM0ZTI4MjktMzQ1Yi00MTRmLWE5NDMtYzg5OTZkZDFiNGY0%40thread.v2/0?context=%7b%22Tid%22%3a%2272f988bf-86f1-41af-91ab-2d7cd011db47%22%2c%22Oid%22%3a%22f4d7b952-84d5-4643-9e5e-4fc98d86e9f0%22%7d" style="color:#0078d4;">
                        Click here to join the meeting
                        </a>
                    </p>
                    <p style="margin:5px 0;font-size:12px;">Meeting ID: 256 789 123 45</p>
                    <p style="margin:5px 0;font-size:12px;">Passcode: aBcDeF</p>
                    <div style="font-size:11px;color:#666666;margin-top:10px;">
                        <a href="https://aka.ms/JoinTeamsMeeting" style="color:#0078d4;">Download Teams</a> | 
                        <a href="https://teams.microsoft.com/meetingOptions/?organizerId=f4d7b952" style="color:#0078d4;">Meeting options</a>
                    </div>
                </div>
                <hr>
                <p style="font-size:12px;color:#666666;">
                If you're having trouble joining, contact IT support.<br>
                Phone Conference ID: 987-654-321#
                </p>
                </div>
                </body>
                </html>
                """
            },
            "attendees": [
                {
                    "type": "required",
                    "emailAddress": {
                        "name": "Sarah Johnson",
                        "address": "sarah.johnson@company.com"
                    }
                },
                {
                    "type": "required", 
                    "emailAddress": {
                        "name": "Mike Chen",
                        "address": "mike.chen@company.com"
                    }
                }
            ],
            "isOnlineMeeting": True,
            "isAllDay": False,
            "isCancelled": False
        }
        
        # Normalize the event
        normalized = client._normalize_event(raw_event)
        
        # Verify HTML was converted to clean markdown
        assert "## Weekly Team Sync" in normalized["body"]
        assert "Hello team," in normalized["body"]
        assert "- **Project Updates**: Review progress on current initiatives" in normalized["body"]
        assert "- **Blockers**: Discuss any issues or impediments" in normalized["body"]
        assert "- **Planning**: Look ahead to next week's priorities" in normalized["body"]
        
        # Verify style tags and CSS are removed
        assert "@font-face" not in normalized["body"]
        assert "font-family:" not in normalized["body"]
        assert "background-color:" not in normalized["body"]
        assert "<style>" not in normalized["body"]
        assert "<div>" not in normalized["body"]
        
        # Verify Teams boilerplate is simplified
        assert "Microsoft Teams meeting" in normalized["body"]
        assert "Meeting ID: 256 789 123" not in normalized["body"]
        
        # Verify meeting URL was extracted
        assert normalized["online_meeting_url"] == "https://teams.microsoft.com/l/meetup-join/19%3ameeting_NjM0ZTI4MjktMzQ1Yi00MTRmLWE5NDMtYzg5OTZkZDFiNGY0%40thread.v2/0?context=%7b%22Tid%22%3a%2272f988bf-86f1-41af-91ab-2d7cd011db47%22%2c%22Oid%22%3a%22f4d7b952-84d5-4643-9e5e-4fc98d86e9f0%22%7d"
        
        # Now format as Obsidian note
        formatter = ObsidianNoteFormatter()
        note_content = formatter.format_event(normalized, tags=["team-meeting"])
        
        # Verify the note has clean content
        assert "# Weekly Team Sync" in note_content
        assert "## Description" in note_content
        assert "Hello team," in note_content
        assert "- **Project Updates**" in note_content
        
        # Verify frontmatter has the meeting URL
        assert "online_meeting_url: https://teams.microsoft.com" in note_content
        assert "is_online_meeting: true" in note_content
        
        # Verify attendees are formatted correctly
        assert "[[Sarah Johnson]]" in note_content
        assert "[[Mike Chen]]" in note_content
        
        # Generate filename
        filename = formatter.generate_filename(normalized)
        assert filename == "2024-01-15 Weekly Team Sync.md"