"""
Test cases for the main CLI interface.
These tests define the expected behavior of the Dayflow CLI.

Following TDD principles:
1. These tests are written BEFORE implementation
2. They should all FAIL initially
3. We implement only enough code to make them pass
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
from datetime import datetime, date, timedelta
from pathlib import Path

# These imports will fail initially - that's expected in TDD
from dayflow.ui.cli import cli, main


class TestCLIBasicCommands:
    """Test basic CLI commands and structure."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_cli_exists_and_runs(self):
        """Test that the CLI can be invoked without errors.
        
        Expected behavior:
        - CLI should run without any arguments
        - Should display a welcome message with the app name
        - Should show basic usage instructions
        - Should NOT perform any actions without explicit commands
        - Exit code should be 0 (success)
        """
        result = self.runner.invoke(cli)
        
        # Basic success
        assert result.exit_code == 0
        
        # Welcome message
        assert "Dayflow" in result.output
        
        # Should show available commands hint
        assert "Usage:" in result.output or "Commands:" in result.output
        
        # Should suggest getting help
        assert "--help" in result.output or "help" in result.output
        
        # Should NOT perform any sync or other operations
        assert "Syncing" not in result.output
        assert "Fetching" not in result.output
    
    def test_cli_has_help(self):
        """Test that --help works and shows expected commands.
        
        Expected behavior:
        - Should show all main commands with descriptions
        - Each command should have a brief explanation
        - Should show global options (--version, --help)
        - Should show how to get help for subcommands
        """
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        
        # Should have standard help sections
        assert "Usage:" in result.output
        assert "Options:" in result.output
        assert "Commands:" in result.output
        
        # Expected commands with descriptions
        expected_commands = {
            'sync': 'Synchronize calendar events to Obsidian',
            'auth': 'Manage authentication and tokens',
            'gtd': 'GTD (Getting Things Done) operations',
            'zettel': 'Zettelkasten note management',
            'config': 'Configuration management',
            'status': 'Show system status and health',
        }
        
        for command, description in expected_commands.items():
            # Command should be listed
            assert command in result.output, f"Command '{command}' not found in help"
            # Should have some description (not checking exact text)
            lines = result.output.split('\n')
            command_line = next((line for line in lines if command in line), None)
            assert command_line is not None, f"Command '{command}' not properly formatted"
            # The description should be on the same line or next line
            assert any(word in result.output for word in description.split()[:3])
    
    def test_version_command(self):
        """Test --version shows version information."""
        result = self.runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert "version" in result.output.lower()


