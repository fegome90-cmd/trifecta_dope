"""
Daemon path utilities to ensure AF_UNIX socket path limits are respected.

Unix domain sockets have a path length limit (~108 chars on macOS/Linux).
Using tmp_path in tests creates paths too long, so we use /tmp with short names.
"""

from pathlib import Path
import tempfile


def get_daemon_socket_path(segment_id: str) -> Path:
    """
    Get short socket path for daemon IPC.

    Format: /tmp/trifecta_lsp_<segment_id>.sock
    Max length: ~35 chars (well under 108 char limit)
    """
    tmp_dir = Path(tempfile.gettempdir())
    return tmp_dir / f"trifecta_lsp_{segment_id}.sock"


def get_daemon_lock_path(segment_id: str) -> Path:
    """Get short lock file path for daemon singleton."""
    tmp_dir = Path(tempfile.gettempdir())
    return tmp_dir / f"trifecta_lsp_{segment_id}.lock"


def get_daemon_pid_path(segment_id: str) -> Path:
    """Get short PID file path for daemon process tracking."""
    tmp_dir = Path(tempfile.gettempdir())
    return tmp_dir / f"trifecta_lsp_{segment_id}.pid"
