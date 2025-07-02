"""Tests for continuous sync CLI commands."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from dayflow.ui.cli import cli


class TestContinuousSync:
    """Test continuous sync functionality in CLI."""

    @pytest.fixture
    def runner(self):
        """Create a CLI runner."""
        return CliRunner()

    @pytest.fixture
    def mock_token(self, tmp_path):
        """Create a mock token file."""
        token_data = {
            "access_token": "test_token",
            "expires_at": (datetime.now() + timedelta(hours=1)).isoformat(),
        }
        token_file = tmp_path / ".graph_token"
        token_file.write_text(json.dumps(token_data))
        return str(tmp_path)

    @pytest.fixture
    def mock_vault_config(self):
        """Mock vault configuration."""
        with patch("dayflow.vault.config.VaultConfig") as mock:
            config = Mock()
            config.vault_path = Path("/test/vault")
            config.validate.return_value = None
            mock.return_value = config
            yield config

    def test_continuous_sync_flag(self, runner):
        """Test that --continuous flag is recognized."""
        with runner.isolated_filesystem():
            # Create token in temp dir
            token_data = {
                "access_token": "test_token",
                "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
                "acquired_at": datetime.now().isoformat(),
            }
            Path(".graph_token").write_text(json.dumps(token_data))

            # Mock VaultConfigError and VaultConfig
            with patch("dayflow.vault.config.VaultConfig") as mock_vault_config:
                from dayflow.vault import VaultConfigError

                # Set up vault config to raise error on validate
                config_instance = Mock()
                config_instance.vault_path = Path("/test/vault")
                config_instance.validate.side_effect = VaultConfigError(
                    "Vault path does not exist: /test/vault"
                )
                mock_vault_config.return_value = config_instance

                with patch("dayflow.vault.connection.VaultConnection"):
                    with patch("dayflow.core.sync.CalendarSyncEngine"):
                        # Patch at the source module
                        with patch(
                            "dayflow.core.sync_daemon.ContinuousSyncManager"
                        ) as mock_manager:
                            # Make the manager stop immediately
                            manager_instance = Mock()
                            mock_manager.return_value = manager_instance

                            # Use input to answer 'y' to the confirmation prompt
                            result = runner.invoke(
                                cli, ["sync", "--continuous"], input="y\n"
                            )

                            # Check if there were any errors
                            if result.exit_code != 0:
                                print(f"Exit code: {result.exit_code}")
                                print(f"Output: {result.output}")
                                print(f"Exception: {result.exception}")

                            # Should create continuous sync manager
                            mock_manager.assert_called_once()
                            manager_instance.start.assert_called_once()

    def test_continuous_sync_with_interval(self, runner):
        """Test continuous sync with custom interval."""
        with runner.isolated_filesystem():
            # Create token in temp dir
            token_data = {
                "access_token": "test_token",
                "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
                "acquired_at": datetime.now().isoformat(),
            }
            Path(".graph_token").write_text(json.dumps(token_data))

            # Mock VaultConfigError and VaultConfig
            with patch("dayflow.vault.config.VaultConfig") as mock_vault_config:
                from dayflow.vault import VaultConfigError

                # Set up vault config to raise error on validate
                config_instance = Mock()
                config_instance.vault_path = Path("/test/vault")
                config_instance.validate.side_effect = VaultConfigError(
                    "Vault path does not exist: /test/vault"
                )
                mock_vault_config.return_value = config_instance

                with patch("dayflow.vault.connection.VaultConnection"):
                    with patch("dayflow.core.sync.CalendarSyncEngine"):
                        # Patch at the source module
                        with patch(
                            "dayflow.core.sync_daemon.ContinuousSyncManager"
                        ) as mock_manager:
                            manager_instance = Mock()
                            mock_manager.return_value = manager_instance

                            # Use input to answer 'y' to the confirmation prompt
                            runner.invoke(
                                cli,
                                ["sync", "--continuous", "--interval", "10"],
                                input="y\n",
                            )

                            # Should pass interval to manager
                            mock_manager.assert_called_once()
                            args = mock_manager.call_args
                            assert args[0][1] == 10  # interval_minutes

    def test_continuous_sync_without_token(self, runner):
        """Test continuous sync fails without authentication."""
        with runner.isolated_filesystem():
            # Test declining token refresh
            result = runner.invoke(cli, ["sync", "--continuous"], input="n\n")

            assert result.exit_code != 0
            assert "Not authenticated or token has expired" in result.output
            assert "Would you like to refresh your token now?" in result.output
            assert "Aborted" in result.output

    def test_continuous_sync_with_token_refresh_prompt(self, runner):
        """Test accepting token refresh prompt triggers login."""
        with runner.isolated_filesystem():
            with patch("webbrowser.open") as mock_browser:
                with patch("subprocess.check_output") as mock_clipboard:
                    with patch("click.pause"):  # Mock the pause to avoid waiting
                        # Mock vault config to avoid prompt
                        with patch("dayflow.vault.config.VaultConfig") as mock_vault:
                            from dayflow.vault import VaultConfigError

                            config_instance = Mock()
                            config_instance.vault_path = Path("/test/vault")
                            config_instance.validate.side_effect = VaultConfigError(
                                "Vault path does not exist: /test/vault"
                            )
                            mock_vault.return_value = config_instance

                            # Mock the continuous sync manager to prevent actual sync
                            with patch(
                                "dayflow.core.sync_daemon.ContinuousSyncManager"
                            ) as mock_manager:
                                manager_instance = Mock()
                                mock_manager.return_value = manager_instance

                                # Mock clipboard to return a valid token
                                mock_clipboard.return_value = (
                                    b"a" * 200
                                )  # Long enough token

                                # Accept token refresh, then 'y' for vault prompt
                                result = runner.invoke(
                                    cli, ["sync", "--continuous"], input="y\ny\n"
                                )

                                # Should open browser
                                base_url = "https://developer.microsoft.com"
                                graph_url = f"{base_url}/en-us/graph/graph-explorer"
                                mock_browser.assert_called_once_with(graph_url)
                                assert (
                                    "Opening Microsoft Graph Explorer" in result.output
                                )
                                assert "Token saved successfully!" in result.output

    def test_sync_status_in_cli_status(self, runner, tmp_path):
        """Test that sync status appears in dayflow status command."""
        # Create sync status file
        with patch("pathlib.Path.home", return_value=tmp_path):
            dayflow_dir = tmp_path / ".dayflow"
            dayflow_dir.mkdir()

            status_data = {
                "last_sync": (datetime.now() - timedelta(minutes=15)).isoformat(),
                "sync_count": 5,
                "error_count": 0,
                "interval_minutes": 5,
            }
            status_file = dayflow_dir / "sync_status.json"
            status_file.write_text(json.dumps(status_data))

            # Mock other status checks
            with patch("dayflow.ui.cli.has_valid_token", return_value=True):
                with patch("dayflow.ui.cli.get_token_info") as mock_token:
                    mock_token.return_value = {
                        "valid": True,
                        "expires_at": datetime.now() + timedelta(hours=1),
                    }

                    with patch("dayflow.vault.config.VaultConfig") as mock_config:
                        mock_config.return_value.vault_path = "/test/vault"

                        result = runner.invoke(cli, ["status"])

                        # Should show sync status
                        assert (
                            "Sync Status" in result.output
                            or "Last sync" in result.output
                        )
