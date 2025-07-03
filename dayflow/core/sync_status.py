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

        # Check if continuous sync is running
        status["sync_mode"] = get_sync_mode()

        return status
    except Exception:
        return None


def get_sync_mode() -> str:
    """Determine the current sync mode.

    Returns:
        "continuous" if continuous sync is running
        "manual" if only manual syncs have been done
        "unknown" if no sync information available
    """
    pid_file = Path.home() / ".dayflow" / "sync.pid"

    if pid_file.exists():
        try:
            # Check if the PID is still running
            pid = int(pid_file.read_text().strip())

            # Simple check - see if we can send signal 0
            # (doesn't actually send a signal)
            try:
                import os

                os.kill(pid, 0)
                return "continuous"
            except (OSError, ProcessLookupError):
                # Process not running, clean up stale PID file
                pid_file.unlink()
        except Exception:
            pass

    # Check status file for interval_minutes as indicator of continuous mode
    status_file = Path.home() / ".dayflow" / "sync_status.json"
    if status_file.exists():
        try:
            status = json.loads(status_file.read_text(encoding="utf-8"))
            if status.get("interval_minutes"):
                # Has interval configured but not running
                return "manual"
        except Exception:
            pass

    return "manual"
