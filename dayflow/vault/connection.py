"""
Vault connection and file operations.
"""

import re
from pathlib import Path
from typing import Optional, List

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
    
    def write_note(self, content: str, filename: str, folder_type: str = 'calendar_events') -> Path:
        """Write a note to the appropriate location.
        
        Args:
            content: Note content
            filename: Name of the file
            folder_type: Type of folder to write to
            
        Returns:
            Path to the written file
        """
        # Sanitize filename
        safe_filename = self._sanitize_filename(filename)
        
        # Ensure folder exists
        folder = self.ensure_folder_exists(folder_type)
        
        # Write the file
        file_path = folder / safe_filename
        file_path.write_text(content, encoding='utf-8')
        
        return file_path
    
    def read_note(self, filename: str, folder_type: str = 'calendar_events') -> Optional[str]:
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
                return file_path.read_text(encoding='utf-8')
            return None
        except Exception:
            return None
    
    def note_exists(self, filename: str, folder_type: str = 'calendar_events') -> bool:
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
    
    def list_notes(self, folder_type: str = 'calendar_events') -> List[Path]:
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
            return sorted([f for f in folder.iterdir() if f.suffix == '.md'])
        except Exception:
            return []
    
    def get_note_path(self, filename: str, folder_type: str = 'calendar_events') -> Path:
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
        sanitized = re.sub(invalid_chars, '-', filename)
        
        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip('. ')
        
        # Ensure it ends with .md if it doesn't have an extension
        if not sanitized.endswith('.md'):
            sanitized += '.md'
        
        return sanitized