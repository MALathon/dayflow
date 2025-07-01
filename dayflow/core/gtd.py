"""
GTD (Getting Things Done) system implementation.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from dayflow.vault import VaultConfig, VaultConnection


class GTDSystem:
    """Manages GTD workflow in Obsidian vault."""

    def __init__(self, vault_connection: Optional[VaultConnection] = None):
        """Initialize GTD system.

        Args:
            vault_connection: Connection to vault for note operations
        """
        self.vault_connection = vault_connection
        self.config = VaultConfig() if vault_connection else None

    def get_inbox_items(self) -> List[Dict]:
        """Get all items from GTD inbox.

        Returns:
            List of inbox items with metadata
        """
        if not self.vault_connection:
            return []

        inbox_path = self.config.get_location("gtd_inbox") if self.config else None
        if not inbox_path or not inbox_path.exists():
            return []

        items: List[Dict[str, Any]] = []
        for file in inbox_path.glob("*.md"):
            # Read file to get metadata
            # content = file.read_text()  # TODO: Parse metadata when needed
            items.append(
                {
                    "id": len(items) + 1,
                    "content": file.stem,
                    "file_path": file,
                    "created": datetime.fromtimestamp(file.stat().st_ctime),
                }
            )

        return sorted(items, key=lambda x: x["created"], reverse=True)

    def add_to_inbox(self, content: str, source: Optional[str] = None) -> Path:
        """Add item to GTD inbox.

        Args:
            content: The content to add
            source: Optional source of the item (e.g., "Meeting: Project Review")

        Returns:
            Path to created file
        """
        if not self.vault_connection:
            raise ValueError("No vault connection configured")

        timestamp = datetime.now()

        # Build note content
        frontmatter_lines = [
            "---",
            f"created: {timestamp.isoformat()}",
            "type: inbox",
            "status: pending",
            "tags: [gtd, inbox]",
        ]

        if source:
            frontmatter_lines.append(f'source: "{source}"')

        frontmatter_lines.append("---")

        note_content = "\n".join(frontmatter_lines) + f"\n\n# {content}\n\n"

        # Generate filename
        safe_content = content[:50].replace("/", "-").replace(":", "-")
        filename = f"{timestamp.strftime('%Y-%m-%d-%H%M')} {safe_content}.md"

        # Write to inbox
        return self.vault_connection.write_note(note_content, filename, "gtd_inbox")

    def process_inbox_item(
        self,
        item_id: int,
        action: str,
        context: Optional[str] = None,
        project: Optional[str] = None,
    ) -> bool:
        """Process an inbox item.

        Args:
            item_id: ID of the inbox item
            action: Action to take (next_action, project, waiting_for,
                someday, reference, trash)
            context: Optional GTD context (e.g., @phone, @computer)
            project: Optional project to assign to

        Returns:
            True if processed successfully
        """
        items = self.get_inbox_items()

        # Find the item
        item = next((i for i in items if i["id"] == item_id), None)
        if not item:
            return False

        # Based on action, move to appropriate location
        # This is a simplified implementation
        # In a real implementation, we'd move files and update metadata

        return True


class WeeklyReviewGenerator:
    """Generates weekly review notes."""

    def __init__(self, vault_connection: Optional[VaultConnection] = None):
        """Initialize review generator."""
        self.vault_connection = vault_connection
        self.config = VaultConfig() if vault_connection else None

    def generate(self, week_start: Optional[datetime] = None) -> str:
        """Generate weekly review content.

        Args:
            week_start: Start of the week to review (defaults to current week)

        Returns:
            Markdown content for weekly review
        """
        if not week_start:
            today = datetime.now()
            days_since_monday = today.weekday()
            week_start = today.replace(
                hour=0, minute=0, second=0, microsecond=0
            ) - timedelta(days=days_since_monday)

        week_end = week_start + timedelta(days=6)

        content = f"""---
date: {datetime.now().strftime('%Y-%m-%d')}
type: weekly-review
week_start: {week_start.strftime('%Y-%m-%d')}
week_end: {week_end.strftime('%Y-%m-%d')}
tags: [gtd, weekly-review]
---

# Weekly Review - Week of {week_start.strftime('%B %d, %Y')}

## 🎯 Get Clear

### 📥 Inbox Processing
- [ ] Process email inbox to zero
- [ ] Process Obsidian inbox
- [ ] Process physical inbox
- [ ] Review voice memos and notes

### 📋 Review Lists
- [ ] Review Next Actions list
- [ ] Review Projects list
- [ ] Review Waiting For list
- [ ] Review Someday/Maybe list

## 🔄 Get Current

### 📅 Calendar Review
- [ ] Review past week's calendar
- [ ] Review upcoming week's calendar
- [ ] Capture any actions from meetings

### 🎯 Project Review
<!-- Review each active project -->

## 🚀 Get Creative

### 💡 Someday/Maybe Review
- [ ] Review Someday/Maybe list
- [ ] Add new ideas
- [ ] Move items to active if ready

### 🎨 Mind Sweep
<!-- Capture any loose thoughts or ideas -->

## 📊 Week Stats
- Meetings attended:
- Tasks completed:
- Projects advanced:

## 🎉 Wins This Week


## 📝 Lessons Learned


## 🎯 Top Priorities for Next Week
1.
2.
3.

"""
        return content

    def create_review(self, week_start: Optional[datetime] = None) -> Path:
        """Create weekly review note in vault.

        Args:
            week_start: Start of week to review

        Returns:
            Path to created review note
        """
        if not self.vault_connection:
            raise ValueError("No vault connection configured")

        content = self.generate(week_start)

        # Generate filename
        if not week_start:
            today = datetime.now()
            days_since_monday = today.weekday()
            week_start = today - timedelta(days=days_since_monday)

        filename = f"Weekly Review - {week_start.strftime('%Y-%m-%d')}.md"

        # Write to appropriate location
        # Try GTD location first, fall back to daily notes
        location = (
            "gtd_projects"
            if self.config and self.config.get_location("gtd_projects")
            else "daily_notes"
        )

        return self.vault_connection.write_note(content, filename, location)
