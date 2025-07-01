"""
Common exceptions for Dayflow.
"""


class DayflowError(Exception):
    """Base exception for all Dayflow errors."""

    pass


class NetworkError(DayflowError):
    """Network-related errors."""

    pass


class VaultNotFoundError(DayflowError):
    """Vault not found error."""

    def __init__(self, path: str):
        self.path = path
        super().__init__(f"Obsidian vault not found at: {path}")


class SyncConflictError(DayflowError):
    """Sync conflict error."""

    def __init__(self, message: str, existing_content: str = "", new_content: str = ""):
        self.existing_content = existing_content
        self.new_content = new_content
        super().__init__(message)
