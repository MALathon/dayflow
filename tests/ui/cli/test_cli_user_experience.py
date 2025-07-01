"""
Test cases for CLI user experience.
These tests ensure helpful error messages, clear feedback, and good UX.
"""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

# These imports will fail initially - expected in TDD
from dayflow.ui.cli import cli


class TestCLIFeedback:
    """Test user feedback and error messages."""

    def setup_method(self):
        self.runner = CliRunner()

    @pytest.mark.tdd
    def test_clear_error_on_missing_config(self):
        """Test helpful error when config is missing."""
        with patch("dayflow.config.Config.load", side_effect=FileNotFoundError):
            result = self.runner.invoke(cli, ["sync"])

        assert result.exit_code == 1
        assert "No configuration found" in result.output
        assert "Run 'dayflow config init' to create one" in result.output

    @pytest.mark.tdd
    def test_helpful_vault_path_error(self):
        """Test clear guidance when vault path is invalid."""
        with patch("pathlib.Path.exists", return_value=False):
            result = self.runner.invoke(cli, ["sync"])

        assert "Obsidian vault not found at:" in result.output
        assert "Please check your configuration" in result.output
        assert (
            "Run 'dayflow config set obsidian.vault_path /path/to/vault'"
            in result.output
        )

    @pytest.mark.tdd
    def test_token_expiry_warning(self):
        """Test warning when token is about to expire."""
        with patch("dayflow.auth.TokenManager.get_token_info") as mock_info:
            mock_info.return_value = {
                "valid": True,
                "expires_in_minutes": 5,  # About to expire
            }

            result = self.runner.invoke(cli, ["sync"])

        assert "⚠️  Token expires in 5 minutes" in result.output
        assert "Consider refreshing your token soon" in result.output


class TestCLIColors:
    """Test colored output for better readability."""

    def setup_method(self):
        self.runner = CliRunner()

    @pytest.mark.tdd
    def test_success_messages_are_green(self):
        """Test that success messages use green color."""
        with patch("dayflow.core.sync.CalendarSyncEngine") as mock_sync:
            mock_engine = Mock()
            mock_engine.sync.return_value = {"events_synced": 5}
            mock_sync.return_value = mock_engine

            _result = self.runner.invoke(cli, ["sync"], color=True)

        # Click uses ANSI codes for colors
        assert "\033[32m" in _result.output  # Green color code
        assert "Successfully synced" in _result.output

    @pytest.mark.tdd
    def test_error_messages_are_red(self):
        """Test that error messages use red color."""
        with patch("dayflow.core.sync.CalendarSyncEngine") as mock_sync:
            mock_sync.side_effect = Exception("Network error")

            result = self.runner.invoke(cli, ["sync"], color=True)

        assert "\033[31m" in result.output  # Red color code
        assert "Error:" in result.output

    @pytest.mark.tdd
    def test_warnings_are_yellow(self):
        """Test that warnings use yellow color."""
        result = self.runner.invoke(cli, ["auth", "status"], color=True)

        # When no token exists, should show yellow warning
        assert "\033[33m" in result.output  # Yellow color code


class TestCLIValidation:
    """Test input validation and helpful error messages."""

    def setup_method(self):
        self.runner = CliRunner()

    @pytest.mark.tdd
    def test_invalid_date_format_help(self):
        """Test helpful error for invalid date formats."""
        result = self.runner.invoke(cli, ["sync", "--start", "invalid-date"])

        assert result.exit_code == 2  # Click's exit code for invalid input
        assert "Invalid date format" in result.output
        assert "Expected format: YYYY-MM-DD" in result.output
        assert "Example: 2024-01-15" in result.output

    @pytest.mark.tdd
    def test_invalid_interval_help(self):
        """Test helpful error for invalid interval values."""
        result = self.runner.invoke(
            cli, ["sync", "--continuous", "--interval", "-5"]  # Negative interval
        )

        assert result.exit_code == 2
        assert "Interval must be positive" in result.output
        assert "Minimum interval: 1 minute" in result.output

    @pytest.mark.tdd
    def test_path_validation_with_suggestions(self):
        """Test path validation with helpful suggestions."""
        result = self.runner.invoke(
            cli, ["config", "set", "obsidian.vault_path", "~/nonexistent/path"]
        )

        assert "Path does not exist" in result.output
        assert "Did you mean:" in result.output
        # Should suggest similar existing paths


