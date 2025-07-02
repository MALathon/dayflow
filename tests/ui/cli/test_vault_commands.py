"""
Test cases for vault-related CLI commands.
"""

from pathlib import Path
from unittest.mock import patch

import yaml  # type: ignore
from click.testing import CliRunner

from dayflow.ui.cli import cli


class TestVaultCommands:
    """Test vault management commands."""

    def setup_method(self):
        self.runner = CliRunner()

    def test_vault_init_interactive(self):
        """Test interactive vault initialization."""
        with self.runner.isolated_filesystem():
            # Create a mock vault
            vault_path = Path.cwd() / "test_vault"
            vault_path.mkdir()
            (vault_path / ".obsidian").mkdir()

            # Mock user inputs
            with patch("click.prompt") as mock_prompt:
                with patch("click.confirm") as mock_confirm:
                    mock_prompt.side_effect = [
                        str(vault_path),
                        "1",
                    ]  # path, then template choice
                    mock_confirm.return_value = True

                    result = self.runner.invoke(cli, ["vault", "init"])

                    assert result.exit_code == 0
                    assert "Vault initialization complete" in result.output

                    # Check config was created
                    config_file = Path.home() / ".dayflow" / "config.yaml"
                    # In isolated filesystem, config would be in current dir
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
            config = yaml.safe_load(config_file.read_text())
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
            config = yaml.safe_load(config_file.read_text())
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
            config = yaml.safe_load(config_file.read_text())
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
            config_file.write_text(yaml.dump(config_data))

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
            config_file.write_text(f"vault:\n  path: {vault_path}")

            result = self.runner.invoke(cli, ["vault", "validate"])

            assert result.exit_code == 0
            assert "✓ Vault configuration is valid" in result.output

    def test_vault_validate_missing_path(self):
        """Test validation with missing vault path."""
        with self.runner.isolated_filesystem():
            config_dir = Path(".dayflow")
            config_dir.mkdir()
            config_file = config_dir / "config.yaml"
            config_file.write_text("vault:\n  path: /nonexistent/path")

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

            with patch("pathlib.Path.home", return_value=Path.cwd()):
                result = self.runner.invoke(cli, ["vault", "detect"])

                assert result.exit_code == 0
                assert "Found 2 Obsidian vault(s):" in result.output
                assert "Personal" in result.output
                assert "Work" in result.output
