"""
Test cases for vault-related CLI commands.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml  # type: ignore
from click.testing import CliRunner

from dayflow.ui.cli import cli


@pytest.fixture(autouse=True)
def mock_vault_detector():
    """Mock VaultDetector to speed up tests."""
    with patch("dayflow.vault.detector.VaultDetector") as mock_detector_class:
        mock_instance = Mock()
        mock_detector_class.return_value = mock_instance

        # Default to finding no vaults unless overridden
        mock_instance.find_obsidian_vaults.return_value = []
        mock_instance.get_vault_stats.return_value = {"total_notes": 0}

        yield mock_instance


class TestVaultCommands:
    """Test vault management commands."""

    def setup_method(self):
        self.runner = CliRunner(env={"DAYFLOW_CONFIG_PATH": ".dayflow/config.yaml"})

    def test_vault_init_interactive(self, mock_vault_detector):
        """Test interactive vault initialization."""
        with self.runner.isolated_filesystem():
            # Create a mock vault
            vault_path = Path.cwd() / "test_vault"
            vault_path.mkdir()
            (vault_path / ".obsidian").mkdir()

            # Mock finding only the test vault
            mock_vault_detector.find_obsidian_vaults.return_value = [vault_path]

            # Mock user inputs
            with patch("click.prompt") as mock_prompt:
                with patch("click.confirm") as mock_confirm:
                    mock_prompt.side_effect = [
                        1,  # Select vault 1 (test_vault) from the list
                        1,  # Calendar events location - option 1
                        1,  # Daily notes location - option 1
                    ]
                    mock_confirm.return_value = True

                    result = self.runner.invoke(cli, ["vault", "init"])

                    if result.exit_code != 0:
                        print(f"Exit code: {result.exit_code}")
                        print(f"Output: {result.output}")
                        print(f"Exception: {result.exception}")
                        if result.exception:
                            import traceback

                            traceback.print_tb(result.exc_info[2])

                    assert result.exit_code == 0
                    assert "✅ Configuration saved to:" in result.output
                    assert "Your vault is now configured!" in result.output

                    # Check config was created in current dir due to env var
                    config_file = Path(".dayflow/config.yaml")
                    assert config_file.exists()

    def test_vault_init_with_options(self):
        """Test non-interactive vault initialization."""
        with self.runner.isolated_filesystem():
            vault_path = Path.cwd() / "test_vault"
            vault_path.mkdir()
            (vault_path / ".obsidian").mkdir()

            result = self.runner.invoke(
                cli, ["vault", "init", "--path", str(vault_path), "--template", "para"]
            )

            assert result.exit_code == 0
            assert "Applied PARA template" in result.output

    def test_vault_set_path(self):
        """Test setting vault path."""
        with self.runner.isolated_filesystem():
            # Create initial config
            config_dir = Path(".dayflow")
            config_dir.mkdir()
            config_file = config_dir / "config.yaml"
            config_file.write_text("vault:\n  path: /old/path", encoding="utf-8")

            # Create new vault
            new_vault = Path.cwd() / "new_vault"
            new_vault.mkdir()
            (new_vault / ".obsidian").mkdir()

            result = self.runner.invoke(cli, ["vault", "set-path", str(new_vault)])

            assert result.exit_code == 0
            assert "Vault path updated" in result.output

            # Check config was updated
            config = yaml.safe_load(config_file.read_text(encoding="utf-8"))
            assert config["vault"]["path"] == str(new_vault)

    def test_vault_set_location(self):
        """Test setting location for content type."""
        with self.runner.isolated_filesystem():
            # Create config
            config_dir = Path(".dayflow")
            config_dir.mkdir()
            config_file = config_dir / "config.yaml"
            config_file.write_text(
                "vault:\n  path: /test/vault\n  locations: {}", encoding="utf-8"
            )

            result = self.runner.invoke(
                cli, ["vault", "set-location", "calendar_events", "Meetings/Work"]
            )

            assert result.exit_code == 0
            assert "Location updated" in result.output

            # Check config
            config = yaml.safe_load(config_file.read_text(encoding="utf-8"))
            assert config["vault"]["locations"]["calendar_events"] == "Meetings/Work"

    def test_vault_list_templates(self):
        """Test listing available templates."""
        result = self.runner.invoke(cli, ["vault", "list-templates"])

        assert result.exit_code == 0
        assert "Available templates:" in result.output
        assert "para" in result.output
        assert "gtd" in result.output
        assert "time_based" in result.output
        assert "zettelkasten" in result.output

    def test_vault_apply_template(self):
        """Test applying a template."""
        with self.runner.isolated_filesystem():
            # Create config
            config_dir = Path(".dayflow")
            config_dir.mkdir()
            config_file = config_dir / "config.yaml"
            config_file.write_text("vault:\n  path: /test/vault", encoding="utf-8")

            result = self.runner.invoke(cli, ["vault", "apply-template", "gtd"])

            assert result.exit_code == 0
            assert "Applied GTD template" in result.output

            # Check locations were added
            config = yaml.safe_load(config_file.read_text(encoding="utf-8"))
            assert "gtd_inbox" in config["vault"]["locations"]
            assert config["vault"]["locations"]["gtd_inbox"] == "00-Inbox"

    def test_vault_status(self):
        """Test showing vault status."""
        with self.runner.isolated_filesystem():
            # Create vault and config
            vault_path = Path.cwd() / "test_vault"
            vault_path.mkdir()
            (vault_path / ".obsidian").mkdir()

            config_dir = Path(".dayflow")
            config_dir.mkdir()
            config_file = config_dir / "config.yaml"
            config_data = {
                "vault": {
                    "path": str(vault_path),
                    "locations": {
                        "calendar_events": "Meetings",
                        "daily_notes": "Daily Notes",
                    },
                }
            }
            config_file.write_text(yaml.dump(config_data), encoding="utf-8")

            result = self.runner.invoke(cli, ["vault", "status"])

            assert result.exit_code == 0
            assert "Vault Status" in result.output
            assert str(vault_path) in result.output
            assert "calendar_events: Meetings" in result.output
            assert "daily_notes: Daily Notes" in result.output

    def test_vault_validate(self):
        """Test vault validation."""
        with self.runner.isolated_filesystem():
            # Create valid vault
            vault_path = Path.cwd() / "test_vault"
            vault_path.mkdir()
            (vault_path / ".obsidian").mkdir()

            config_dir = Path(".dayflow")
            config_dir.mkdir()
            config_file = config_dir / "config.yaml"
            config_file.write_text(f"vault:\n  path: {vault_path}", encoding="utf-8")

            result = self.runner.invoke(cli, ["vault", "validate"])

            assert result.exit_code == 0
            assert "✅ Vault configuration is valid" in result.output

    def test_vault_validate_missing_path(self):
        """Test validation with missing vault path."""
        with self.runner.isolated_filesystem():
            config_dir = Path(".dayflow")
            config_dir.mkdir()
            config_file = config_dir / "config.yaml"
            config_file.write_text(
                "vault:\n  path: /nonexistent/path", encoding="utf-8"
            )

            result = self.runner.invoke(cli, ["vault", "validate"])

            assert result.exit_code != 0
            assert "Vault path does not exist" in result.output

    def test_vault_auto_detect(self):
        """Test automatic vault detection."""
        with self.runner.isolated_filesystem():
            # Create multiple vaults
            vault1 = Path.cwd() / "Obsidian" / "Personal"
            vault1.mkdir(parents=True)
            (vault1 / ".obsidian").mkdir()

            vault2 = Path.cwd() / "Documents" / "Work"
            vault2.mkdir(parents=True)
            (vault2 / ".obsidian").mkdir()

            # Mock the detector at the vault module level
            with patch("dayflow.vault.VaultDetector") as mock_detector_class:
                mock_instance = Mock()
                mock_detector_class.return_value = mock_instance
                mock_instance.find_obsidian_vaults.return_value = [vault1, vault2]

                result = self.runner.invoke(cli, ["vault", "detect"])

                assert result.exit_code == 0
                assert "Found 2 Obsidian vault(s):" in result.output
                assert "Personal" in result.output
                assert "Work" in result.output