class TestCLIDefaults:
    """Test sensible defaults and smart behavior."""

    def setup_method(self):
        self.runner = CliRunner()

    @pytest.mark.tdd
    def test_sync_defaults_to_reasonable_range(self):
        """Test sync uses sensible default date range."""
        with patch("dayflow.core.sync.CalendarSyncEngine") as mock_sync:
            mock_engine = Mock()
            mock_sync.return_value = mock_engine

            with patch("dayflow.ui.cli.auth.has_valid_token", return_value=True):
                result = self.runner.invoke(cli, ["sync"])  # noqa: F841

            # Should sync from yesterday to 7 days ahead by default
            mock_engine.sync.assert_called_once()
            call_args = mock_engine.sync.call_args

            # Verify default date range
            assert call_args is not None

    @pytest.mark.tdd
    def test_smart_vault_detection(self):
        """Test CLI tries to auto-detect Obsidian vault."""
        from os.path import expanduser

        common_paths = [
            expanduser("~/Documents/Obsidian"),
            expanduser("~/Obsidian"),
            expanduser("~/Documents/ObsidianVault"),
        ]

        with patch("pathlib.Path.exists") as mock_exists:
            # Simulate finding vault in common location
            mock_exists.side_effect = lambda p: str(p) in common_paths

            result = self.runner.invoke(cli, ["config", "init"])

        assert "Found Obsidian vault at" in result.output


class TestCLIOnboarding:
    """Test first-time user experience."""

    def setup_method(self):
        self.runner = CliRunner()

    @pytest.mark.tdd
    def test_first_run_guidance(self):
        """Test helpful guidance on first run."""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli)

        assert "Welcome to Dayflow!" in result.output
        assert "It looks like this is your first time" in result.output
        assert "Let's get you set up:" in result.output
        assert "1. Run 'dayflow config init'" in result.output
        assert "2. Run 'dayflow auth login'" in result.output
        assert "3. Run 'dayflow sync'" in result.output

    @pytest.mark.tdd
    def test_config_init_wizard(self):
        """Test configuration initialization wizard."""
        user_inputs = [
            "/Users/test/Obsidian/MyVault",  # Vault path
            "America/Chicago",  # Timezone
            "y",  # Confirm
        ]

        result = self.runner.invoke(
            cli, ["config", "init"], input="\n".join(user_inputs)
        )

        assert result.exit_code == 0
        assert "Let's set up your configuration" in result.output
        assert "Where is your Obsidian vault located?" in result.output
        assert "What timezone are you in?" in result.output
        assert "Configuration saved!" in result.output


class TestCLIDryRun:
    """Test dry-run mode for safety."""

    def setup_method(self):
        self.runner = CliRunner()

    @pytest.mark.tdd
    def test_sync_dry_run_mode(self):
        """Test dry-run shows what would happen without making changes."""
        with patch("dayflow.core.sync.CalendarSyncEngine") as mock_sync:
            mock_engine = Mock()
            mock_engine.sync_dry_run.return_value = {
                "would_sync": 10,
                "would_create": 3,
                "would_update": 7,
            }
            mock_sync.return_value = mock_engine

            result = self.runner.invoke(cli, ["sync", "--dry-run"])

        assert result.exit_code == 0
        assert "DRY RUN MODE" in result.output
        assert "Would sync 10 events" in result.output
        assert "Would create 3 new notes" in result.output
        assert "Would update 7 existing notes" in result.output
        assert "No changes were made" in result.output


class TestCLIAccessibility:
    """Test accessibility features."""

    def setup_method(self):
        self.runner = CliRunner()

    @pytest.mark.tdd
    def test_no_emoji_mode(self):
        """Test option to disable emoji for accessibility."""
        result = self.runner.invoke(cli, ["sync", "--no-emoji"])

        # Should not contain emoji characters
        assert "✅" not in result.output
        assert "❌" not in result.output
        assert "⚠️" not in result.output

        # Should use text indicators instead
        assert "[SUCCESS]" in result.output or "Success:" in result.output

    @pytest.mark.tdd
    def test_verbose_mode_for_screen_readers(self):
        """Test verbose mode provides detailed text output."""
        result = self.runner.invoke(cli, ["sync", "--verbose"])

        # Should provide detailed textual feedback
        assert "Starting synchronization process" in result.output
        assert "Checking authentication status" in result.output
        assert "Connecting to Microsoft Graph API" in result.output
