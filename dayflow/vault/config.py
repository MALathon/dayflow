"""
Vault configuration management.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List


class VaultConfigError(Exception):
    """Error in vault configuration."""
    pass


class VaultConfig:
    """Manages vault configuration and paths."""
    
    DEFAULT_CONFIG = {
        'vault': {
            'path': '',
            'locations': {
                'calendar_events': 'Calendar Events',
                'daily_notes': 'Daily Notes',
                'people': 'People',
                'gtd_inbox': 'Inbox',
                'zettel_permanent': 'Permanent Notes'
            }
        }
    }
    
    TEMPLATE_CONFIGS = {
        'para': {
            'locations': {
                'calendar_events': '1-Projects/_Meeting Notes',
                'daily_notes': '2-Areas/Daily Notes',
                'people': '3-Resources/People',
                'gtd_inbox': '1-Projects/_Inbox',
                'archive': '4-Archive'
            }
        },
        'gtd': {
            'locations': {
                'calendar_events': '05-Reference/Meeting Notes',
                'daily_notes': '05-Reference/Daily Notes',
                'people': '05-Reference/People',
                'gtd_inbox': '00-Inbox',
                'gtd_next_actions': '01-Next Actions',
                'gtd_projects': '02-Projects',
                'gtd_waiting_for': '03-Waiting For',
                'gtd_someday': '04-Someday Maybe'
            }
        },
        'time_based': {
            'locations': {
                'calendar_events': 'Meetings/{year}/{month}',
                'daily_notes': 'Daily Notes/{year}/{month}',
                'people': 'People',
                'archive': 'Archive/{year}'
            }
        },
        'zettelkasten': {
            'locations': {
                'calendar_events': 'fleeting/meetings',
                'daily_notes': 'fleeting/daily',
                'people': 'permanent/people',
                'zettel_literature': 'literature',
                'zettel_permanent': 'permanent',
                'zettel_fleeting': 'fleeting'
            }
        }
    }
    
    def __init__(self):
        """Initialize configuration."""
        self.config_path = self._find_config()
        if not self.config_path.exists():
            self._create_default_config()
        self.config = self._load_config()
    
    def _find_config(self) -> Path:
        """Find configuration file in standard locations."""
        # Check home directory first
        home_config = Path.home() / '.dayflow' / 'config.yaml'
        if home_config.exists():
            return home_config
        
        # Check current directory
        local_config = Path.cwd() / '.dayflow' / 'config.yaml'
        if local_config.exists():
            return local_config
        
        # Default to home directory
        return home_config
    
    def _create_default_config(self):
        """Create default configuration file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(self.DEFAULT_CONFIG, f, default_flow_style=False)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f) or {}
    
    @property
    def vault_path(self) -> Path:
        """Get the configured vault path."""
        path = self.config.get('vault', {}).get('path', '')
        if not path:
            raise VaultConfigError("Vault path not configured. Run 'dayflow vault init' to set up.")
        return Path(path)
    
    def get_location(self, location_type: str) -> Optional[Path]:
        """Get path for specific content type."""
        locations = self.config.get('vault', {}).get('locations', {})
        rel_path = locations.get(location_type)
        
        if not rel_path:
            return None
        
        try:
            return self.vault_path / rel_path
        except VaultConfigError:
            return None
    
    def validate(self):
        """Validate that configuration is correct."""
        # Check vault path exists
        if not self.vault_path.exists():
            raise VaultConfigError(f"Vault path does not exist: {self.vault_path}")
        
        # Check it looks like an Obsidian vault
        obsidian_folder = self.vault_path / '.obsidian'
        if not obsidian_folder.exists():
            raise VaultConfigError(f"Path doesn't appear to be an Obsidian vault (no .obsidian folder): {self.vault_path}")
    
    def set_vault_path(self, path: str):
        """Update the vault path."""
        self.config.setdefault('vault', {})['path'] = str(path)
        self._save_config()
    
    def set_location(self, location_type: str, path: str):
        """Set path for a specific location type."""
        self.config.setdefault('vault', {}).setdefault('locations', {})[location_type] = path
        self._save_config()
    
    def _save_config(self):
        """Save configuration to file."""
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
    
    def get_template(self, template_name: str) -> Dict[str, Any]:
        """Get a configuration template."""
        if template_name not in self.TEMPLATE_CONFIGS:
            raise ValueError(f"Unknown template: {template_name}")
        return self.TEMPLATE_CONFIGS[template_name].copy()
    
    def list_templates(self) -> List[str]:
        """List available configuration templates."""
        return list(self.TEMPLATE_CONFIGS.keys())
    
    def apply_template(self, template_name: str):
        """Apply a template to the current configuration."""
        template = self.get_template(template_name)
        self.config.setdefault('vault', {}).update(template)
        self._save_config()