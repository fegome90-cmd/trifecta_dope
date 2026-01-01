import pytest
import time
import shutil
import json
from pathlib import Path
from src.infrastructure.lsp_daemon import LSPDaemonClient, LSPDaemonServer, SOCKET_NAME, PID_NAME


@pytest.fixture
def clean_daemon_env():
    root = Path.cwd()
    lsp_dir = root / "_ctx" / "lsp" / "restored_seg"
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
    lsp_dir = root / "_ctx" / "lsp" / "restored_seg"
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

    # 6. Check Telemetry Event (daemon_spawn missing in this quick test,
    # but we can verify lsp.spawn happens via daemon LOGS if we redirected them,
    # or by checking events.jsonl which daemon writes to)

    # Wait a bit for daemon telemetry flush? Daemon flushes on exit or events?
    # Telemetry appends immediately to events.jsonl

    events_file = root / "_ctx" / "telemetry" / "events.jsonl"
    # We might need to wait for daemon to actually initialize LSPClient and log spawn
    time.sleep(1)  # Allow daemon thread to run

    if events_file.exists():
        lines = events_file.read_text().splitlines()
        # Look for lsp.spawn from daemon (check pid matches daemon pid or child)
        damon_pid = int(pid_file.read_text())

        spawn_events = [json.loads(l) for l in lines if json.loads(l)["cmd"] == "lsp.spawn"]
        assert len(spawn_events) > 0
        # Check one of them corresponds to our daemon usage

    # Cleanup (Kill daemon)
    import os
    import signal

    try:
        os.kill(int(pid_file.read_text()), signal.SIGTERM)
    except:
        pass
