"""Tests for the status command."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from dayflow.ui.cli import cli


class TestStatusCommand:
    """Test the status command."""

    @pytest.fixture
    def runner(self):
        """Create a CLI runner."""
        return CliRunner()

    def test_status_no_token(self, runner):
        """Test status when no token exists."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 0
            assert "System Status" in result.output
            assert "❌ Authentication: No valid token" in result.output

    def test_status_valid_token(self, runner):
        """Test status with valid token."""
        with runner.isolated_filesystem():
            # Create a valid token file
            token_data = {
                "access_token": "test_token",
                "expires_at": (datetime.now() + timedelta(hours=20)).isoformat(),
                "acquired_at": datetime.now().isoformat(),
            }

            token_file = Path(".graph_token")
            with open(token_file, "w") as f:
                json.dump(token_data, f)

            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 0
            assert "✅ Authentication: Valid" in result.output
            assert "hours remaining" in result.output

    def test_status_expired_token(self, runner):
        """Test status with expired token."""
        with runner.isolated_filesystem():
            # Create an expired token file
            token_data = {
                "access_token": "test_token",
                "expires_at": (datetime.now() - timedelta(hours=1)).isoformat(),
                "acquired_at": (datetime.now() - timedelta(hours=25)).isoformat(),
            }

            token_file = Path(".graph_token")
            with open(token_file, "w") as f:
                json.dump(token_data, f)

            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 0
            assert "❌ Authentication: No valid token" in result.output

    @patch("dayflow.vault.VaultConfig")
    def test_status_vault_configured(self, mock_config, runner):
        """Test status with configured vault."""
        # Mock vault config
        config_instance = Mock()
        config_instance.vault_path = Path("/Users/test/ObsidianVault")
        config_instance.validate.return_value = None
        mock_config.return_value = config_instance

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 0
            assert "✅ Vault: /Users/test/ObsidianVault" in result.output

    @patch("dayflow.vault.VaultConfig")
    def test_status_vault_not_configured(self, mock_config, runner):
        """Test status when vault is not configured."""
        mock_config.side_effect = Exception("Vault path not set")

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 0
            assert "❌ Vault: Not configured" in result.output
            assert "Vault path not set" in result.output

    @patch("dayflow.vault.VaultConfig")
    @patch("dayflow.core.meeting_matcher.MeetingMatcher")
    def test_status_with_current_meeting(self, mock_matcher, mock_config, runner):
        """Test status showing current meeting."""
        # Mock vault config
        config_instance = Mock()
        config_instance.vault_path = Path("/Users/test/ObsidianVault")
        meeting_path = Mock()
        meeting_path.exists.return_value = True
        config_instance.get_location.return_value = meeting_path
        config_instance.validate.return_value = None
        mock_config.return_value = config_instance

        # Mock meeting matcher
        current_meeting = {
            "title": "Team Standup",
            "start_time": datetime.now(timezone.utc) - timedelta(minutes=15),
            "location": "Conference Room A",
            "file_path": Path("2024-01-15 Team Standup.md"),
        }

        matcher_instance = Mock()
        matcher_instance.find_current_meeting.return_value = current_meeting
        matcher_instance.find_upcoming_meeting.return_value = None
        matcher_instance.find_recent_meeting.return_value = None
        mock_matcher.return_value = matcher_instance

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 0
            assert "Meeting Context" in result.output
            assert "📍 Current: Team Standup" in result.output
            assert "Location: Conference Room A" in result.output

    @patch("dayflow.vault.VaultConfig")
    @patch("dayflow.core.meeting_matcher.MeetingMatcher")
    def test_status_with_upcoming_meeting(self, mock_matcher, mock_config, runner):
        """Test status showing upcoming meeting."""
        # Mock vault config
        config_instance = Mock()
        config_instance.vault_path = Path("/Users/test/ObsidianVault")
        meeting_path = Mock()
        meeting_path.exists.return_value = True
        config_instance.get_location.return_value = meeting_path
        config_instance.validate.return_value = None
        mock_config.return_value = config_instance

        # Mock meeting matcher
        upcoming_meeting = {
            "title": "Budget Review",
            "start_time": datetime.now(timezone.utc) + timedelta(minutes=30),
            "file_path": Path("2024-01-15 Budget Review.md"),
        }

        recent_meeting = {
            "title": "Morning Scrum",
            "file_path": Path("2024-01-15 Morning Scrum.md"),
        }

        matcher_instance = Mock()
        matcher_instance.find_current_meeting.return_value = None
        matcher_instance.find_upcoming_meeting.return_value = upcoming_meeting
        matcher_instance.find_recent_meeting.return_value = recent_meeting
        mock_matcher.return_value = matcher_instance

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 0
            assert "📍 Current: No active meeting" in result.output
            assert (
                "🔜 Next: Budget Review (in 2" in result.output
                or "🔜 Next: Budget Review (in 30 minutes)" in result.output
            )
            assert "🕐 Recent: Morning Scrum" in result.output

    @patch("dayflow.vault.VaultConfig")
    def test_status_no_meeting_notes(self, mock_config, runner):
        """Test status when meeting notes folder doesn't exist."""
        # Mock vault config
        config_instance = Mock()
        config_instance.vault_path = Path("/Users/test/ObsidianVault")
        config_instance.get_location.return_value = (
            None  # No meeting location configured
        )
        config_instance.validate.return_value = None
        mock_config.return_value = config_instance

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 0
            assert "No meeting notes found" in result.output

    @patch("dayflow.vault.VaultConfig")
    @patch("dayflow.core.meeting_matcher.MeetingMatcher")
    def test_status_meeting_error_handling(self, mock_matcher, mock_config, runner):
        """Test status handles meeting detection errors gracefully."""
        # Mock vault config
        config_instance = Mock()
        config_instance.vault_path = Path("/Users/test/ObsidianVault")
        config_instance.get_location.side_effect = Exception("Failed to get location")
        config_instance.validate.return_value = None
        mock_config.return_value = config_instance

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 0
            assert "Unable to check meetings" in result.output

    def test_status_complete_system(self, runner):
        """Test status with complete system setup."""
        with runner.isolated_filesystem():
            # Create a valid token
            token_data = {
                "access_token": "test_token",
                "expires_at": (datetime.now() + timedelta(hours=12)).isoformat(),
                "acquired_at": datetime.now().isoformat(),
            }

            token_file = Path(".graph_token")
            with open(token_file, "w") as f:
                json.dump(token_data, f)

            with patch("dayflow.vault.VaultConfig") as mock_config:
                with patch(
                    "dayflow.core.meeting_matcher.MeetingMatcher"
                ) as mock_matcher:
                    # Mock vault
                    config_instance = Mock()
                    config_instance.vault_path = Path("/Users/test/Vault")
                    meeting_path = Mock()
                    meeting_path.exists.return_value = True
                    config_instance.get_location.return_value = meeting_path
                    config_instance.validate.return_value = None
                    mock_config.return_value = config_instance

                    # Mock meetings
                    current = {
                        "title": "Daily Standup",
                        "start_time": datetime.now(timezone.utc) - timedelta(minutes=5),
                        "location": "Zoom",
                        "file_path": Path("meeting.md"),
                    }

                    matcher_instance = Mock()
                    matcher_instance.find_current_meeting.return_value = current
                    matcher_instance.find_upcoming_meeting.return_value = None
                    matcher_instance.find_recent_meeting.return_value = None
                    mock_matcher.return_value = matcher_instance

                    result = runner.invoke(cli, ["status"])

                    assert result.exit_code == 0
                    # Should show all components
                    assert "✅ Authentication: Valid" in result.output
                    assert "✅ Vault:" in result.output
                    assert "📍 Current: Daily Standup" in result.output
