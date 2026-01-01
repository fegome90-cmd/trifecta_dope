import time
import socket
import pytest
import shutil
import signal
import os
import json
from pathlib import Path
from src.infrastructure.lsp_daemon import (
    LSPDaemonServer,
    LSPDaemonClient,
    SOCKET_NAME,
    LOCK_NAME,
    PID_NAME,
)
from src.infrastructure.segment_utils import compute_segment_id


@pytest.fixture
def clean_daemon_env():
    root = Path.cwd()
    seg_id = compute_segment_id(root)
    lsp_dir = root / "_ctx" / "lsp" / seg_id
    if lsp_dir.exists():
        shutil.rmtree(lsp_dir)
    return root


def test_daemon_spawn_and_connect(clean_daemon_env):
    root = clean_daemon_env
    client = LSPDaemonClient(root)

    # 1. Connect should fail initially
    assert client._try_connect() is False

    # 2. Spawn
    spawned = client.connect_or_spawn()
    assert spawned is True

    # 3. Wait for daemon to write PID/Socket (Async start)
    seg_id = compute_segment_id(root)
    lsp_dir = root / "_ctx" / "lsp" / seg_id
    pid_file = lsp_dir / PID_NAME
    sock_file = lsp_dir / SOCKET_NAME

    max_retries = 50
    for _ in range(max_retries):
        if pid_file.exists() and sock_file.exists():
            break
        time.sleep(0.1)

    assert pid_file.exists()
    assert sock_file.exists()

    # 4. Connect should succeed now
    assert client._try_connect() is True

    # 5. Check Status
    status = client.send({"method": "status"})
    assert status["status"] == "ok"
    assert "state" in status["data"]

    # Cleanup done by context manager or fixture in real world, but here explicit
    import os
    import signal

    try:
        os.kill(int(pid_file.read_text()), signal.SIGTERM)
    except:
        pass


def test_daemon_singleton_lock(clean_daemon_env):
    """Tripwire: Ensure only one daemon runs per segment."""
    root = clean_daemon_env

    # Start first daemon manually
    client1 = LSPDaemonClient(root)
    client1.connect_or_spawn()

    seg_id = compute_segment_id(root)
    pid_file = root / "_ctx" / "lsp" / seg_id / PID_NAME
    # Wait for start
    for _ in range(50):
        if pid_file.exists():
            break
        time.sleep(0.05)

    pid1 = int(pid_file.read_text())

    # Try to start second daemon manually (simulate race or duplicate logic)
    # We use subprocess directly to simulate independent process launch
    import sys
    import subprocess

    # Launch identical start command
    cmd = [sys.executable, "-m", "src.infrastructure.lsp_daemon", "start", "--root", str(root)]
    # This should exit immediately because lock is held
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = p.communicate(timeout=5)

    assert "Daemon already running" in stdout

    # Verify PID file didn't change (still pid1)
    assert int(pid_file.read_text()) == pid1

    # Cleanup
    try:
        os.kill(pid1, signal.SIGTERM)
    except:
        pass


def test_ttl_shutdown_cleans_files(clean_daemon_env):
    """Tripwire: Daemon shuts down after TTL and cleans up."""
    root = clean_daemon_env
    # Launch with short TTL
    import subprocess
    import sys

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
    lsp_dir = root / "_ctx" / "lsp" / seg_id
    pid_file = lsp_dir / PID_NAME
    sock_file = lsp_dir / SOCKET_NAME

    # Wait for startup
    started = False
    for _ in range(20):
        if pid_file.exists():
            started = True
            break
        time.sleep(0.1)
    assert started, "Daemon failed to start"

    # Wait for TTL (2s) + buffer
    time.sleep(3.5)

    # Verify files are gone
    assert not pid_file.exists(), "PID file should be removed after shutdown"
    assert not sock_file.exists(), "Socket file should be removed after shutdown"


def test_no_blocking_on_cold_start(clean_daemon_env):
    """Tripwire: Cold start returns immediately (doesn't wait for READY)."""
    root = clean_daemon_env
    client = LSPDaemonClient(root)

    t0 = time.time()
    spawned = client.connect_or_spawn()
    t1 = time.time()

    assert spawned is True
    # Should be fast (< 1s), definitely not waiting for LSP (~2s+)
    assert (t1 - t0) < 1.0

    # Ensure process is actually running
    seg_id = compute_segment_id(root)
    lsp_dir = root / "_ctx" / "lsp" / seg_id
    pid_file = lsp_dir / PID_NAME
    # Wait briefly for PID to prove it spawned
    for _ in range(20):
        if pid_file.exists():
            break
        time.sleep(0.1)
    assert pid_file.exists()

    # Cleanup
    import os
    import signal

    try:
        os.kill(int(pid_file.read_text()), signal.SIGTERM)
    except:
        pass


