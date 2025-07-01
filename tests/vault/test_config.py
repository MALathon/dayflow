"""
Test cases for vault configuration management.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest
import yaml

from dayflow.vault.config import VaultConfig, VaultConfigError


class TestVaultConfig:
    """Test vault configuration functionality."""

    def test_find_config_in_home_directory(self):
        """Test finding config in user's home directory."""
        # Create a temporary directory structure
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            home_dir = Path(tmpdir) / "home"
            config_dir = home_dir / ".dayflow"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.yaml"
            config_file.write_text("vault:\n  path: /test/vault")

            with patch("pathlib.Path.home", return_value=home_dir):
                config = VaultConfig()
                assert config.config_path == config_file

    def test_find_config_in_current_directory(self):
        """Test finding config in current working directory."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            home_dir = Path(tmpdir) / "home"
            project_dir = Path(tmpdir) / "project"
            project_dir.mkdir(parents=True)

            # Create config in project directory, not home
            config_dir = project_dir / ".dayflow"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.yaml"
            config_file.write_text("vault:\n  path: /test/vault")

            with patch("pathlib.Path.home", return_value=home_dir):
                with patch("pathlib.Path.cwd", return_value=project_dir):
                    config = VaultConfig()
                    assert config.config_path == config_file

    def test_create_default_config_if_none_exists(self):
        """Test creating default config when none exists."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            home_dir = Path(tmpdir) / "home"
            home_dir.mkdir()

            with patch("pathlib.Path.home", return_value=home_dir):
                config = VaultConfig()

                # Check that config was created
                expected_path = home_dir / ".dayflow" / "config.yaml"
                assert expected_path.exists()

                # Check content
                content = yaml.safe_load(expected_path.read_text())
                assert "vault" in content
                assert "path" in content["vault"]
                assert "locations" in content["vault"]

    def test_load_existing_config(self):
        """Test loading an existing configuration file."""
        config_data = {
            "vault": {
                "path": "/Users/test/MyVault",
                "locations": {
                    "calendar_events": "Meetings",
                    "daily_notes": "Daily Notes",
                    "people": "People",
                },
            }
        }

        with patch("builtins.open", mock_open(read_data=yaml.dump(config_data))):
            with patch("pathlib.Path.exists", return_value=True):
                config = VaultConfig()

                assert config.vault_path == Path("/Users/test/MyVault")
                assert config.get_location("calendar_events") == Path(
                    "/Users/test/MyVault/Meetings"
                )
                assert config.get_location("daily_notes") == Path(
                    "/Users/test/MyVault/Daily Notes"
                )

    def test_vault_path_not_configured(self):
        """Test handling when vault path is not configured."""
        with patch("builtins.open", mock_open(read_data="vault: {}")):
            with patch("pathlib.Path.exists", return_value=True):
                config = VaultConfig()

                with pytest.raises(VaultConfigError, match="Vault path not configured"):
                    _ = config.vault_path

    def test_validate_vault_path_exists(self):
        """Test validation that configured vault path exists."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            home_dir = Path(tmpdir) / "home"
            config_dir = home_dir / ".dayflow"
            config_dir.mkdir(parents=True)

            # Create config pointing to nonexistent vault
            config_file = config_dir / "config.yaml"
            config_file.write_text("vault:\n  path: /nonexistent/path")

            with patch("pathlib.Path.home", return_value=home_dir):
                config = VaultConfig()
                with pytest.raises(VaultConfigError, match="Vault path does not exist"):
                    config.validate()

    def test_get_location_with_nested_paths(self):
        """Test getting locations with nested folder structures."""
        config_data = {
            "vault": {
                "path": "/Users/test/Vault",
                "locations": {
                    "calendar_events": "1-Projects/Work/Meetings",
                    "gtd_inbox": "00-Inbox",
                },
            }
        }

        with patch("builtins.open", mock_open(read_data=yaml.dump(config_data))):
            with patch("pathlib.Path.exists", return_value=True):
                config = VaultConfig()

                assert config.get_location("calendar_events") == Path(
                    "/Users/test/Vault/1-Projects/Work/Meetings"
                )
                assert config.get_location("gtd_inbox") == Path(
                    "/Users/test/Vault/00-Inbox"
                )

    def test_get_unconfigured_location_returns_none(self):
        """Test that unconfigured location types return None."""
        config_data = {"vault": {"path": "/Users/test/Vault"}}

        with patch("builtins.open", mock_open(read_data=yaml.dump(config_data))):
            with patch("pathlib.Path.exists", return_value=True):
                config = VaultConfig()

                assert config.get_location("undefined_type") is None

    def test_update_config(self):
        """Test updating configuration values."""
        initial_config = {"vault": {"path": "/old/path"}}

        with patch("builtins.open", mock_open(read_data=yaml.dump(initial_config))):
            with patch("pathlib.Path.exists", return_value=True):
                config = VaultConfig()

                # Update vault path
                with patch("builtins.open", mock_open()) as mock_file:
                    config.set_vault_path("/new/path")

                    # Should write updated config
                    mock_file.assert_called()
                    written_content = "".join(
                        call.args[0] for call in mock_file().write.call_args_list
                    )
                    assert "/new/path" in written_content

    def test_config_template_methods(self):
        """Test methods for getting configuration templates."""
        config = VaultConfig()

        # Should provide PARA template
        para_template = config.get_template("para")
        assert "locations" in para_template
        assert "calendar_events" in para_template["locations"]

        # Should provide GTD template
        gtd_template = config.get_template("gtd")
        assert "gtd_inbox" in gtd_template["locations"]

        # Should list available templates
        templates = config.list_templates()
        assert "para" in templates
        assert "gtd" in templates
        assert "time_based" in templates
