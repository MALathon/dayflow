"""
Test cases for config management CLI commands.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from click.testing import CliRunner

from dayflow.ui.cli import cli


class TestConfigCommands:
    """Test configuration management commands."""

    def setup_method(self):
        self.runner = CliRunner()

    @pytest.mark.tdd
    def test_config_show(self):
        """Test showing current configuration."""
        with self.runner.isolated_filesystem():
            # Create config
            config_dir = Path(".dayflow")
            config_dir.mkdir()
            config_file = config_dir / "config.yaml"
            config_data = {
                "vault": {
                    "path": "/test/vault",
                    "locations": {
                        "calendar_events": "Meetings",
                        "daily_notes": "Daily Notes",
                    },
                }
            }
            config_file.write_text(yaml.dump(config_data), encoding="utf-8")

            result = self.runner.invoke(cli, ["config", "show"])

            assert result.exit_code == 0
            assert "Current Configuration" in result.output
            assert "vault:" in result.output
            assert "path: /test/vault" in result.output
            assert "calendar_events: Meetings" in result.output

    @pytest.mark.tdd
    def test_config_show_no_config(self):
        """Test showing config when none exists."""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["config", "show"])

            assert result.exit_code == 0
            assert "No configuration found" in result.output
            assert "dayflow vault init" in result.output

    @pytest.mark.tdd
    def test_config_path(self):
        """Test showing config file path."""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["config", "path"])

            assert result.exit_code == 0
            # Check for the config file name - works on both Windows and Unix
            assert "config.yaml" in result.output
            # Also check for the directory name (with either separator)
            assert ".dayflow" in result.output or ".dayflow\\" in result.output

    @pytest.mark.tdd
    def test_config_edit(self):
        """Test opening config in editor."""
        with self.runner.isolated_filesystem():
            # Create config
            config_dir = Path(".dayflow")
            config_dir.mkdir()
            config_file = config_dir / "config.yaml"
            config_file.write_text("vault:\n  path: /test/vault", encoding="utf-8")

            # Mock editor
            with patch("click.edit") as mock_edit:
                mock_edit.return_value = "vault:\n  path: /new/vault"

                result = self.runner.invoke(cli, ["config", "edit"])

                assert result.exit_code == 0
                assert "Configuration updated" in result.output

                # Check file was updated
                assert "/new/vault" in config_file.read_text()

    @pytest.mark.tdd
    def test_config_reset(self):
        """Test resetting configuration to defaults."""
        with self.runner.isolated_filesystem():
            # Create custom config
            config_dir = Path(".dayflow")
            config_dir.mkdir()
            config_file = config_dir / "config.yaml"
            config_file.write_text(
                "vault:\n  path: /custom/vault\n  custom: value", encoding="utf-8"
            )

            # Confirm reset
            result = self.runner.invoke(cli, ["config", "reset"], input="y\n")

            assert result.exit_code == 0
            assert "Configuration reset to defaults" in result.output

            # Check defaults were applied
            config = yaml.safe_load(config_file.read_text())
            assert config["vault"]["path"] == ""  # Default empty path
            assert "custom" not in config["vault"]  # Custom field removed

    @pytest.mark.tdd
    def test_config_get_value(self):
        """Test getting specific config value."""
        with self.runner.isolated_filesystem():
            # Create config
            config_dir = Path(".dayflow")
            config_dir.mkdir()
            config_file = config_dir / "config.yaml"
            config_data = (
                "vault:\n  path: /test/vault\n  locations:\n    "
                "calendar_events: Meetings"
            )
            config_file.write_text(config_data, encoding="utf-8")

            # Get vault path
            result = self.runner.invoke(cli, ["config", "get", "vault.path"])
            assert result.exit_code == 0
            assert "/test/vault" in result.output

            # Get nested value
            result = self.runner.invoke(
                cli, ["config", "get", "vault.locations.calendar_events"]
            )
            assert result.exit_code == 0
            assert "Meetings" in result.output

    @pytest.mark.tdd
    def test_config_set_value(self):
        """Test setting specific config value."""
        with self.runner.isolated_filesystem():
            # Create config
            config_dir = Path(".dayflow")
            config_dir.mkdir()
            config_file = config_dir / "config.yaml"
            config_file.write_text("vault:\n  path: /old/vault", encoding="utf-8")

            # Set new value
            result = self.runner.invoke(
                cli, ["config", "set", "vault.path", "/new/vault"]
            )

            assert result.exit_code == 0
            assert "Configuration updated" in result.output

            # Verify change
            config = yaml.safe_load(config_file.read_text())
            assert config["vault"]["path"] == "/new/vault"