@pytest.fixture
def clean_daemon_env(tmp_path):
    """Provide an isolated root for daemon testing."""
    # Create marker to ensure resolve_segment_root stops here
    (tmp_path / "pyproject.toml").touch()
    return tmp_path


def test_daemon_spawn_and_connect(clean_daemon_env):
    root = clean_daemon_env
    client = LSPDaemonClient(root)

    # 1. Connect should fail initially (fresh root)
    assert client._try_connect() is False

    # 2. Spawn
    spawned = client.connect_or_spawn()
    assert spawned is True

    # 3. Wait for daemon to write PID/Socket (Async start)
    # Re-compute segment ID based on THIS root
    seg_id = compute_segment_id(root)
    lsp_dir = root / "_ctx" / "lsp" / seg_id
    pid_file = lsp_dir / PID_NAME
    sock_file = lsp_dir / SOCKET_NAME

    max_retries = 50
    for _ in range(max_retries):
        if pid_file.exists() and sock_file.exists():
            break
        time.sleep(0.1)

    assert pid_file.exists(), "PID file not created"
    assert sock_file.exists(), "Socket file not created"

    # 4. Connect should succeed now
    assert client._try_connect() is True

    # 5. Check Status
    status = client.send({"method": "status"})
    assert status["status"] == "ok"
    assert "state" in status["data"]

    # Cleanup
    import os
    import signal

    try:
        pid = int(pid_file.read_text())
        os.kill(pid, signal.SIGTERM)
        # Wait for cleanup
        time.sleep(0.2)
    except:
        pass


def test_daemon_singleton_lock(clean_daemon_env):
    """Tripwire: Ensure only one daemon runs per segment."""
    root = clean_daemon_env

    # Start first daemon manually
    client1 = LSPDaemonClient(root)
    client1.connect_or_spawn()

    seg_id = compute_segment_id(root)
    pid_file = root / "_ctx" / "lsp" / seg_id / PID_NAME

    # Wait for start
    for _ in range(50):
        if pid_file.exists():
            break
        time.sleep(0.05)

    assert pid_file.exists()
    pid1 = int(pid_file.read_text())

    # Try to start second daemon manually (simulate race or duplicate logic)
    import subprocess
    import sys

    # Launch identical start command
    cmd = [sys.executable, "-m", "src.infrastructure.lsp_daemon", "start", "--root", str(root)]

    # This should exit immediately because lock is held by pid1
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = p.communicate(timeout=5)

    assert "Daemon already running" in stdout

    # Verify PID file didn't change (still pid1)
    if pid_file.exists():
        assert int(pid_file.read_text()) == pid1

    # Cleanup
    import os
    import signal

    try:
        os.kill(pid1, signal.SIGTERM)
    except:
        pass


def test_ttl_shutdown_cleans_files(clean_daemon_env):
    """Tripwire: Daemon shuts down after TTL and cleans up."""
    root = clean_daemon_env
    # Launch with short TTL
    import subprocess
    import sys

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
    lsp_dir = root / "_ctx" / "lsp" / seg_id
    pid_file = lsp_dir / PID_NAME
    sock_file = lsp_dir / SOCKET_NAME

    # Wait for startup
    started = False
    for _ in range(20):
        if pid_file.exists():
            started = True
            break
        time.sleep(0.1)
    assert started, "Daemon failed to start"

    # Wait for TTL (2s) + buffer
    time.sleep(3.5)

    # Verify files are gone
    assert not pid_file.exists(), "PID file should be removed after shutdown"
    assert not sock_file.exists(), "Socket file should be removed after shutdown"


def test_no_blocking_on_cold_start(clean_daemon_env):
    """Tripwire: Cold start returns immediately (doesn't wait for READY)."""
    root = clean_daemon_env
    client = LSPDaemonClient(root)

    t0 = time.time()
    spawned = client.connect_or_spawn()
    t1 = time.time()

    assert spawned is True
    # Should be fast (< 1s), definitely not waiting for LSP (~2s+)
    assert (t1 - t0) < 1.0

    # Verify it is running but maybe not ready yet
    # (We can't easily query status if it's WARMING because connect might fail if socket not bound yet?
    # Actually client.connect_or_spawn returns once Popen is called.
    # Socket binding happens async in that process.
    # So immediate check of is_ready() might return False (connection fail or status WARMING)

    # Ensure process is actually running
    seg_id = compute_segment_id(root)
    lsp_dir = root / "_ctx" / "lsp" / seg_id
    pid_file = lsp_dir / PID_NAME
    # Wait briefly for PID to prove it spawned
    for _ in range(20):
        if pid_file.exists():
            break
        time.sleep(0.1)
    assert pid_file.exists()

    # Cleanup
    import os
    import signal

    try:
        os.kill(int(pid_file.read_text()), signal.SIGTERM)
    except:
        pass