class TestAuthCommand:
    """Test authentication-related CLI commands."""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    def test_auth_status_when_no_token(self):
        """Test 'auth status' when no token exists.
        
        Expected behavior:
        - Should NOT crash when no token exists
        - Should clearly indicate no token is available
        - Should provide instructions on how to authenticate
        - Should NOT attempt to make API calls
        - Exit code should be 0 (checking status is not an error)
        """
        # Ensure no token file exists
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ['auth', 'status'])
            
            # Should complete successfully
            assert result.exit_code == 0
            
            # Clear message about missing token
            assert "No valid token found" in result.output or "Not authenticated" in result.output
            
            # Should provide next steps
            assert "auth login" in result.output
            
            # Should NOT show token details
            assert "expires" not in result.output.lower()
            assert "valid for" not in result.output.lower()
    
    @patch('dayflow.ui.cli.get_token_info')
    def test_auth_status_with_valid_token(self, mock_token_info):
        """Test 'auth status' with a valid token."""
        mock_token_info.return_value = {
            'valid': True,
            'expires_at': datetime.now() + timedelta(minutes=30),
            'age_minutes': 30
        }
        
        result = self.runner.invoke(cli, ['auth', 'status'])
        assert result.exit_code == 0
        assert "Token is valid" in result.output
        # Check for approximate time (29-30 minutes due to timing)
        assert "Expires in " in result.output
        assert "minutes" in result.output
    
    @patch('webbrowser.open')
    @patch('subprocess.check_output')
    def test_auth_login(self, mock_clipboard, mock_browser):
        """Test 'auth login' command flow.
        
        This is THE CRITICAL TEST for Mayo Clinic authentication.
        
        Expected behavior:
        1. Opens Microsoft Graph Explorer in browser
        2. Provides clear instructions for manual token copy
        3. Waits for user to copy token to clipboard
        4. Reads token from clipboard (macOS pbpaste)
        5. Validates token length (>100 chars)
        6. Stores token securely with metadata
        7. Shows success confirmation
        
        Token storage format should include:
        - access_token: The actual token
        - acquired_at: When token was obtained
        - expires_at: Calculated expiry (1 hour from acquisition)
        - source: "graph_explorer_manual"
        """
        # Simulate clipboard containing a valid token (long string)
        mock_clipboard.return_value = b'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6' + b'x' * 1000
        
        # Run in non-interactive mode for testing
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ['auth', 'login', '--no-interactive'])
            
            # Should succeed
            assert result.exit_code == 0
            
            # Browser should open to Graph Explorer
            assert mock_browser.called
            mock_browser.assert_called_with('https://developer.microsoft.com/en-us/graph/graph-explorer')
            
            # Should read from clipboard
            assert mock_clipboard.called
            mock_clipboard.assert_called_with(['pbpaste'])
            
            # Should show success
            assert "Token saved successfully" in result.output
            
            # Token file should exist
            assert Path('.graph_token').exists()
            
            # Verify token file format
            import json
            with open('.graph_token', 'r') as f:
                token_data = json.load(f)
            
            assert 'access_token' in token_data
            assert token_data['access_token'].startswith('eyJ0eXAiOiJKV1QiLCJhbGc')
            assert 'acquired_at' in token_data
            assert 'expires_at' in token_data
            assert 'source' in token_data
            assert token_data['source'] == 'graph_explorer_manual'
    
    def test_auth_logout(self):
        """Test 'auth logout' removes token."""
        with self.runner.isolated_filesystem():
            # Create a fake token file
            with open('.graph_token', 'w') as f:
                f.write('{"token": "fake"}')
            
            result = self.runner.invoke(cli, ['auth', 'logout'])
            assert result.exit_code == 0
            assert "Logged out successfully" in result.output
            assert not Path('.graph_token').exists()


