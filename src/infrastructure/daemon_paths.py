"""
Daemon path utilities to ensure AF_UNIX socket path limits are respected.

Unix domain sockets have a path length limit (~108 chars on macOS/Linux).
Using tmp_path in tests creates paths too long, so we use /tmp with short names.
"""

from pathlib import Path
import tempfile
import os

# AF_UNIX socket path limit (conservative estimate for cross-platform)
MAX_UNIX_SOCKET_PATH = 100


def _validate_daemon_base_dir(tmp_dir: Path) -> None:
    """
        Validate that base directory for daemon files is accessible.

        Raises:
            Runtime

    Error: If tmp_dir doesn't exist or isn't writable.
    """
    if not tmp_dir.exists():
        raise RuntimeError(
            f"Daemon base directory does not exist: {tmp_dir}. Cannot create daemon IPC files."
        )

    if not os.access(tmp_dir, os.W_OK):
        raise RuntimeError(
            f"Daemon base directory is not writable: {tmp_dir}. Cannot create daemon IPC files."
        )


def _validate_path_length(path: Path, path_type: str) -> None:
    """
    Validate that path is under AF_UNIX socket length limit.

    Args:
        path: Path to validate
        path_type: Description (e.g. "socket", "lock", "pid")

    Raises:
        RuntimeError: If path exceeds MAX_UNIX_SOCKET_PATH
    """
    path_str = str(path)
    if len(path_str) > MAX_UNIX_SOCKET_PATH:
        raise RuntimeError(
            f"Daemon {path_type} path too long ({len(path_str)} chars, "
            f"limit {MAX_UNIX_SOCKET_PATH}): {path_str}"
        )


def get_daemon_socket_path(segment_id: str) -> Path:
    """
    Get short socket path for daemon IPC.

    Format: /tmp/trifecta_lsp_<segment_id>.sock
    Max length: ~35 chars (well under 108 char limit)

    Raises:
        RuntimeError: If /tmp inaccessible or path too long
    """
    tmp_dir = Path(tempfile.gettempdir())
    _validate_daemon_base_dir(tmp_dir)

    socket_path = tmp_dir / f"trifecta_lsp_{segment_id}.sock"
    _validate_path_length(socket_path, "socket")

    return socket_path


def get_daemon_lock_path(segment_id: str) -> Path:
    """
    Get short lock file path for daemon singleton.

    Raises:
        RuntimeError: If /tmp inaccessible or path too long
    """
    tmp_dir = Path(tempfile.gettempdir())
    _validate_daemon_base_dir(tmp_dir)

    lock_path = tmp_dir / f"trifecta_lsp_{segment_id}.lock"
    _validate_path_length(lock_path, "lock")

    return lock_path


def get_daemon_pid_path(segment_id: str) -> Path:
    """
    Get short PID file path for daemon process tracking.

    Raises:
        RuntimeError: If /tmp inaccessible or path too long
    """
    tmp_dir = Path(tempfile.gettempdir())
    _validate_daemon_base_dir(tmp_dir)

    pid_path = tmp_dir / f"trifecta_lsp_{segment_id}.pid"
    _validate_path_length(pid_path, "pid")

    return pid_path
