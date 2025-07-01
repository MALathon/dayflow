"""
Vault connection and file operations.
"""

import re
from datetime import date
from pathlib import Path
from typing import List, Optional

from .config import VaultConfig


class VaultConnection:
    """Generic vault connection that works with any structure."""

    def __init__(self, config: VaultConfig):
        """Initialize vault connection.

        Args:
            config: Vault configuration object
        """
        self.config = config
        self.vault_path = config.vault_path

    def ensure_folder_exists(self, folder_type: str) -> Path:
        """Create folder if it doesn't exist.

        Args:
            folder_type: Type of folder (e.g. 'calendar_events', 'daily_notes')

        Returns:
            Path to the folder

        Raises:
            ValueError: If folder_type is not configured
        """
        folder_path = self.config.get_location(folder_type)
        if folder_path is None:
            raise ValueError(f"Location type '{folder_type}' not configured")

        folder_path.mkdir(parents=True, exist_ok=True)
        return folder_path

    def write_note(
        self,
        content: str,
        filename: str,
        folder_type: str = "calendar_events",
        date_folder: Optional[date] = None,
    ) -> Path:
        """Write a note to the appropriate location.

        Args:
            content: Note content
            filename: Name of the file
            folder_type: Type of folder to write to
            date_folder: Optional date for organizing into date-based folders

        Returns:
            Path to the written file
        """
        # Sanitize filename
        safe_filename = self._sanitize_filename(filename)

        # Ensure base folder exists
        folder = self.ensure_folder_exists(folder_type)

        # Apply folder organization if configured and date provided
        if date_folder and folder_type == "calendar_events":
            folder_org = self.config.get_setting("calendar.folder_organization")
            if folder_org:
                folder = self._get_date_folder(folder, date_folder, folder_org)
                folder.mkdir(parents=True, exist_ok=True)

        # Write the file
        file_path = folder / safe_filename
        file_path.write_text(content, encoding="utf-8")

        return file_path

    def read_note(
        self, filename: str, folder_type: str = "calendar_events"
    ) -> Optional[str]:
        """Read a note from the vault.

        Args:
            filename: Name of the file to read
            folder_type: Type of folder to read from

        Returns:
            Note content or None if not found
        """
        try:
            folder = self.config.get_location(folder_type)
            if folder is None:
                return None

            file_path = folder / filename
            if file_path.exists():
                return file_path.read_text(encoding="utf-8")
            return None
        except Exception:
            return None

    def note_exists(self, filename: str, folder_type: str = "calendar_events") -> bool:
        """Check if a note exists.

        Args:
            filename: Name of the file
            folder_type: Type of folder to check

        Returns:
            True if note exists
        """
        try:
            folder = self.config.get_location(folder_type)
            if folder is None:
                return False

            file_path = folder / filename
            return file_path.exists()
        except Exception:
            return False

    def list_notes(self, folder_type: str = "calendar_events") -> List[Path]:
        """List all notes in a folder.

        Args:
            folder_type: Type of folder to list

        Returns:
            List of note paths
        """
        try:
            folder = self.config.get_location(folder_type)
            if folder is None or not folder.exists():
                return []

            # Find all .md files
            return sorted([f for f in folder.iterdir() if f.suffix == ".md"])
        except Exception:
            return []

    def get_note_path(
        self, filename: str, folder_type: str = "calendar_events"
    ) -> Path:
        """Get the full path for a note.

        Args:
            filename: Name of the file
            folder_type: Type of folder

        Returns:
            Full path to the note
        """
        folder = self.config.get_location(folder_type)
        if folder is None:
            raise ValueError(f"Location type '{folder_type}' not configured")
        return folder / filename

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Replace invalid characters
        invalid_chars = r'[<>:"/\\|?*]'
        sanitized = re.sub(invalid_chars, "-", filename)

        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip(". ")

        # Ensure it ends with .md if it doesn't have an extension
        if not sanitized.endswith(".md"):
            sanitized += ".md"

        return sanitized

    def _get_date_folder(
        self, base_folder: Path, event_date: date, pattern: str
    ) -> Path:
        """Get folder path based on date organization pattern.

        Args:
            base_folder: Base folder for events
            event_date: Date of the event
            pattern: Organization pattern (e.g., "year/month/day", "year/week")

        Returns:
            Path to the date-organized folder
        """
        # Handle both Unix and Windows path separators
        parts = pattern.lower().replace("\\", "/").split("/")
        folder = base_folder

        for part in parts:
            if part == "year":
                folder = folder / f"{event_date.year:04d}"
            elif part == "month":
                folder = folder / f"{event_date.month:02d}"
            elif part == "day":
                folder = folder / f"{event_date.day:02d}"
            elif part == "week":
                # ISO week number
                week_num = event_date.isocalendar()[1]
                folder = folder / f"W{week_num:02d}"

        return folder