class TestSyncCommand:
    """Test calendar sync CLI commands."""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    @patch('dayflow.core.sync.CalendarSyncEngine')
    def test_sync_requires_auth(self, mock_sync_engine):
        """Test sync fails gracefully when not authenticated.
        
        Expected behavior:
        - Should check for valid authentication before attempting sync
        - Should NOT attempt to connect to Graph API without token
        - Should provide clear error message
        - Should guide user to authenticate first
        - Exit code should be 1 (error)
        - Should NOT create any files or make changes
        """
        # Ensure no token exists
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ['sync'])
            
            # Should fail with error code
            assert result.exit_code == 1
            
            # Clear authentication error
            assert "not authenticated" in result.output.lower() or "no token" in result.output.lower()
            
            # Helpful guidance
            assert "auth login" in result.output
            
            # Should NOT have attempted sync
            assert mock_sync_engine.called is False
            
            # Should not show sync-related messages
            assert "Syncing" not in result.output
            assert "Fetching events" not in result.output
    
    @patch('dayflow.core.sync.CalendarSyncEngine')
    @patch('dayflow.ui.cli.has_valid_token')
    @patch('dayflow.vault.VaultConfig')
    def test_sync_basic(self, mock_vault_config, mock_has_token, mock_sync_engine):
        """Test basic sync command."""
        mock_has_token.return_value = True
        # Mock vault configuration error - no vault configured
        mock_vault_config.side_effect = Exception("No vault configured")
        
        mock_sync = Mock()
        mock_sync.sync.return_value = {
            'events_synced': 5,
            'notes_created': 0,
            'notes_updated': 0,
            'events': [],
            'sync_time': datetime.now()
        }
        mock_sync_engine.return_value = mock_sync
        
        # Create a mock token file
        with self.runner.isolated_filesystem():
            token_file = Path('.graph_token')
            with open(token_file, 'w') as f:
                json.dump({'access_token': 'mock_token', 'expires_at': (datetime.now() + timedelta(hours=1)).isoformat()}, f)
            
            # Should prompt to continue without vault, we'll simulate "yes"
            result = self.runner.invoke(cli, ['sync'], input='y\n')
            assert result.exit_code == 0
            assert "Synced 5 active events" in result.output
            assert "(No notes created - vault not configured)" in result.output
    
    def test_sync_with_date_range(self):
        """Test sync with custom date range."""
        with patch('dayflow.ui.cli.has_valid_token', return_value=True):
            with patch('dayflow.core.sync.CalendarSyncEngine') as mock_sync_engine:
                mock_sync = Mock()
                mock_sync.sync.return_value = {
                    'events_synced': 2,
                    'notes_updated': 0,
                    'events': [],
                    'sync_time': datetime.now()
                }
                mock_sync_engine.return_value = mock_sync
                
                # Create a mock token file
                with self.runner.isolated_filesystem():
                    token_file = Path('.graph_token')
                    with open(token_file, 'w') as f:
                        json.dump({'access_token': 'mock_token'}, f)
                    
                    result = self.runner.invoke(cli, [
                        'sync',
                        '--start', '2024-01-01',
                        '--end', '2024-01-07'
                    ])
                    
                    # Should parse dates correctly
                    assert result.exit_code == 0
                    # Check that sync was called with date objects
                    mock_sync.sync.assert_called_once()
                    call_args = mock_sync.sync.call_args
                    assert call_args.kwargs['start_date'] == date(2024, 1, 1)
                    assert call_args.kwargs['end_date'] == date(2024, 1, 7)
    
    def test_sync_continuous_mode(self):
        """Test continuous sync mode."""
        with patch('dayflow.ui.cli.has_valid_token', return_value=True):
            # Create a mock token file
            with self.runner.isolated_filesystem():
                token_file = Path('.graph_token')
                with open(token_file, 'w') as f:
                    json.dump({'access_token': 'mock_token'}, f)
                
                result = self.runner.invoke(cli, [
                    'sync',
                    '--continuous',
                    '--interval', '5'
                ])
                
                # Currently not implemented
                assert result.exit_code == 0
                assert "Continuous sync not yet implemented" in result.output


class TestGTDCommand:
    """Test GTD-related CLI commands."""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    def test_gtd_inbox_show(self):
        """Test showing GTD inbox items."""
        with patch('dayflow.core.gtd.GTDSystem') as mock_gtd:
            mock_system = Mock()
            mock_system.get_inbox_items.return_value = [
                {'id': 1, 'content': 'Call Bob about project'},
                {'id': 2, 'content': 'Review meeting notes'}
            ]
            mock_gtd.return_value = mock_system
            
            result = self.runner.invoke(cli, ['gtd', 'inbox'])
            assert result.exit_code == 0
            assert "Call Bob about project" in result.output
            assert "Review meeting notes" in result.output
    
    def test_gtd_process(self):
        """Test processing inbox items."""
        result = self.runner.invoke(cli, ['gtd', 'process'])
        assert result.exit_code == 0
        # Should start interactive processing
    
    def test_gtd_review_generate(self):
        """Test generating weekly review."""
        with patch('dayflow.core.gtd.WeeklyReviewGenerator') as mock_review:
            mock_generator = Mock()
            mock_generator.generate.return_value = "Weekly review content"
            mock_review.return_value = mock_generator
            
            result = self.runner.invoke(cli, ['gtd', 'review', '--generate'])
            assert result.exit_code == 0
            assert "Weekly review generated" in result.output


