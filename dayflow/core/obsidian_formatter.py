"""Formatter for creating Obsidian notes from calendar events."""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional


class ObsidianNoteFormatter:
    """Formats calendar events as Obsidian notes with frontmatter."""
    
    def format_event(self, event: Dict[str, Any], tags: Optional[List[str]] = None) -> str:
        """Format a calendar event as an Obsidian note.
        
        Args:
            event: Calendar event data
            tags: Additional tags to include
            
        Returns:
            Formatted note content with frontmatter
        """
        # Build frontmatter
        frontmatter = self._build_frontmatter(event, tags)
        
        # Build note content
        content = self._build_content(event)
        
        return f"{frontmatter}\n{content}"
    
    def generate_filename(self, event: Dict[str, Any]) -> str:
        """Generate a filename for the event.
        
        Args:
            event: Calendar event data
            
        Returns:
            Sanitized filename with date prefix
        """
        # Get date prefix
        start_time = event['start_time']
        date_prefix = start_time.strftime('%Y-%m-%d')
        
        # Sanitize subject
        subject = event.get('subject', 'Untitled')
        # Replace invalid characters
        safe_subject = re.sub(r'[<>:"/\\|?*]', '-', subject)
        # Trim to reasonable length
        if len(safe_subject) > 80:
            safe_subject = safe_subject[:77] + '...'
        
        return f"{date_prefix} {safe_subject}.md"
    
    def _build_frontmatter(self, event: Dict[str, Any], tags: Optional[List[str]] = None) -> str:
        """Build YAML frontmatter for the note.
        
        Args:
            event: Calendar event data
            tags: Additional tags
            
        Returns:
            YAML frontmatter string
        """
        frontmatter_parts = ['---']
        
        # Title
        title = self._escape_yaml_value(event.get('subject', 'Untitled'))
        frontmatter_parts.append(f'title: {title}')
        
        # Date
        date_str = event['start_time'].strftime('%Y-%m-%d')
        frontmatter_parts.append(f'date: {date_str}')
        
        # Times
        frontmatter_parts.append(f'start_time: {event["start_time"].isoformat()}')
        if 'end_time' in event:
            frontmatter_parts.append(f'end_time: {event["end_time"].isoformat()}')
        
        # Type
        frontmatter_parts.append('type: meeting')
        
        # All day
        if event.get('is_all_day', False):
            frontmatter_parts.append('is_all_day: true')
        
        # Location
        if 'location' in event:
            location = self._escape_yaml_value(event['location'])
            frontmatter_parts.append(f'location: {location}')
        
        # Online meeting
        if event.get('is_online_meeting', False):
            frontmatter_parts.append('is_online_meeting: true')
            if 'online_meeting_url' in event:
                url = event['online_meeting_url']
                frontmatter_parts.append(f'online_meeting_url: {url}')
        
        # Recurring
        if event.get('is_recurring', False):
            frontmatter_parts.append('is_recurring: true')
            if 'recurrence_pattern' in event:
                pattern = self._escape_yaml_value(event['recurrence_pattern'])
                frontmatter_parts.append(f'recurrence_pattern: {pattern}')
        
        # Cancelled
        if event.get('is_cancelled', False):
            frontmatter_parts.append('is_cancelled: true')
            frontmatter_parts.append('status: cancelled')
        
        # Tags
        all_tags = ['calendar-sync']
        if tags:
            all_tags.extend(tags)
        frontmatter_parts.append(f'tags: [{", ".join(all_tags)}]')
        
        frontmatter_parts.append('---')
        return '\n'.join(frontmatter_parts)
    
    def _build_content(self, event: Dict[str, Any]) -> str:
        """Build the main content of the note.
        
        Args:
            event: Calendar event data
            
        Returns:
            Markdown content
        """
        content_parts = []
        
        # Title
        content_parts.append(f"# {event.get('subject', 'Untitled')}")
        content_parts.append('')
        
        # Cancelled warning
        if event.get('is_cancelled', False):
            content_parts.append('> ⚠️ This event has been cancelled')
            content_parts.append('')
        
        # Event details section
        content_parts.append('## Event Details')
        content_parts.append('')
        
        # Date
        date_str = event['start_time'].strftime('%Y-%m-%d')
        content_parts.append(f'**Date**: {date_str}')
        
        # Time
        if event.get('is_all_day', False):
            content_parts.append('**Time**: All day')
        else:
            start_str = event['start_time'].strftime('%H:%M')
            timezone_str = event['start_time'].strftime('%Z')
            if 'end_time' in event:
                end_str = event['end_time'].strftime('%H:%M')
                content_parts.append(f'**Time**: {start_str} - {end_str} {timezone_str}')
            else:
                content_parts.append(f'**Time**: {start_str} {timezone_str}')
        
        # Location
        if 'location' in event:
            content_parts.append(f'**Location**: {event["location"]}')
        
        # Recurrence
        if event.get('is_recurring', False) and 'recurrence_pattern' in event:
            content_parts.append(f'**Recurrence**: {event["recurrence_pattern"]}')
        
        # Online meeting link
        if event.get('is_online_meeting', False) and 'online_meeting_url' in event:
            content_parts.append('')
            content_parts.append(f'📞 [Join Meeting]({event["online_meeting_url"]})')
        
        content_parts.append('')
        
        # Attendees
        if 'attendees' in event and event['attendees']:
            content_parts.append('## Attendees')
            content_parts.append('')
            for attendee in event['attendees']:
                name = attendee.get('name', attendee.get('email', 'Unknown'))
                # Use wiki links for attendees
                content_parts.append(f'- [[{name}]]')
            content_parts.append('')
        
        # Description/Body
        if 'body' in event and event['body']:
            content_parts.append('## Description')
            content_parts.append('')
            content_parts.append(event['body'])
            content_parts.append('')
        
        # Notes section
        content_parts.append('## Notes')
        content_parts.append('')
        content_parts.append('_Add your notes here_')
        content_parts.append('')
        
        # Action items section
        content_parts.append('## Action Items')
        content_parts.append('')
        content_parts.append('- [ ] ')
        content_parts.append('')
        
        return '\n'.join(content_parts)
    
    def _escape_yaml_value(self, value: str) -> str:
        """Escape a value for YAML frontmatter.
        
        Args:
            value: Value to escape
            
        Returns:
            Properly quoted/escaped value
        """
        # If value contains special characters, quote it
        if any(char in value for char in [':', '"', "'", '\n', '#', '[', ']', '{', '}', '|', '>', '-']):
            # Escape double quotes and newlines
            escaped = value.replace('"', '\\"').replace('\n', '\\n')
            return f'"{escaped}"'
        return value