"""
Test cases for interactive CLI features.
These tests cover user prompts, confirmations, and interactive workflows.
"""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from dayflow.core.exceptions import SyncConflictError

# These imports will fail initially - expected in TDD
from dayflow.ui.cli import cli


class TestInteractiveAuth:
    """Test interactive authentication flow."""

    def setup_method(self):
        self.runner = CliRunner()

    @pytest.mark.tdd
    def test_auth_login_interactive_flow(self):
        """Test the full interactive auth flow."""
        # Simulate user interactions
        user_inputs = [
            "",  # Press enter to open browser
            "",  # Press enter after copying token
        ]

        with patch("webbrowser.open") as _mock_browser:  # noqa: F841
            with patch("subprocess.check_output", return_value=b"valid_token_12345"):
                result = self.runner.invoke(
                    cli, ["auth", "login"], input="\n".join(user_inputs)
                )

        assert result.exit_code == 0
        assert "Opening Microsoft Graph Explorer" in result.output
        assert "Sign in and copy the access token" in result.output
        assert "Press Enter when you've copied the token" in result.output
        assert "Token saved successfully" in result.output

    @pytest.mark.tdd
    def test_auth_login_retry_on_invalid_token(self):
        """Test retry mechanism for invalid tokens."""
        # First attempt: invalid token (too short)
        # Second attempt: valid token
        with patch(
            "subprocess.check_output",
            side_effect=[b"short", b"valid_token_" + b"x" * 1000],
        ):
            result = self.runner.invoke(
                cli, ["auth", "login"], input="\n\n\n"  # Multiple enters for retry
            )

        assert "Token appears invalid (too short)" in result.output
        assert "Would you like to try again?" in result.output


class TestInteractiveGTD:
    """Test interactive GTD processing."""

    def setup_method(self):
        self.runner = CliRunner()

    @patch("dayflow.core.gtd.GTDSystem")
    @pytest.mark.tdd
    def test_gtd_process_interactive(self, mock_gtd):
        """Test interactive inbox processing."""
        # Mock inbox items
        mock_system = Mock()
        mock_system.get_inbox_items.return_value = [
            {
                "id": 1,
                "content": "Call Bob about project",
                "source": "Meeting: Project Review",
            },
            {"id": 2, "content": "Review Q4 budget", "source": "Email"},
        ]
        mock_gtd.return_value = mock_system

        # User choices:
        # 1. Process first item as Next Action with @phone context
        # 2. Process second item as Project
        user_inputs = [
            "1",  # Select first item
            "action",  # Make it a next action
            "@phone",  # Add context
            "y",  # Confirm
            "2",  # Select second item
            "project",  # Make it a project
            "y",  # Confirm
            "q",  # Quit
        ]

        result = self.runner.invoke(
            cli, ["gtd", "process"], input="\n".join(user_inputs)
        )

        assert result.exit_code == 0
        assert "Inbox Items (2)" in result.output
        assert "Call Bob about project" in result.output
        assert "What would you like to do?" in result.output
        assert "Added to Next Actions with context: @phone" in result.output


class TestInteractiveSync:
    """Test interactive sync features."""

    def setup_method(self):
        self.runner = CliRunner()

    @patch("dayflow.core.sync.CalendarSyncEngine")
    @pytest.mark.tdd
    def test_sync_conflict_resolution(self, mock_sync):
        """Test interactive conflict resolution during sync."""
        # Mock a sync conflict
        mock_engine = Mock()
        mock_engine.sync.side_effect = SyncConflictError(
            "Daily note already contains calendar section",
            existing_content="Existing calendar data",
            new_content="New calendar data",
        )
        mock_sync.return_value = mock_engine

        # User chooses to merge
        result = self.runner.invoke(cli, ["sync"], input="merge\n")

        assert "Conflict detected" in result.output
        assert "How would you like to resolve?" in result.output
        assert "[merge/replace/skip]" in result.output

    @pytest.mark.tdd
    def test_continuous_sync_confirmation(self):
        """Test confirmation for continuous sync mode."""
        with patch("dayflow.ui.cli.auth.has_valid_token", return_value=True):
            with patch("dayflow.ui.cli.auth.get_token_info") as mock_info:
                mock_info.return_value = {"expires_in_minutes": 45}

                # User confirms continuous sync
                result = self.runner.invoke(cli, ["sync", "--continuous"], input="y\n")

                assert "Token expires in 45 minutes" in result.output
                assert "Run continuous sync until token expires?" in result.output


