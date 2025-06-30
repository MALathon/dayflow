"""
Vault detection and structure analysis.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class VaultStructure:
    """Represents a detected vault structure."""
    type: str
    is_empty: bool = False
    locations: Dict[str, str] = None
    
    def __post_init__(self):
        if self.locations is None:
            self.locations = {}
    
    def get_location(self, location_type: str) -> str:
        """Get suggested location for a content type."""
        return self.locations.get(location_type, self._default_location(location_type))
    
    def _default_location(self, location_type: str) -> str:
        """Get default location for unknown types."""
        defaults = {
            'calendar_events': 'Calendar Events',
            'daily_notes': 'Daily Notes',
            'people': 'People',
            'gtd_inbox': 'Inbox'
        }
        return defaults.get(location_type, location_type.replace('_', ' ').title())


class VaultDetector:
    """Detect vault location and structure."""
    
    def find_obsidian_vaults(self) -> List[Path]:
        """Search common locations for Obsidian vaults.
        
        Returns:
            List of paths to Obsidian vaults
        """
        candidates = []
        
        # Common vault locations
        home = Path.home()
        search_paths = [
            home / "Documents" / "Obsidian",
            home / "Documents",
            home / "Obsidian", 
            home / "Desktop",
            home / "OneDrive" / "Documents",
            home / "Dropbox",
            home / "iCloud Drive" / "Obsidian",
            home,  # Some people put vaults in home
        ]
        
        # Also check current directory and parent
        search_paths.extend([Path.cwd(), Path.cwd().parent])
        
        for base_path in search_paths:
            if base_path.exists():
                # Look for .obsidian folders (max depth 3 to avoid long searches)
                for item in self._find_folders(base_path, '.obsidian', max_depth=3):
                    if item.is_dir():
                        vault_path = item.parent
                        if vault_path not in candidates:
                            candidates.append(vault_path)
        
        return sorted(candidates)
    
    def _find_folders(self, base_path: Path, name: str, max_depth: int = 3) -> List[Path]:
        """Find folders with specific name up to max depth."""
        results = []
        
        def search(path: Path, depth: int):
            if depth > max_depth:
                return
            
            try:
                for item in path.iterdir():
                    if item.name == name and item.is_dir():
                        results.append(item)
                    elif item.is_dir() and not item.name.startswith('.'):
                        search(item, depth + 1)
            except (PermissionError, OSError):
                pass
        
        search(base_path, 0)
        return results
    
    def analyze_vault(self, vault_path: Path) -> VaultStructure:
        """Detect existing organizational system.
        
        Args:
            vault_path: Path to the vault
            
        Returns:
            Detected vault structure
        """
        if not vault_path.exists():
            return VaultStructure(type="custom", is_empty=True)
        
        # Get all folders in vault
        folders = [f.name for f in vault_path.iterdir() if f.is_dir() and not f.name.startswith('.')]
        
        # Check if vault is empty
        if len(folders) == 0:
            return VaultStructure(type="custom", is_empty=True)
        
        # Check for PARA structure
        if self._is_para_structure(folders):
            return VaultStructure(
                type="para",
                locations={
                    'calendar_events': '1-Projects/_Meeting Notes',
                    'daily_notes': '2-Areas/Daily Notes',
                    'people': '3-Resources/People',
                    'gtd_inbox': '1-Projects/_Inbox',
                    'archive': '4-Archive'
                }
            )
        
        # Check for GTD structure
        if self._is_gtd_structure(folders):
            return VaultStructure(
                type="gtd",
                locations={
                    'calendar_events': '02-Projects/Meeting Notes',
                    'daily_notes': '05-Reference/Daily Notes',
                    'people': '05-Reference/People',
                    'gtd_inbox': '00-Inbox',
                    'gtd_next_actions': '01-Next Actions',
                    'gtd_projects': '02-Projects',
                    'gtd_waiting_for': '03-Waiting For'
                }
            )
        
        # Check for time-based structure
        if self._is_time_based_structure(folders):
            return VaultStructure(
                type="time_based",
                locations={
                    'calendar_events': 'Meetings',
                    'daily_notes': 'Daily Notes',
                    'weekly_notes': 'Weekly Notes',
                    'people': 'People'
                }
            )
        
        # Check for Zettelkasten structure
        if self._is_zettelkasten_structure(folders):
            return VaultStructure(
                type="zettelkasten",
                locations={
                    'calendar_events': 'fleeting/meetings',
                    'daily_notes': 'fleeting/daily',
                    'people': 'permanent/people',
                    'zettel_permanent': 'permanent',
                    'zettel_literature': 'literature',
                    'zettel_fleeting': 'fleeting'
                }
            )
        
        # Default to custom structure
        return VaultStructure(type="custom")
    
    def _is_para_structure(self, folders: List[str]) -> bool:
        """Check if folders match PARA method."""
        para_folders = ['1-Projects', '2-Areas', '3-Resources', '4-Archive']
        matches = sum(1 for f in para_folders if f in folders)
        return matches >= 3
    
    def _is_gtd_structure(self, folders: List[str]) -> bool:
        """Check if folders match GTD structure."""
        gtd_patterns = [r'0\d-\w+', r'Inbox', r'Next Actions', r'Projects', r'Waiting']
        matches = 0
        for folder in folders:
            for pattern in gtd_patterns:
                if re.match(pattern, folder, re.IGNORECASE):
                    matches += 1
                    break
        return matches >= 3
    
    def _is_time_based_structure(self, folders: List[str]) -> bool:
        """Check if folders match time-based structure."""
        time_patterns = ['Daily Notes', 'Weekly Notes', 'Monthly Notes', r'20\d\d']
        matches = 0
        for folder in folders:
            for pattern in time_patterns:
                if re.match(pattern, folder, re.IGNORECASE):
                    matches += 1
                    break
        return matches >= 2
    
    def _is_zettelkasten_structure(self, folders: List[str]) -> bool:
        """Check if folders match Zettelkasten structure."""
        zettel_folders = ['zettelkasten', 'permanent', 'literature', 'fleeting', 'index']
        matches = sum(1 for f in zettel_folders if f.lower() in [folder.lower() for folder in folders])
        return matches >= 2
    
    def find_meeting_notes(self, vault_path: Path) -> List[Path]:
        """Find existing meeting notes in vault.
        
        Args:
            vault_path: Path to the vault
            
        Returns:
            List of paths to meeting notes
        """
        meeting_patterns = [
            r'\d{4}-\d{2}-\d{2}.*[Mm]eeting',
            r'1[-:]1\s+with',
            r'[Tt]eam\s+[Ss]ync',
            r'[Ss]tandup',
            r'[Cc]lient\s+[Mm]eeting',
            r'[Pp]roject\s+[Rr]eview'
        ]
        
        meeting_notes = []
        
        # Search for markdown files
        for md_file in vault_path.rglob('*.md'):
            # Check if filename matches meeting patterns
            for pattern in meeting_patterns:
                if re.search(pattern, md_file.name):
                    meeting_notes.append(md_file)
                    break
        
        return sorted(meeting_notes)
    
    def suggest_calendar_location(self, vault_path: Path) -> List[str]:
        """Suggest locations for calendar events based on existing structure.
        
        Args:
            vault_path: Path to the vault
            
        Returns:
            List of suggested locations (relative paths)
        """
        suggestions = []
        
        # Look for existing meeting-related folders
        for folder in vault_path.rglob('*'):
            if folder.is_dir() and not folder.name.startswith('.'):
                folder_lower = folder.name.lower()
                if any(word in folder_lower for word in ['meeting', 'calendar', 'event', 'appointment']):
                    rel_path = folder.relative_to(vault_path)
                    suggestions.append(str(rel_path))
        
        # Add default suggestions
        if not suggestions:
            structure = self.analyze_vault(vault_path)
            suggestions.append(structure.get_location('calendar_events'))
        
        return suggestions
    
    def get_vault_stats(self, vault_path: Path) -> Dict[str, Any]:
        """Get statistics about a vault.
        
        Args:
            vault_path: Path to the vault
            
        Returns:
            Dictionary with vault statistics
        """
        stats = {
            'total_notes': 0,
            'total_files': 0,
            'folder_count': 0,
            'markdown_files': 0,
            'has_daily_notes': False,
            'has_templates': False
        }
        
        folders = set()
        
        for item in vault_path.rglob('*'):
            if item.name.startswith('.'):
                continue
                
            if item.is_file():
                stats['total_files'] += 1
                if item.suffix == '.md':
                    stats['markdown_files'] += 1
                    stats['total_notes'] += 1
            elif item.is_dir():
                folders.add(item)
                if 'daily' in item.name.lower():
                    stats['has_daily_notes'] = True
                if 'template' in item.name.lower():
                    stats['has_templates'] = True
        
        stats['folder_count'] = len(folders) + 1  # +1 for root folder
        
        return stats