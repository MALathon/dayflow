"""Tests for the note command with meeting linking."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from dayflow.ui.cli import cli


class TestNoteCommand:
    """Test the note creation command."""

    @pytest.fixture
    def runner(self):
        """Create a CLI runner."""
        return CliRunner()

    @pytest.fixture
    def mock_vault_setup(self):
        """Mock vault configuration."""
        with patch("dayflow.vault.VaultConfig") as mock_config:
            with patch("dayflow.vault.VaultConnection") as mock_conn:
                # Setup mock config
                config_instance = Mock()
                config_instance.vault_path = Path("/test/vault")
                meeting_path = Mock()
                meeting_path.exists.return_value = True
                config_instance.get_location.return_value = meeting_path
                config_instance.validate.return_value = None
                mock_config.return_value = config_instance

                # Setup mock connection
                conn_instance = Mock()
                conn_instance.write_note.return_value = Path(
                    "/test/vault/Daily Notes/test-note.md"
                )
                mock_conn.return_value = conn_instance

                yield config_instance, conn_instance

    def test_note_basic_creation(self, runner, mock_vault_setup):
        """Test basic note creation without meeting link."""
        config, conn = mock_vault_setup

        with patch("dayflow.core.meeting_matcher.MeetingMatcher") as mock_matcher:
            # No current meeting
            matcher_instance = Mock()
            matcher_instance.find_current_meeting.return_value = None
            matcher_instance.find_upcoming_meeting.return_value = None
            mock_matcher.return_value = matcher_instance

            # Run command with title only (simulate Ctrl+D immediately, then N for
            # Obsidian prompt)
            result = runner.invoke(
                cli,
                ["note", "--title", "Test Note", "--no-link-meeting"],
                input="\x04n\n",
            )

            if result.exit_code != 0:
                print("Error output:", result.output)
                print("Exception:", result.exception)
            assert result.exit_code == 0
            assert "✅ Created note:" in result.output

            # Check that note was written
            conn.write_note.assert_called_once()
            content = conn.write_note.call_args[0][0]

            # Verify content structure
            assert "title: Test Note" in content
            assert "type: note" in content
            assert "tags: [quick-note]" in content
            assert "# Test Note" in content

    def test_note_with_current_meeting(self, runner, mock_vault_setup):
        """Test note creation linked to current meeting."""
        config, conn = mock_vault_setup

        with patch("dayflow.core.meeting_matcher.MeetingMatcher") as mock_matcher:
            # Mock current meeting
            current_meeting = {
                "title": "Team Standup",
                "file_path": Path("/test/vault/Meetings/2024-01-15 Team Standup.md"),
                "start_time": datetime.now(timezone.utc),
            }

            matcher_instance = Mock()
            matcher_instance.find_current_meeting.return_value = current_meeting
            mock_matcher.return_value = matcher_instance

            result = runner.invoke(
                cli, ["note", "--title", "Meeting Notes"], input="\x04n\n"
            )

            assert result.exit_code == 0
            assert "✅ Linked to meeting: Team Standup" in result.output

            # Check content includes meeting link
            content = conn.write_note.call_args[0][0]
            assert 'meeting: "[[2024-01-15 Team Standup]]"' in content
            assert (
                "This note was created during: [[2024-01-15 Team Standup]]" in content
            )

    def test_note_with_upcoming_meeting(self, runner, mock_vault_setup):
        """Test note creation linked to upcoming meeting."""
        config, conn = mock_vault_setup

        with patch("dayflow.core.meeting_matcher.MeetingMatcher") as mock_matcher:
            # No current meeting, but upcoming one
            upcoming_meeting = {
                "title": "Budget Review",
                "file_path": Path("/test/vault/Meetings/2024-01-15 Budget Review.md"),
                "start_time": datetime.now(timezone.utc) + timedelta(minutes=3),
            }

            matcher_instance = Mock()
            matcher_instance.find_current_meeting.return_value = None
            matcher_instance.find_upcoming_meeting.return_value = upcoming_meeting
            mock_matcher.return_value = matcher_instance

            result = runner.invoke(
                cli, ["note", "--title", "Pre-meeting Prep"], input="\x04n\n"
            )

            assert result.exit_code == 0
            assert "✅ Linked to upcoming meeting: Budget Review" in result.output

            content = conn.write_note.call_args[0][0]
            assert (
                "This note was created before: [[2024-01-15 Budget Review]]" in content
            )

    def test_note_with_meeting_template(self, runner, mock_vault_setup):
        """Test note creation with meeting template."""
        config, conn = mock_vault_setup

        with patch("dayflow.core.meeting_matcher.MeetingMatcher"):
            result = runner.invoke(
                cli,
                ["note", "--title", "Team Sync", "--template", "meeting"],
                input="\x04n\n",
            )

            assert result.exit_code == 0

            content = conn.write_note.call_args[0][0]
            # Check meeting template sections
            assert "## Key Points" in content
            assert "## Decisions" in content
            assert "## Action Items" in content
            assert "## Follow-up Required" in content

    def test_note_with_idea_template(self, runner, mock_vault_setup):
        """Test note creation with idea template."""
        config, conn = mock_vault_setup

        with patch("dayflow.core.meeting_matcher.MeetingMatcher"):
            result = runner.invoke(
                cli,
                ["note", "--title", "New Feature Idea", "--template", "idea"],
                input="\x04n\n",
            )

            assert result.exit_code == 0

            content = conn.write_note.call_args[0][0]
            # Check idea template sections
            assert "## The Idea" in content
            assert "## Why It Matters" in content
            assert "## Next Steps" in content
            assert "## Related Concepts" in content

    def test_note_with_content_input(self, runner, mock_vault_setup):
        """Test note creation with user content."""
        config, conn = mock_vault_setup

        with patch("dayflow.core.meeting_matcher.MeetingMatcher"):
            # Simulate user entering content then Ctrl+D
            user_input = "This is my note content\nWith multiple lines\n\nn\n"
            result = runner.invoke(
                cli, ["note", "--title", "Content Test"], input=user_input
            )

            assert result.exit_code == 0

            content = conn.write_note.call_args[0][0]
            # User content should be inserted
            assert "This is my note content" in content
            assert "With multiple lines" in content

    def test_note_with_editor_mode(self, runner, mock_vault_setup):
        """Test note creation with editor mode."""
        config, conn = mock_vault_setup

        with patch("dayflow.core.meeting_matcher.MeetingMatcher"):
            with patch("click.edit") as mock_edit:
                # Simulate editor returning modified content
                mock_edit.return_value = (
                    "# Edited Note\n\nThis was edited in the editor."
                )

                result = runner.invoke(
                    cli, ["note", "--title", "Editor Test", "--editor"]
                )

                assert result.exit_code == 0
                mock_edit.assert_called_once()

                # Should save the edited content
                content = conn.write_note.call_args[0][0]
                assert content == "# Edited Note\n\nThis was edited in the editor."

    def test_note_editor_cancelled(self, runner, mock_vault_setup):
        """Test note creation cancelled in editor."""
        config, conn = mock_vault_setup

        with patch("dayflow.core.meeting_matcher.MeetingMatcher"):
            with patch("click.edit") as mock_edit:
                # Simulate editor cancelled (returns None)
                mock_edit.return_value = None

                result = runner.invoke(
                    cli, ["note", "--title", "Cancelled", "--editor"]
                )

                assert result.exit_code == 0
                assert "Note creation cancelled" in result.output

                # Should not write any note
                conn.write_note.assert_not_called()

    def test_note_special_characters_in_title(self, runner, mock_vault_setup):
        """Test note creation with special characters in title."""
        config, conn = mock_vault_setup

        with patch("dayflow.core.meeting_matcher.MeetingMatcher"):
            result = runner.invoke(
                cli, ["note", "--title", "Project: Alpha/Beta"], input="\x04n\n"
            )

            assert result.exit_code == 0

            # Check filename sanitization
            filename = conn.write_note.call_args[0][1]
            assert "/" not in filename
            assert ":" not in filename

    def test_note_vault_not_configured(self, runner):
        """Test note creation when vault is not configured."""
        with patch("dayflow.vault.VaultConfig") as mock_config:
            mock_config.side_effect = Exception("Vault not configured")

            result = runner.invoke(cli, ["note", "--title", "Test"], input="\x04")

            assert result.exit_code == 1
            assert "Vault not configured" in result.output
            assert "Run 'dayflow vault setup' first" in result.output

    def test_note_open_in_obsidian(self, runner, mock_vault_setup):
        """Test opening note in Obsidian after creation."""
        config, conn = mock_vault_setup
        config.vault_path = Path("/Users/test/Vault")
        conn.write_note.return_value = Path(
            "/Users/test/Vault/Daily Notes/2024-01-15-1430 Test.md"
        )

        with patch("dayflow.core.meeting_matcher.MeetingMatcher"):
            # Use editor mode to avoid the interactive prompt issue
            with patch("click.edit") as mock_edit:
                mock_edit.return_value = "# Test Note\n\nContent here."

                result = runner.invoke(cli, ["note", "--title", "Test", "--editor"])

                assert result.exit_code == 0
                # Verify editor was called
                mock_edit.assert_called_once()

                # Verify note was created
                conn.write_note.assert_called_once()
                content = conn.write_note.call_args[0][0]
                assert content == "# Test Note\n\nContent here."