class TestProgressIndicators:
    """Test progress indicators and user feedback."""

    def setup_method(self):
        self.runner = CliRunner()

    @patch("dayflow.core.sync.CalendarSyncEngine")
    @pytest.mark.tdd
    def test_sync_progress_bar(self, mock_sync):
        """Test progress bar during sync."""

        # Mock sync with progress callback
        def mock_sync_with_progress(start_date, end_date, progress_callback=None):
            if progress_callback:
                progress_callback(0, 100, "Fetching events...")
                progress_callback(50, 100, "Processing events...")
                progress_callback(100, 100, "Writing to Obsidian...")
            return {"events_synced": 10}

        mock_engine = Mock()
        mock_engine.sync = mock_sync_with_progress
        mock_sync.return_value = mock_engine

        with patch("dayflow.ui.cli.auth.has_valid_token", return_value=True):
            result = self.runner.invoke(cli, ["sync", "--show-progress"])

        # Should show progress indicators
        assert "Fetching events..." in result.output
        assert "Processing events..." in result.output
        assert "Writing to Obsidian..." in result.output


class TestBatchOperations:
    """Test batch operation confirmations."""

    def setup_method(self):
        self.runner = CliRunner()

    @pytest.mark.tdd
    def test_batch_zettel_creation_confirmation(self):
        """Test confirmation for batch note creation."""
        with patch("dayflow.core.zettel.ZettelkastenEngine") as mock_zettel:
            mock_engine = Mock()
            mock_engine.find_unprocessed_literature_notes.return_value = [
                "Meeting Notes/2024-01-01 Project Review.md",
                "Meeting Notes/2024-01-02 Team Standup.md",
                "Meeting Notes/2024-01-03 Client Call.md",
            ]
            mock_zettel.return_value = mock_engine

            # User confirms batch processing
            result = self.runner.invoke(
                cli, ["zettel", "process-literature", "--batch"], input="y\n"
            )

            assert "Found 3 literature notes to process" in result.output
            assert "Process all notes?" in result.output
            assert "[y/N]" in result.output


class TestMenuNavigation:
    """Test menu-based navigation."""

    def setup_method(self):
        self.runner = CliRunner()

    @pytest.mark.tdd
    def test_main_menu_interface(self):
        """Test main menu interface (if implemented)."""
        # User navigates through menu
        user_inputs = [
            "1",  # Select sync
            "b",  # Back to main menu
            "2",  # Select GTD
            "b",  # Back to main menu
            "q",  # Quit
        ]

        result = self.runner.invoke(
            cli, ["menu"], input="\n".join(user_inputs)  # Launch interactive menu
        )

        assert result.exit_code == 0
        assert "Dayflow" in result.output
        assert "1. Sync Calendar" in result.output
        assert "2. GTD Processing" in result.output
        assert "3. Zettelkasten" in result.output
        assert "q. Quit" in result.output


class TestAutoCompletion:
    """Test auto-completion features."""

    @pytest.mark.tdd
    def test_context_completion_in_gtd(self):
        """Test auto-completion of GTD contexts."""
        # This tests that the CLI provides completion for contexts
        _completion_test = self.runner.invoke(  # noqa: F841
            cli,
            ["gtd", "add", "--context", "@"],  # Should trigger completion
            catch_exceptions=False,
        )

        # The actual completion would be handled by Click's completion system
        # This test ensures the structure is in place


class TestUserPreferences:
    """Test saving and applying user preferences."""

    def setup_method(self):
        self.runner = CliRunner()

    @pytest.mark.tdd
    def test_remember_user_choices(self):
        """Test that CLI remembers user preferences."""
        with self.runner.isolated_filesystem():
            # First run - user sets preference
            result1 = self.runner.invoke(
                cli, ["sync"], input="always\n"  # Always merge conflicts
            )

            # Second run - should not ask again
            result2 = self.runner.invoke(cli, ["sync"])

            assert "How would you like to resolve?" in result1.output
            assert "How would you like to resolve?" not in result2.output
