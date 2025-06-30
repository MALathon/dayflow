"""
Test cases for vault detection and structure analysis.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

from dayflow.vault.detector import VaultDetector, VaultStructure


class TestVaultDetector:
    """Test vault detection functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.detector = VaultDetector()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_find_obsidian_vaults_in_common_locations(self):
        """Test finding Obsidian vaults in common locations."""
        # Create mock vaults
        vault1 = Path(self.temp_dir) / "Documents" / "ObsidianVault"
        vault1.mkdir(parents=True)
        (vault1 / ".obsidian").mkdir()
        
        vault2 = Path(self.temp_dir) / "Work" / "Notes"
        vault2.mkdir(parents=True)
        (vault2 / ".obsidian").mkdir()
        
        # Also create a non-vault folder
        non_vault = Path(self.temp_dir) / "Documents" / "RegularFolder"
        non_vault.mkdir(parents=True)
        
        with patch('pathlib.Path.home', return_value=Path(self.temp_dir)):
            vaults = self.detector.find_obsidian_vaults()
        
        # Should find both vaults but not the regular folder
        vault_paths = [str(v) for v in vaults]
        assert str(vault1) in vault_paths
        assert str(vault2) in vault_paths
        assert str(non_vault) not in vault_paths
        assert len(vaults) == 2
    
    def test_detect_para_structure(self):
        """Test detecting PARA method structure."""
        vault = Path(self.temp_dir) / "vault"
        vault.mkdir()
        
        # Create PARA folders
        (vault / "1-Projects").mkdir()
        (vault / "2-Areas").mkdir()
        (vault / "3-Resources").mkdir()
        (vault / "4-Archive").mkdir()
        
        structure = self.detector.analyze_vault(vault)
        
        assert structure.type == "para"
        assert structure.get_location('calendar_events') == "1-Projects/_Meeting Notes"
    
    def test_detect_gtd_structure(self):
        """Test detecting GTD structure."""
        vault = Path(self.temp_dir) / "vault"
        vault.mkdir()
        
        # Create GTD folders
        (vault / "00-Inbox").mkdir()
        (vault / "01-Next Actions").mkdir()
        (vault / "02-Projects").mkdir()
        (vault / "03-Waiting For").mkdir()
        
        structure = self.detector.analyze_vault(vault)
        
        assert structure.type == "gtd"
        assert structure.get_location('calendar_events') == "02-Projects/Meeting Notes"
        assert structure.get_location('gtd_inbox') == "00-Inbox"
    
    def test_detect_time_based_structure(self):
        """Test detecting time-based structure."""
        vault = Path(self.temp_dir) / "vault"
        vault.mkdir()
        
        # Create time-based folders
        (vault / "Daily Notes").mkdir()
        (vault / "Weekly Notes").mkdir()
        (vault / "2024").mkdir()
        (vault / "2024" / "01-January").mkdir()
        
        structure = self.detector.analyze_vault(vault)
        
        assert structure.type == "time_based"
        assert structure.get_location('daily_notes') == "Daily Notes"
    
    def test_detect_zettelkasten_structure(self):
        """Test detecting Zettelkasten structure."""
        vault = Path(self.temp_dir) / "vault"
        vault.mkdir()
        
        # Create Zettelkasten folders
        (vault / "zettelkasten").mkdir()
        (vault / "literature").mkdir()
        (vault / "permanent").mkdir()
        
        structure = self.detector.analyze_vault(vault)
        
        assert structure.type == "zettelkasten"
        assert structure.get_location('zettel_permanent') == "permanent"
    
    def test_detect_custom_structure(self):
        """Test fallback to custom structure for unknown layouts."""
        vault = Path(self.temp_dir) / "vault"
        vault.mkdir()
        
        # Create some random folders
        (vault / "My Notes").mkdir()
        (vault / "Work Stuff").mkdir()
        (vault / "Personal").mkdir()
        
        structure = self.detector.analyze_vault(vault)
        
        assert structure.type == "custom"
        # Custom structure should suggest sensible defaults
        assert structure.get_location('calendar_events') == "Calendar Events"
    
    def test_find_existing_meeting_notes(self):
        """Test finding existing meeting notes in vault."""
        vault = Path(self.temp_dir) / "vault"
        vault.mkdir()
        
        # Create various notes
        (vault / "2024-01-15 Team Meeting.md").write_text("# Team Meeting")
        (vault / "1-1 with John.md").write_text("# 1:1")
        (vault / "Project Planning.md").write_text("# Planning")
        (vault / "Random Note.md").write_text("# Random")
        
        # Create nested meeting note
        subfolder = vault / "Work"
        subfolder.mkdir()
        (subfolder / "2024-01-10 Client Meeting.md").write_text("# Client")
        
        meeting_notes = self.detector.find_meeting_notes(vault)
        
        # Should find notes that look like meetings
        note_names = [n.name for n in meeting_notes]
        assert "2024-01-15 Team Meeting.md" in note_names
        assert "1-1 with John.md" in note_names
        assert "2024-01-10 Client Meeting.md" in note_names
        assert "Random Note.md" not in note_names
        assert len(meeting_notes) == 3
    
    def test_suggest_vault_locations(self):
        """Test suggesting locations for calendar events based on existing structure."""
        vault = Path(self.temp_dir) / "vault"
        vault.mkdir()
        
        # Create some folders
        (vault / "Work").mkdir()
        (vault / "Work" / "Meetings").mkdir()
        (vault / "Personal").mkdir()
        (vault / "Archive").mkdir()
        
        suggestions = self.detector.suggest_calendar_location(vault)
        
        # Should suggest the existing Meetings folder first
        assert len(suggestions) > 0
        assert "Work/Meetings" in suggestions[0]
    
    def test_empty_vault_detection(self):
        """Test handling of empty vaults."""
        vault = Path(self.temp_dir) / "empty_vault"
        vault.mkdir()
        (vault / ".obsidian").mkdir()
        
        structure = self.detector.analyze_vault(vault)
        
        # Should return custom structure for empty vault
        assert structure.type == "custom"
        assert structure.is_empty == True
    
    def test_vault_statistics(self):
        """Test gathering statistics about a vault."""
        vault = Path(self.temp_dir) / "vault"
        vault.mkdir()
        
        # Create various files
        (vault / "note1.md").write_text("# Note 1")
        (vault / "note2.md").write_text("# Note 2")
        (vault / "document.pdf").write_text("PDF content")
        
        subfolder = vault / "subfolder"
        subfolder.mkdir()
        (subfolder / "note3.md").write_text("# Note 3")
        
        stats = self.detector.get_vault_stats(vault)
        
        assert stats['total_notes'] == 3
        assert stats['total_files'] == 4
        assert stats['folder_count'] == 2  # root + subfolder
        assert 'markdown_files' in stats
        assert stats['markdown_files'] == 3