class TestZettelCommand:
    """Test Zettelkasten CLI commands."""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    def test_zettel_new_note(self):
        """Test creating new Zettelkasten note."""
        result = self.runner.invoke(cli, [
            'zettel', 'new',
            '--title', 'Test Note',
            '--content', 'This is a test note'
        ])
        assert result.exit_code == 0
        assert "Created note" in result.output
        # Should show the generated ID
    
    def test_zettel_suggest_permanent_notes(self):
        """Test suggesting permanent notes from literature notes."""
        with patch('dayflow.core.zettel.ZettelkastenEngine') as mock_zettel:
            mock_engine = Mock()
            mock_engine.suggest_permanent_notes.return_value = [
                {'title': 'Concept A', 'reason': 'Extends existing note on X'},
                {'title': 'Concept B', 'reason': 'New insight on Y'}
            ]
            mock_zettel.return_value = mock_engine
            
            result = self.runner.invoke(cli, ['zettel', 'suggest'])
            assert result.exit_code == 0
            assert "Concept A" in result.output
            assert "Concept B" in result.output


class TestConfigCommand:
    """Test configuration management commands."""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    def test_config_show(self):
        """Test showing current configuration."""
        result = self.runner.invoke(cli, ['config', 'show'])
        assert result.exit_code == 0
        assert "Configuration" in result.output
    
    def test_config_set_vault_path(self):
        """Test setting Obsidian vault path."""
        test_path = "/Users/test/Obsidian/Vault"
        result = self.runner.invoke(cli, [
            'config', 'set',
            'obsidian.vault_path',
            test_path
        ])
        assert result.exit_code == 0
        assert f"Set obsidian.vault_path to {test_path}" in result.output
    
    def test_config_validate(self):
        """Test configuration validation."""
        result = self.runner.invoke(cli, ['config', 'validate'])
        assert result.exit_code == 0
        # Should check vault exists, timezone is valid, etc.


class TestStatusCommand:
    """Test status command showing system state."""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    @patch('dayflow.ui.cli.status.get_system_status')
    def test_status_overview(self, mock_status):
        """Test status command shows system overview."""
        mock_status.return_value = {
            'auth': {'status': 'valid', 'expires_in': 30},
            'vault': {'path': '/Users/test/vault', 'exists': True},
            'last_sync': '2024-01-01 10:00:00',
            'pending_tasks': 5
        }
        
        result = self.runner.invoke(cli, ['status'])
        assert result.exit_code == 0
        assert "Authentication: valid" in result.output
        assert "Vault: /Users/test/vault" in result.output
        assert "Last sync: 2024-01-01 10:00:00" in result.output
        assert "Pending tasks: 5" in result.output


class TestCLIErrorHandling:
    """Test CLI error handling and user feedback."""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    def test_network_error_handling(self):
        """Test graceful handling of network errors."""
        with patch('dayflow.core.sync.CalendarSyncEngine') as mock_sync:
            mock_sync.side_effect = NetworkError("Connection failed")
            
            result = self.runner.invoke(cli, ['sync'])
            assert result.exit_code == 1
            assert "Network error" in result.output
            assert "Please check your internet connection" in result.output
    
    def test_vault_not_found_error(self):
        """Test handling of missing Obsidian vault."""
        with patch('dayflow.core.vault.ObsidianVault') as mock_vault:
            mock_vault.side_effect = VaultNotFoundError("/path/to/vault")
            
            result = self.runner.invoke(cli, ['sync'])
            assert result.exit_code == 1
            assert "Obsidian vault not found" in result.output
            assert "Please run 'config set obsidian.vault_path'" in result.output


# Test fixtures and helper functions
@pytest.fixture
def mock_config():
    """Mock configuration for tests."""
    return {
        'obsidian': {
            'vault_path': '/Users/test/Obsidian/TestVault',
            'timezone': 'America/Chicago'
        },
        'sync': {
            'interval_minutes': 5,
            'days_ahead': 7
        }
    }


@pytest.fixture
def mock_token():
    """Mock valid token for tests."""
    return {
        'access_token': 'fake_token_12345',
        'expires_at': (datetime.now() + timedelta(minutes=45)).isoformat()
    }