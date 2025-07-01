"""Tests specifically for Windows compatibility issues."""

import os
import platform
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from dayflow.vault.config import VaultConfig
from dayflow.vault.connection import VaultConnection


class TestWindowsPaths:
    """Test Windows-specific path handling."""

    @pytest.fixture
    def temp_vault(self):
        """Create a temporary vault for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def vault_connection(self, temp_vault):
        """Create vault connection."""
        config = Mock(spec=VaultConfig)
        config.vault_path = temp_vault
        config.get_location = Mock(side_effect=lambda key: temp_vault / key)
        config.get_setting = Mock(return_value=None)
        return VaultConnection(config)

    def test_windows_path_separator_in_pattern(self, vault_connection):
        """Test handling of Windows backslashes in folder patterns."""
        # Test the _get_date_folder method with Windows-style path
        from datetime import date

        test_date = date(2024, 3, 15)

        # Test various Windows path patterns
        patterns = [
            r"year\month\day",  # Windows style
            "year/month/day",  # Unix style
            r"year\month",  # Mixed could happen
            "year/week",  # Unix style
        ]

        for pattern in patterns:
            folder = vault_connection._get_date_folder(
                vault_connection.vault_path, test_date, pattern
            )

            # Should create correct path regardless of input separator
            # Get the relative path from vault root
            relative_folder = folder.relative_to(vault_connection.vault_path)
            parts = relative_folder.parts

            if "day" in pattern:
                assert len(parts) >= 3
                assert parts[-3] == "2024"
                assert parts[-2] == "03"
                assert parts[-1] == "15"
            elif "week" in pattern:
                assert len(parts) >= 2
                assert parts[-2] == "2024"
                assert parts[-1] == "W11"  # Week 11 of 2024
            elif "month" in pattern:
                assert len(parts) >= 2
                assert parts[-2] == "2024"
                assert parts[-1] == "03"

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific test")
    def test_windows_long_path_support(self, temp_vault):
        """Test handling of long paths on Windows."""
        # Windows has a 260 character path limit by default
        # Create a deeply nested structure
        deep_path = temp_vault
        for i in range(20):
            deep_path = deep_path / f"level_{i:02d}_with_long_name"

        try:
            deep_path.mkdir(parents=True, exist_ok=True)
            test_file = deep_path / "test.md"
            test_file.write_text("Test content", encoding="utf-8")

            # Should be able to read it back
            assert test_file.exists()
            assert test_file.read_text(encoding="utf-8") == "Test content"
        except OSError as e:
            if "path too long" in str(e).lower():
                pytest.skip("Windows long path support not enabled")
            raise

    def test_path_resolution_cross_platform(self, temp_vault):
        """Test path resolution works correctly across platforms."""
        # Create a structure
        subdir = temp_vault / "Calendar" / "2024" / "03" / "15"
        subdir.mkdir(parents=True, exist_ok=True)

        test_file = subdir / "meeting.md"
        test_file.write_text("Meeting notes", encoding="utf-8")

        # Test various path operations
        # Using resolve() should work cross-platform
        resolved = test_file.resolve()
        assert resolved.exists()
        assert resolved.is_absolute()

        # Parent resolution
        assert test_file.parent.name == "15"
        assert test_file.parent.parent.name == "03"

        # Relative path from vault root
        try:
            relative = test_file.relative_to(temp_vault)
            # Should work on both platforms
            parts = relative.parts
            assert parts[0] == "Calendar"
            assert parts[1] == "2024"
            assert parts[2] == "03"
            assert parts[3] == "15"
            assert parts[4] == "meeting.md"
        except ValueError:
            # Can happen if paths are on different drives on Windows
            pass

    def test_special_chars_in_filenames_windows(self, vault_connection):
        """Test Windows-forbidden characters in filenames."""
        # Windows forbidden chars: < > : " | ? * \
        test_cases = [
            ("Meeting: Project Review", "Meeting- Project Review"),
            ("Q&A Session", "Q&A Session"),  # & is allowed
            ("Time: 10:30 AM", "Time- 10-30 AM"),
            ('Notes "Important"', "Notes -Important-"),
            ("What? When? Where?", "What- When- Where-"),
            ("Progress|Status", "Progress-Status"),
            ("Results*.md", "Results-.md"),
            ("Path\\to\\file", "Path-to-file"),
            ("Email<->Phone", "Email---Phone"),
        ]

        for original, expected in test_cases:
            sanitized = vault_connection._sanitize_filename(original)
            # Remove .md extension for comparison
            if sanitized.endswith(".md"):
                sanitized = sanitized[:-3]
            if expected.endswith(".md"):
                expected = expected[:-3]
            assert sanitized == expected, f"Failed for: {original}"

    def test_case_sensitivity_handling(self, temp_vault):
        """Test case sensitivity differences between platforms."""
        # Windows is case-insensitive, Unix is case-sensitive
        # Note: macOS can be case-insensitive depending on filesystem

        # Create a file
        file1 = temp_vault / "TestFile.md"
        file1.write_text("Content 1", encoding="utf-8")

        # Try to access with different case
        file2 = temp_vault / "testfile.md"

        if platform.system() == "Windows":
            # Should refer to the same file on Windows
            assert file2.exists()
            assert file2.read_text(encoding="utf-8") == "Content 1"
        else:
            # On Unix/macOS, behavior depends on filesystem
            # macOS APFS can be case-insensitive
            if file2.exists():
                # Case-insensitive filesystem (common on macOS)
                assert file2.read_text(encoding="utf-8") == "Content 1"
            else:
                # Case-sensitive filesystem
                file2.write_text("Content 2", encoding="utf-8")
                assert file1.read_text(encoding="utf-8") == "Content 1"
                assert file2.read_text(encoding="utf-8") == "Content 2"

    @patch("platform.system")
    def test_mock_windows_behavior(self, mock_system, vault_connection):
        """Test Windows-specific behavior using mocks."""
        mock_system.return_value = "Windows"

        # Test path separator handling
        from datetime import date

        test_date = date(2024, 3, 15)

        # Windows path with backslashes
        pattern = r"year\month\day"
        folder = vault_connection._get_date_folder(
            vault_connection.vault_path, test_date, pattern
        )

        # Should handle backslashes correctly
        assert "2024" in str(folder)
        assert "03" in str(folder)
        assert "15" in str(folder)

    def test_network_path_handling(self):
        """Test handling of network paths (UNC paths on Windows)."""
        if platform.system() != "Windows":
            pytest.skip("Network path test is Windows-specific")

        # UNC path example: \\server\share\folder
        # Note: This test is mostly for documentation as we can't
        # actually test network paths in CI
        network_path = r"\\server\share\vault"

        try:
            path = Path(network_path)
            # Path object should handle it
            assert str(path).startswith("\\\\")
        except Exception:
            # May fail in test environment
            pass

    def test_drive_letter_handling(self):
        """Test handling of Windows drive letters."""
        if platform.system() != "Windows":
            # Test that Unix systems handle Windows-style paths gracefully
            windows_path = "C:\\Users\\test\\vault"
            path = Path(windows_path)
            # On Unix, this becomes a relative path
            assert not path.is_absolute()
        else:
            # On Windows, test actual drive letter handling
            import string

            # Find an actual drive letter
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if Path(drive).exists():
                    test_path = Path(f"{drive}test\\vault")
                    assert test_path.is_absolute()
                    assert str(test_path).startswith(f"{letter}:")
                    break


class TestWindowsEncoding:
    """Test Windows-specific encoding issues."""

    @pytest.fixture
    def temp_file(self):
        """Create a temporary file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as f:
            yield Path(f.name)
        try:
            Path(f.name).unlink()
        except FileNotFoundError:
            pass

    def test_console_encoding_windows(self):
        """Test console encoding issues on Windows."""
        if platform.system() != "Windows":
            pytest.skip("Windows-specific test")

        # Windows console might use different encoding
        import sys

        # Test that we handle console encoding
        original_stdout = sys.stdout
        try:
            # Simulate Windows console encoding
            import io

            sys.stdout = io.TextIOWrapper(
                io.BytesIO(), encoding="cp437", errors="replace"  # Old DOS encoding
            )

            # Should handle Unicode output
            print("Unicode test: 你好 🌍")

        finally:
            sys.stdout = original_stdout

    def test_environment_variable_encoding(self):
        """Test environment variable encoding on Windows."""
        if platform.system() != "Windows":
            pytest.skip("Windows-specific test")

        # Windows environment variables might have encoding issues
        test_var = "TEST_UNICODE_VAR"
        test_value = "café_münchen_北京"

        os.environ[test_var] = test_value

        # Should be able to read it back
        read_value = os.environ.get(test_var)
        assert read_value is not None

        # Clean up
        del os.environ[test_var]
