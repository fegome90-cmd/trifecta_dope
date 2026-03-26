import os
import shutil
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import src.platform.daemon_manager as daemon_manager_module
from src.platform.daemon_manager import DaemonManager


@pytest.fixture
def allowed_runtime(monkeypatch: pytest.MonkeyPatch) -> Path:
    allowed_base = Path(tempfile.mkdtemp(prefix="tf-daemon-", dir="/tmp"))
    runtime_dir = allowed_base / "repos" / "safe-segment" / "runtime"
    monkeypatch.setattr(daemon_manager_module, "ALLOWED_BASES", [allowed_base])
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

    assert manager.start() is False


def test_acquire_singleton_lock_recovers_stale_lock_file(
    allowed_runtime: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = DaemonManager(allowed_runtime)
    manager._socket_path.parent.mkdir(parents=True, exist_ok=True)
    stale_lock_path = Path(str(manager._socket_path) + ".lock")
    stale_lock_path.write_text("stale")
    old_mtime = daemon_manager_module.time.time() - (manager.DAEMON_START_TIMEOUT + 1)
    os.utime(stale_lock_path, (old_mtime, old_mtime))
    monkeypatch.setattr(manager, "is_running", lambda: False)

    acquired = manager._acquire_singleton_lock()

    assert acquired is True
    assert stale_lock_path.exists() is True
    manager._release_singleton_lock()
    assert stale_lock_path.exists() is False


def test_acquire_singleton_lock_keeps_recent_lock_for_startup_in_progress(
    allowed_runtime: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = DaemonManager(allowed_runtime)
    manager._socket_path.parent.mkdir(parents=True, exist_ok=True)
    recent_lock_path = Path(str(manager._socket_path) + ".lock")
    recent_lock_path.write_text("recent")
    monkeypatch.setattr(manager, "is_running", lambda: False)

    acquired = manager._acquire_singleton_lock()

    assert acquired is False
    assert recent_lock_path.exists() is True


def test_start_releases_singleton_lock_after_success(
    allowed_runtime: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = DaemonManager(allowed_runtime)
    manager._runtime_dir.mkdir(parents=True, exist_ok=True)
    manager._socket_path.parent.mkdir(parents=True, exist_ok=True)
    sleep_calls = {"count": 0}

    def fake_sleep(_value: float) -> None:
        sleep_calls["count"] += 1
        if sleep_calls["count"] == 1:
            manager._socket_path.write_text("")

    monkeypatch.setattr(
        daemon_manager_module.subprocess,
        "Popen",
        lambda *args, **kwargs: SimpleNamespace(pid=4321, poll=lambda: None),
    )
    monkeypatch.setattr(daemon_manager_module.time, "sleep", fake_sleep)

    started = manager.start()

    assert started is True
    assert manager._pid_path.read_text() == "4321"
    assert Path(str(manager._socket_path) + ".lock").exists() is False


def test_start_closes_log_handle_after_spawn(
    allowed_runtime: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = DaemonManager(allowed_runtime)
    captured: dict[str, object] = {}

    class FakeProcess:
        pid = 4321

        @staticmethod
        def poll() -> None:
            return None

    def fake_popen(*_args: object, **kwargs: object) -> FakeProcess:
        captured["stdout"] = kwargs["stdout"]
        return FakeProcess()

    manager._runtime_dir.mkdir(parents=True, exist_ok=True)
    manager._socket_path.parent.mkdir(parents=True, exist_ok=True)
    sleep_calls = {"count": 0}

    def fake_sleep(_value: float) -> None:
        sleep_calls["count"] += 1
        if sleep_calls["count"] == 1:
            manager._socket_path.write_text("")

    monkeypatch.setattr(daemon_manager_module.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(daemon_manager_module.time, "sleep", fake_sleep)

    assert manager.start() is True
    assert manager._pid_path.read_text() == "4321"
    assert captured["stdout"].closed is True


def test_start_does_not_write_pid_when_child_exits_before_ready(
    allowed_runtime: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = DaemonManager(allowed_runtime)
    manager._runtime_dir.mkdir(parents=True, exist_ok=True)
    manager._socket_path.parent.mkdir(parents=True, exist_ok=True)
    manager._socket_path.write_text("")

    class DeadProcess:
        pid = 9999

        @staticmethod
        def poll() -> int:
            return 17

    monkeypatch.setattr(daemon_manager_module.subprocess, "Popen", lambda *args, **kwargs: DeadProcess())
    monkeypatch.setattr(daemon_manager_module.time, "sleep", lambda _value: None)

    assert manager.start() is False
    assert manager._pid_path.exists() is False


def test_start_ignores_stale_socket_until_new_socket_appears(
    allowed_runtime: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = DaemonManager(allowed_runtime)
    manager._runtime_dir.mkdir(parents=True, exist_ok=True)
    manager._socket_path.parent.mkdir(parents=True, exist_ok=True)
    manager._socket_path.write_text("stale")

    class LiveProcess:
        pid = 4321

        @staticmethod
        def poll() -> None:
            return None

    sleep_calls = {"count": 0}

    def fake_sleep(_value: float) -> None:
        sleep_calls["count"] += 1
        if sleep_calls["count"] == 1:
            manager._socket_path.write_text("")

    monkeypatch.setattr(daemon_manager_module.subprocess, "Popen", lambda *args, **kwargs: LiveProcess())
    monkeypatch.setattr(daemon_manager_module.time, "sleep", fake_sleep)

    assert manager.start() is True
    assert sleep_calls["count"] == 1
    assert manager._pid_path.read_text() == "4321"




def test_start_terminates_child_and_cleans_pid_on_timeout(
    allowed_runtime: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = DaemonManager(allowed_runtime)
    manager._runtime_dir.mkdir(parents=True, exist_ok=True)
    manager._socket_path.parent.mkdir(parents=True, exist_ok=True)

    class HungProcess:
        pid = 2468

        def __init__(self) -> None:
            self.terminated = False
            self.killed = False

        def poll(self) -> None:
            return None

        def terminate(self) -> None:
            self.terminated = True

        def wait(self, timeout: float | None = None) -> None:
            raise daemon_manager_module.subprocess.TimeoutExpired(cmd='daemon', timeout=timeout or 0)

        def kill(self) -> None:
            self.killed = True

    proc = HungProcess()
    monkeypatch.setattr(daemon_manager_module.subprocess, 'Popen', lambda *args, **kwargs: proc)
    monkeypatch.setattr(daemon_manager_module.time, 'sleep', lambda _value: None)

    assert manager.start() is False
    assert proc.terminated is True
    assert proc.killed is True
    assert manager._pid_path.exists() is False


def test_restart_returns_false_when_stop_fails(
    allowed_runtime: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = DaemonManager(allowed_runtime)
    start = Mock(return_value=True)
    monkeypatch.setattr(manager, 'stop', lambda: False)
    monkeypatch.setattr(manager, 'start', start)

    assert manager.restart() is False
    start.assert_not_called()

def test_stop_keeps_pid_and_socket_when_process_survives_kill(
    allowed_runtime: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = DaemonManager(allowed_runtime)
    manager._pid_path.parent.mkdir(parents=True, exist_ok=True)
    manager._pid_path.write_text("4321")
    manager._socket_path.write_text("")

    cleanup = Mock()
    monkeypatch.setattr(manager, "_cleanup_files", cleanup)
    monkeypatch.setattr(daemon_manager_module.os, "kill", lambda _pid, _sig: None)
    monkeypatch.setattr(daemon_manager_module.time, "sleep", lambda _value: None)

    calls = iter([True] * 62)
    monkeypatch.setattr(manager, "is_running", lambda: next(calls))

    assert manager.stop() is False
    cleanup.assert_not_called()


def test_stop_does_not_treat_proxy_not_running_as_real_exit(
    allowed_runtime: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = DaemonManager(allowed_runtime)
    manager._pid_path.parent.mkdir(parents=True, exist_ok=True)
    manager._pid_path.write_text("4321")
    manager._socket_path.write_text("")

    cleanup = Mock()
    signals: list[int] = []
    monkeypatch.setattr(manager, "_cleanup_files", cleanup)
    monkeypatch.setattr(manager, "is_running", lambda: False)
    monkeypatch.setattr(manager, "_is_process_alive", lambda _pid: True)
    monkeypatch.setattr(daemon_manager_module.os, "kill", lambda _pid, sig: signals.append(sig))
    monkeypatch.setattr(daemon_manager_module.time, "sleep", lambda _value: None)

    assert manager.stop() is False
    assert signals == [daemon_manager_module.signal.SIGTERM, daemon_manager_module.signal.SIGKILL]
    cleanup.assert_not_called()


def test_stop_cleans_files_once_process_is_gone(
    allowed_runtime: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = DaemonManager(allowed_runtime)
    manager._pid_path.parent.mkdir(parents=True, exist_ok=True)
    manager._pid_path.write_text("4321")

    cleanup = Mock()
    monkeypatch.setattr(manager, "_cleanup_files", cleanup)

    def fake_kill(_pid: int, sig: int) -> None:
        if sig == 0:
            raise ProcessLookupError

    monkeypatch.setattr(daemon_manager_module.os, "kill", fake_kill)
    monkeypatch.setattr(daemon_manager_module.time, "sleep", lambda _value: None)

    calls = iter([True, False])
    monkeypatch.setattr(manager, "is_running", lambda: next(calls))

    assert manager.stop() is True
    cleanup.assert_called_once_with()


def test_stop_retries_post_sigkill_until_process_is_gone(
    allowed_runtime: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = DaemonManager(allowed_runtime)
    manager._pid_path.parent.mkdir(parents=True, exist_ok=True)
    manager._pid_path.write_text("4321")
    manager._socket_path.write_text("")

    cleanup = Mock()
    monkeypatch.setattr(manager, "_cleanup_files", cleanup)
    monkeypatch.setattr(daemon_manager_module.os, "kill", lambda _pid, _sig: None)
    monkeypatch.setattr(daemon_manager_module.time, "sleep", lambda _value: None)
    monkeypatch.setattr(manager, "is_running", lambda: True)
    liveness = iter([True] * 50 + [True, False, False])
    monkeypatch.setattr(manager, "_is_process_alive", lambda _pid: next(liveness))

    assert manager.stop() is True
    cleanup.assert_called_once_with()
