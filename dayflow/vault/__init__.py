"""Vault management for Obsidian integration."""

from .config import VaultConfig, VaultConfigError
from .connection import VaultConnection
from .detector import VaultDetector
from .setup_wizard import VaultSetupWizard

__all__ = ['VaultConfig', 'VaultConfigError', 'VaultConnection', 'VaultDetector', 'VaultSetupWizard']