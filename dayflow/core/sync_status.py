"""Sync status utilities."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


def get_sync_status() -> Optional[Dict[str, Any]]:
    """Get the current sync status.

    Returns:
        Dict with sync status information or None if no status file exists
    """
    status_file = Path.home() / ".dayflow" / "sync_status.json"

    if not status_file.exists():
        return None

    try:
        status: Dict[str, Any] = json.loads(status_file.read_text(encoding="utf-8"))

        # Add calculated fields
        if status.get("last_sync"):
            last_sync = datetime.fromisoformat(status["last_sync"])
            status["last_sync_datetime"] = last_sync
            status["time_since_last_sync"] = datetime.now() - last_sync

        return status
    except Exception:
        return None
