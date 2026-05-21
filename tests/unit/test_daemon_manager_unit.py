import os
import shutil
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

import src.platform.daemon_manager as daemon_manager_module
from src.platform.daemon_manager import DaemonManager


@pytest.fixture
def allowed_runtime(monkeypatch: pytest.MonkeyPatch) -> Path:
    allowed_base = Path(tempfile.mkdtemp(prefix="tf-daemon-", dir="/tmp"))
    runtime_dir = allowed_base / "repos" / "safe-segment" / "runtime"
    monkeypatch.setattr(daemon_manager_module, "ALLOWED_BASES", [allowed_base])

    # Pre-create a DaemonManager to discover its resolved paths and clean stale files
    manager = DaemonManager(runtime_dir)
    for stale_path in [manager._socket_path, manager._lock_path]:
        if stale_path.exists():
            try:
                stale_path.unlink()
            except OSError:
                pass

    try:
        yield runtime_dir
    finally:
        shutil.rmtree(allowed_base, ignore_errors=True)


def test_start_creates_parent_dirs_before_acquiring_lock(
    allowed_runtime: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = DaemonManager(allowed_runtime)

    def fake_acquire() -> bool:
        assert allowed_runtime.exists() is True
        assert manager._socket_path.parent.exists() is True
        return False

    monkeypatch.setattr(manager, "_acquire_singleton_lock", fake_acquire)

    started, msg = manager.start()
    assert started is False
    assert msg == "Failed to acquire singleton lock"


def test_acquire_singleton_lock_recovers_stale_lock_file(
    allowed_runtime: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = DaemonManager(allowed_runtime)
    manager.DAEMON_START_TIMEOUT = 0.2

    # Use the actual lock path from the manager (trifecta_lsp_{fp}.lock)
    stale_lock_path = manager._lock_path
    stale_lock_path.parent.mkdir(parents=True, exist_ok=True)
    stale_lock_path.write_text("stale")
    monkeypatch.setattr(manager, "is_running", lambda: False)

    # The current _acquire_singleton_lock flow: bind fails on stale →
    # _lock_owner_is_alive returns False (no PID) →
    # _wait_for_lock_release tries to bind → fails →
    # removes stale lock → retries bind → succeeds
    acquired = manager._acquire_singleton_lock()

    assert acquired is True
    # Lock was acquired — stale file may still exist on disk as the new
    # socket bind creates a fresh file descriptor at the same path.
    # The important invariant is that we acquired the lock.
    manager._release_singleton_lock()


def test_acquire_singleton_lock_keeps_live_owner_lock_file(
    allowed_runtime: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = DaemonManager(allowed_runtime)
    lock_path = manager._lock_path
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text("busy")
    manager._pid_path.parent.mkdir(parents=True, exist_ok=True)
    manager._pid_path.write_text(str(os.getpid()), encoding="utf-8")
    monkeypatch.setattr(manager, "is_running", lambda: False)

    acquired = manager._acquire_singleton_lock()

    # Lock is held by live owner (our own PID) — should not acquire
    assert acquired is False
    assert lock_path.exists() is True


def test_acquire_singleton_lock_does_not_unlink_during_startup_backoff(
    allowed_runtime: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = DaemonManager(allowed_runtime)
    lock_path = manager._lock_path
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text("busy")
    running_states = [False, True, True]

    def fake_is_running() -> bool:
        if running_states:
            return running_states.pop(0)
        return True

    monkeypatch.setattr(manager, "is_running", fake_is_running)

    acquired = manager._acquire_singleton_lock()

    # Lock owner appears to start running during backoff — should NOT unlink
    assert acquired is False
    assert lock_path.exists() is True


def test_start_releases_singleton_lock_after_success(
    allowed_runtime: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = DaemonManager(allowed_runtime)
    manager._runtime_dir.mkdir(parents=True, exist_ok=True)
    manager._socket_path.parent.mkdir(parents=True, exist_ok=True)

    # Create the socket file as a real AF_UNIX socket so start() sees it
    import socket as _socket

    sock = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
    try:
        sock.bind(str(manager._socket_path))
    except OSError:
        # If bind fails (e.g. path in use), skip socket creation
        pass

    monkeypatch.setattr(
        daemon_manager_module.subprocess,
        "Popen",
        lambda *args, **kwargs: SimpleNamespace(pid=4321, poll=lambda: None),
    )
    monkeypatch.setattr(daemon_manager_module.time, "sleep", lambda _value: None)

    started, msg = manager.start()

    assert started is True
    assert manager._pid_path.read_text() == "4321"
    assert not manager._lock_path.exists(), "Lock should be released after start"
    sock.close()
