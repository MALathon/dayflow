"""Tests for cross-platform encoding compatibility."""

import platform
import tempfile
from pathlib import Path

import pytest


class TestEncoding:
    """Test encoding handling across platforms."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_unicode_content_write_read(self, temp_dir):
        """Test writing and reading files with Unicode content."""
        # Test various Unicode characters that often cause issues
        test_content = """
        # Meeting Notes 📅

        Attendees: José García, François Müller, 王明 (Wang Ming)

        Topics:
        - Project α (alpha) review ✓
        - β testing phase 🚀
        - Financial review (€1,234.56)
        - Timeline: Q1 → Q2 transition

        Emojis: 😊 🎯 💡 ⏰ 📊
        Special chars: ñ ü ß ø æ
        Math symbols: ∑ ∏ √ ∞ ≈
        Arrows: → ← ↑ ↓ ⇒ ⇐
        """

        # Write with explicit UTF-8 encoding
        test_file = temp_dir / "unicode_test.md"
        test_file.write_text(test_content, encoding="utf-8")

        # Read back with explicit UTF-8 encoding
        read_content = test_file.read_text(encoding="utf-8")

        # Should match exactly
        assert read_content == test_content

        # Verify specific characters are preserved
        assert "📅" in read_content
        assert "José García" in read_content
        assert "€1,234.56" in read_content
        assert "→" in read_content

    def test_emoji_in_filenames(self, temp_dir):
        """Test handling files with emojis in names."""
        # Some filesystems don't support emojis in filenames
        filename = "Meeting_Notes_📅_2024.md"
        content = "Test content"

        try:
            test_file = temp_dir / filename
            test_file.write_text(content, encoding="utf-8")

            # Verify file exists and can be read
            assert test_file.exists()
            assert test_file.read_text(encoding="utf-8") == content
        except (OSError, UnicodeError) as e:
            # Some filesystems may not support emojis in filenames
            pytest.skip(f"Filesystem doesn't support emojis in filenames: {e}")

    def test_path_separator_handling(self, temp_dir):
        """Test cross-platform path separator handling."""
        # Create nested directory structure
        nested_path = temp_dir / "level1" / "level2" / "level3"
        nested_path.mkdir(parents=True)

        test_file = nested_path / "test.md"
        test_file.write_text("test content", encoding="utf-8")

        # Convert to string and back to Path
        path_str = str(test_file)
        reconstructed_path = Path(path_str)

        # Should work regardless of platform
        assert reconstructed_path.exists()
        assert reconstructed_path.read_text(encoding="utf-8") == "test content"

        # Test path operations
        assert test_file.parent.name == "level3"
        assert test_file.parent.parent.name == "level2"

    def test_windows_cp1252_fallback(self, temp_dir):
        """Test handling of CP1252 encoded files on Windows."""
        if platform.system() != "Windows":
            pytest.skip("Windows-specific test")

        test_file = temp_dir / "cp1252_test.md"
        content = "Windows specific content with special chars: café"

        # Write with CP1252 encoding (Windows default for some operations)
        test_file.write_text(content, encoding="cp1252")

        # Should be able to read with UTF-8 or handle gracefully
        try:
            # Try UTF-8 first
            read_content = test_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Fall back to CP1252
            read_content = test_file.read_text(encoding="cp1252")

        assert "café" in read_content

    def test_line_ending_normalization(self, temp_dir):
        """Test handling of different line endings across platforms."""
        test_file = temp_dir / "line_endings.md"

        # Test content with explicit line endings
        content_unix = "Line 1\nLine 2\nLine 3"

        # Write with Unix line endings
        test_file.write_text(content_unix, encoding="utf-8")
        read_content = test_file.read_text(encoding="utf-8")

        # Should handle line endings based on platform
        if platform.system() == "Windows":
            # Windows might convert to \r\n
            assert "Line 1" in read_content
            assert "Line 2" in read_content
            assert "Line 3" in read_content
        else:
            assert read_content == content_unix

    def test_special_characters_in_paths(self, temp_dir):
        """Test handling paths with special characters."""
        # Test directory names with spaces and special chars
        special_dir = temp_dir / "My Documents" / "Project (2024)" / "Notes & Ideas"
        special_dir.mkdir(parents=True, exist_ok=True)

        test_file = special_dir / "meeting notes.md"
        test_file.write_text("Content in special path", encoding="utf-8")

        # Verify we can read it back
        assert test_file.exists()
        assert test_file.read_text(encoding="utf-8") == "Content in special path"

        # Test path string handling
        path_str = str(test_file)
        assert "My Documents" in path_str
        assert "Project (2024)" in path_str
        assert "Notes & Ideas" in path_str

    def test_bom_handling(self, temp_dir):
        """Test handling of Byte Order Mark (BOM) in files."""
        test_file = temp_dir / "bom_test.md"
        content = "Test content"

        # Write with UTF-8 BOM
        with open(test_file, "w", encoding="utf-8-sig") as f:
            f.write(content)

        # Standard UTF-8 will include the BOM character
        read_content = test_file.read_text(encoding="utf-8")
        # BOM appears as zero-width no-break space
        assert read_content == "\ufeff" + content or read_content == content

        # utf-8-sig will strip the BOM
        read_content_sig = test_file.read_text(encoding="utf-8-sig")
        assert read_content_sig == content

    @pytest.mark.parametrize(
        "char,name",
        [
            ("€", "euro"),
            ("£", "pound"),
            ("¥", "yen"),
            ("°", "degree"),
            ("±", "plus_minus"),
            ("²", "squared"),
            ("³", "cubed"),
            ("µ", "micro"),
            ("¼", "quarter"),
            ("½", "half"),
            ("¾", "three_quarters"),
            ("×", "multiply"),
            ("÷", "divide"),
            ("∞", "infinity"),
            ("π", "pi"),
            ("Σ", "sigma"),
            ("√", "sqrt"),
            ("∫", "integral"),
            ("≈", "approx"),
            ("≠", "not_equal"),
            ("≤", "less_equal"),
            ("≥", "greater_equal"),
            ("◊", "diamond"),
            ("♠", "spade"),
            ("♣", "club"),
            ("♥", "heart"),
            ("♦", "diamond_suit"),
        ],
    )
    def test_special_character_preservation(self, temp_dir, char, name):
        """Test that special characters are preserved correctly."""
        test_file = temp_dir / f"{name}_test.md"
        content = f"Special character test: {char}"

        test_file.write_text(content, encoding="utf-8")
        read_content = test_file.read_text(encoding="utf-8")

        assert char in read_content
        assert read_content == content

    def test_large_unicode_file(self, temp_dir):
        """Test handling of large files with Unicode content."""
        test_file = temp_dir / "large_unicode.md"

        # Generate large content with various Unicode
        lines = []
        for i in range(1000):
            lines.append(f"Line {i}: 你好世界 🌍 Здравствуй мир こんにちは世界 {i * 'x'}")

        large_content = "\n".join(lines)

        # Write and read back
        test_file.write_text(large_content, encoding="utf-8")
        read_content = test_file.read_text(encoding="utf-8")

        assert read_content == large_content
        assert "你好世界" in read_content
        assert "🌍" in read_content
        assert "Здравствуй мир" in read_content
        assert "こんにちは世界" in read_content


class TestEncodingErrorHandling:
    """Test error handling for encoding issues."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_mixed_encoding_graceful_handling(self, temp_dir):
        """Test graceful handling of files with mixed or unknown encoding."""
        test_file = temp_dir / "mixed_encoding.txt"

        # Write raw bytes that might cause encoding issues
        test_bytes = b"Normal text\n\x80\x81\x82\x83\nMore text"
        test_file.write_bytes(test_bytes)

        # Try to read with error handling
        try:
            content = test_file.read_text(encoding="utf-8", errors="replace")
            assert "Normal text" in content
            assert "More text" in content
            # Invalid bytes should be replaced with replacement character
            assert "�" in content or "\ufffd" in content
        except Exception as e:
            pytest.fail(f"Should handle encoding errors gracefully: {e}")

    def test_encoding_detection_fallback(self, temp_dir):
        """Test fallback encoding detection."""
        test_file = temp_dir / "unknown_encoding.md"

        # Common test strings in different languages
        test_strings = [
            ("English", "Hello World"),
            ("Spanish", "Hola Mundo ñáéíóú"),
            ("French", "Bonjour le monde àèéêç"),
            ("German", "Hallo Welt äöüß"),
            ("Russian", "Привет мир"),
            ("Japanese", "こんにちは世界"),
            ("Chinese", "你好世界"),
            ("Arabic", "مرحبا بالعالم"),
            ("Hebrew", "שלום עולם"),
            ("Greek", "Γεια σου κόσμος"),
        ]

        for lang, text in test_strings:
            content = f"# {lang}\n{text}\n"

            # Write with UTF-8
            test_file.write_text(content, encoding="utf-8")

            # Read back
            read_content = test_file.read_text(encoding="utf-8")
            assert text in read_content, f"Failed to preserve {lang} text"
