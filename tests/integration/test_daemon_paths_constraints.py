"""
Test daemon path validation (platform constraints).

Verifies that daemon paths respect AF_UNIX socket limits and /tmp accessibility.
"""

import pytest
from src.infrastructure.daemon_paths import (
    get_daemon_socket_path,
    get_daemon_lock_path,
    get_daemon_pid_path,
    MAX_UNIX_SOCKET_PATH,
)


def test_socket_path_under_limit():
    """Tripwire: Socket paths must be under AF_UNIX limit."""
    seg_id = "6f25e381"  # Typical 8-char hash

    socket_path = get_daemon_socket_path(seg_id)

    # Must be under conservative limit
    assert len(str(socket_path)) <= MAX_UNIX_SOCKET_PATH, (
        f"Socket path too long: {len(str(socket_path))} chars (limit {MAX_UNIX_SOCKET_PATH})"
    )


def test_all_daemon_paths_under_limit():
    """All daemon paths (socket/lock/pid) must be under limit."""
    seg_id = "test_seg"

    paths = [
        ("socket", get_daemon_socket_path(seg_id)),
        ("lock", get_daemon_lock_path(seg_id)),
        ("pid", get_daemon_pid_path(seg_id)),
    ]

    for name, path in paths:
        assert len(str(path)) <= MAX_UNIX_SOCKET_PATH, (
            f"{name} path too long: {len(str(path))} chars"
        )


def test_daemon_base_dir_exists():
    """Base directory (/tmp) must exist for daemon paths to work."""
    seg_id = "test"

    # Should not raise if /tmp exists
    socket_path = get_daemon_socket_path(seg_id)

    # Parent should exist
    assert socket_path.parent.exists(), f"Base dir doesn't exist: {socket_path.parent}"


def test_validation_fails_on_inaccessible_dir(monkeypatch, tmp_path):
    """If /tmp is inaccessible, fail explicitly with RuntimeError."""
    # Simulate gettempdir() returning non-existent directory
    fake_tmp = tmp_path / "nonexistent_tmp_xyz"
    monkeypatch.setattr("tempfile.gettempdir", lambda: str(fake_tmp))

    with pytest.raises(RuntimeError, match="does not exist"):
        get_daemon_socket_path("test")


def test_path_length_validation():
    """If somehow path exceeds limit, fail explicitly."""
    # Create unrealistically long segment ID (would never happen in practice)
    long_seg_id = "x" * 200  # Forces path over limit

    with pytest.raises(RuntimeError, match="path too long"):
        get_daemon_socket_path(long_seg_id)
