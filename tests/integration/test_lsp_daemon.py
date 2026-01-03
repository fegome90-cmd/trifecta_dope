"""Integration tests for LSP Daemon lifecycle.

Uses wait_for_condition polling instead of time.sleep for determinism.
"""

import os
import signal
import subprocess
import sys
import pytest
from pathlib import Path

from tests.helpers import wait_for_file, wait_for_file_removal
from src.infrastructure.lsp_daemon import LSPDaemonClient
from src.infrastructure.daemon_paths import (
    get_daemon_socket_path,
    get_daemon_pid_path,
)
from src.infrastructure.segment_utils import compute_segment_id


@pytest.fixture
def clean_daemon_env(tmp_path):
    """Provide an isolated root for daemon testing."""
    # Create marker to ensure resolve_segment_root stops here
    (tmp_path / "pyproject.toml").touch()
    yield tmp_path
    # Cleanup: kill any daemon that may still be running
    seg_id = compute_segment_id(tmp_path)
    pid_file = get_daemon_pid_path(seg_id)
    if pid_file.exists():
        try:
            os.kill(int(pid_file.read_text()), signal.SIGTERM)
        except (OSError, ValueError):
            pass


def test_daemon_spawn_and_connect(clean_daemon_env):
    """Test daemon spawn and connection lifecycle."""
    root = clean_daemon_env
    client = LSPDaemonClient(root)

    # 1. Connect should fail initially (fresh root)
    assert client._try_connect() is False

    # 2. Spawn
    spawned = client.connect_or_spawn()
    assert spawned is True

    # 3. Wait for daemon to write PID/Socket (using polling, not sleep)
    seg_id = compute_segment_id(root)
    pid_file = get_daemon_pid_path(seg_id)
    sock_file = get_daemon_socket_path(seg_id)

    assert wait_for_file(pid_file, timeout=5.0), "PID file not created"
    assert wait_for_file(sock_file, timeout=5.0), "Socket file not created"

    # 4. Connect should succeed now
    assert client._try_connect() is True

    # 5. Check Status
    status = client.send({"method": "status"})
    assert status["status"] == "ok"
    assert "state" in status["data"]


def test_daemon_singleton_lock(clean_daemon_env):
    """Tripwire: Ensure only one daemon runs per segment."""
    root = clean_daemon_env

    # Start first daemon
    client1 = LSPDaemonClient(root)
    client1.connect_or_spawn()

    seg_id = compute_segment_id(root)
    pid_file = get_daemon_pid_path(seg_id)

    # Wait for start (polling)
    assert wait_for_file(pid_file, timeout=5.0), "First daemon failed to start"
    pid1 = int(pid_file.read_text())

    # Try to start second daemon (should detect lock)
    cmd = [sys.executable, "-m", "src.infrastructure.lsp_daemon", "start", "--root", str(root)]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = p.communicate(timeout=5)

    assert "Daemon already running" in stdout

    # Verify PID unchanged
    if pid_file.exists():
        assert int(pid_file.read_text()) == pid1


def test_ttl_shutdown_cleans_files(clean_daemon_env):
    """Tripwire: Daemon shuts down after TTL and cleans up."""
    root = clean_daemon_env

    # Launch with short TTL (2s)
    cmd = [
        sys.executable,
        "-m",
        "src.infrastructure.lsp_daemon",
        "start",
        "--root",
        str(root),
        "--ttl",
        "2",
    ]
    subprocess.Popen(cmd, start_new_session=True)

    seg_id = compute_segment_id(root)
    pid_file = get_daemon_pid_path(seg_id)
    sock_file = get_daemon_socket_path(seg_id)

    # Wait for startup (polling)
    assert wait_for_file(pid_file, timeout=5.0), "Daemon failed to start"

    # Wait for TTL expiry + cleanup (polling instead of sleep(3.5))
    assert wait_for_file_removal(pid_file, timeout=6.0), "PID file should be removed after shutdown"
    assert wait_for_file_removal(sock_file, timeout=1.0), (
        "Socket file should be removed after shutdown"
    )


def test_no_blocking_on_cold_start(clean_daemon_env):
    """Tripwire: Cold start returns immediately (doesn't wait for READY)."""
    root = clean_daemon_env
    client = LSPDaemonClient(root)

    import time

    t0 = time.time()
    spawned = client.connect_or_spawn()
    t1 = time.time()

    assert spawned is True
    # Should be fast (<1s), not waiting for LSP (~2s+)
    assert (t1 - t0) < 1.0

    # Verify process spawned (polling)
    seg_id = compute_segment_id(root)
    pid_file = get_daemon_pid_path(seg_id)
    assert wait_for_file(pid_file, timeout=5.0), "Daemon did not spawn"


def test_no_long_sleeps_in_lsp_daemon(monkeypatch):
    """Tripwire: Verify no long time.sleep calls in daemon tests.

    This test reads the source file and ensures no sleep > 0.5s exists,
    enforcing the use of wait_for_condition instead.
    """
    import ast

    test_file = Path(__file__)
    tree = ast.parse(test_file.read_text())

    long_sleeps = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Check for time.sleep(X) where X > 0.5
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == "sleep":
                if node.args and isinstance(node.args[0], ast.Constant):
                    duration = node.args[0].value
                    if isinstance(duration, (int, float)) and duration > 0.5:
                        long_sleeps.append((node.lineno, duration))

    assert len(long_sleeps) == 0, (
        f"Found {len(long_sleeps)} long sleep calls. Use wait_for_condition instead: {long_sleeps}"
    )
