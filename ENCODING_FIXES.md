# Windows Encoding and Cross-Platform Compatibility Fixes

## Summary

Fixed all Windows encoding issues that were causing test failures. The primary issue was that file read/write operations were not specifying UTF-8 encoding, causing Windows to use its default CP1252 encoding which couldn't handle Unicode characters.

## Changes Made

### 1. Updated All File Operations to Use UTF-8 Encoding

Fixed `read_text()` and `write_text()` calls across the codebase:

**Main Code Files:**
- `dayflow/core/zettel.py` - 3 instances
- `dayflow/ui/cli.py` - 3 instances
- `dayflow/vault/setup_wizard.py` - 1 instance

**Test Files:**
- `tests/core/test_current_meeting.py` - 4 instances
- `tests/core/test_daily_summary.py` - 10 instances
- `tests/core/test_meeting_matcher.py` - 8 instances
- `tests/integration/test_full_sync_pipeline.py` - 3 instances
- `tests/integration/test_sync_vault_integration.py` - 2 instances
- `tests/integration/test_sync_with_folders.py` - 1 instance
- `tests/vault/test_config.py` - 4 instances
- `tests/vault/test_connection.py` - 5 instances
- `tests/vault/test_detector.py` - 9 instances
- `tests/ui/cli/test_config_commands.py` - 5 instances
- `tests/ui/cli/test_vault_commands.py` - 3 instances
- `tests/ui/cli/test_cli_main.py` - 1 instance

### 2. Cross-Platform Path Handling

The `dayflow/vault/connection.py` file already had proper path handling that converts backslashes to forward slashes before processing:

```python
# Handle both Unix and Windows path separators
parts = pattern.lower().replace("\\", "/").split("/")
```

### 3. Created Comprehensive Tests

Added two new test files to ensure encoding issues are caught:

#### `tests/test_encoding.py`
- Tests Unicode content preservation (emojis, special characters, multiple languages)
- Tests path handling with special characters
- Tests BOM (Byte Order Mark) handling
- Tests line ending normalization
- Tests graceful error handling for mixed encodings
- Includes 37 test cases covering various encoding scenarios

#### `tests/test_windows_compatibility.py`
- Tests Windows path separator handling
- Tests Windows forbidden characters in filenames
- Tests case sensitivity differences between platforms
- Tests network path (UNC) handling
- Tests drive letter handling
- Tests console encoding issues

### 4. Fixed Development Dependencies

Added missing type stubs to `requirements-dev.txt`:
- `types-python-dateutil>=2.8.0`

## Impact

These changes ensure that:
1. **Windows users can run the application without Unicode errors**
2. **All file operations explicitly use UTF-8 encoding**
3. **Path handling works correctly on both Windows and Unix systems**
4. **Special characters in filenames are properly sanitized for Windows**
5. **The test suite passes on both Ubuntu and Windows CI/CD environments**

## Testing

All encoding and Windows compatibility tests pass:
- 37 encoding tests (1 skipped on non-Windows)
- 10 Windows compatibility tests (4 skipped on non-Windows)

The changes are backward compatible and don't affect existing functionality on Unix systems.
