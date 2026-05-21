from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import src.platform.daemon_manager as daemon_manager_module
from src.platform.daemon_manager import DaemonManager, DaemonStatus, is_runtime_dir_allowed


def _clean_stale_files(manager: DaemonManager) -> None:
    """Remove stale socket/lock files from previous daemon runs."""
    for stale_path in [manager._socket_path, manager._lock_path]:
        if stale_path.exists():
            try:
                stale_path.unlink()
            except OSError:
                pass


class TestDaemonManagerLifecycle:
    @pytest.fixture
    def temp_dir(self) -> Path:
        tmp = Path(tempfile.mkdtemp())
        yield tmp
        shutil.rmtree(tmp)

    @pytest.fixture
    def manager(self, temp_dir: Path) -> DaemonManager:
        runtime_dir = temp_dir / "runtime"
        runtime_dir.mkdir(parents=True, exist_ok=True)
        m = DaemonManager(runtime_dir)
        _clean_stale_files(m)
        return m

    def test_initial_status_not_running(self, manager: DaemonManager) -> None:
        status = manager.status()
        assert status.running is False
        assert status.pid is None
        assert status.socket_path is None

    def test_status_after_stop(self, manager: DaemonManager) -> None:
        manager.stop()
        status = manager.status()
        assert status.running is False

    def test_restart_when_not_running(self, manager: DaemonManager) -> None:
        result = manager.restart()
        # restart() returns tuple[bool, Optional[str]] — either (True, None) or (False, msg)
        assert isinstance(result, tuple)
        assert isinstance(result[0], bool)

    def test_stop_idempotent(self, manager: DaemonManager) -> None:
        result1 = manager.stop()
        assert result1 is True

        result2 = manager.stop()
        assert result2 is True


class TestDaemonManagerSecurity:
    def test_runtime_dir_guard_accepts_descendant_of_allowed_base(self, tmp_path: Path) -> None:
        allowed_base = tmp_path / "trifecta"
        runtime_dir = allowed_base / "repos" / "safe-segment" / "runtime"

        assert is_runtime_dir_allowed(runtime_dir, [allowed_base]) is True

    def test_runtime_dir_guard_rejects_prefixed_sibling_path(self, tmp_path: Path) -> None:
        allowed_base = tmp_path / "trifecta"
        runtime_dir = Path(str(allowed_base) + "-evil/runtime")

        assert is_runtime_dir_allowed(runtime_dir, [allowed_base]) is False

    def test_start_rejects_prefixed_sibling_path_before_creating_dirs(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        allowed_base = tmp_path / "trifecta"
        runtime_dir = Path(str(allowed_base) + "-evil/runtime")
        manager = DaemonManager(runtime_dir)

        monkeypatch.setattr(daemon_manager_module, "ALLOWED_BASES", [allowed_base])

        started, msg = manager.start()

        assert started is False
        assert runtime_dir.exists() is False

    def test_start_with_invalid_path(self) -> None:
        invalid_path = Path("/tmp/completely/invalid/path/that/explodes")
        manager = DaemonManager(invalid_path)
        started, msg = manager.start()
        assert started is False

    def test_status_with_nonexistent_runtime(self) -> None:
        runtime_dir = Path("/tmp/nonexistent/runtime/xyz123")
        manager = DaemonManager(runtime_dir)
        status = manager.status()
        assert status.running is False


class TestDaemonStatus:
    def test_daemon_status_dataclass(self) -> None:
        status = DaemonStatus(running=False, pid=None, socket_path=None)
        assert status.running is False
        assert status.pid is None

    def test_daemon_status_with_pid(self, tmp_path: Path) -> None:
        socket_path = tmp_path / "socket"
        status = DaemonStatus(running=True, pid=12345, socket_path=socket_path)
        assert status.running is True
        assert status.pid == 12345
        assert status.socket_path == socket_path


@pytest.mark.parametrize(
    ("env_value", "expected"),
    [(None, "30"), ("45", "45"), ("2.5", "2.5"), ("invalid", "30")],
)
def test_start_exports_lsp_timeout_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    env_value: str | None,
    expected: str,
) -> None:
    allowed_base = tmp_path / "trifecta"
    runtime_dir = allowed_base / "repos" / "safe-segment" / "runtime"
    manager = DaemonManager(runtime_dir)
    _clean_stale_files(manager)
    manager._runtime_dir.mkdir(parents=True, exist_ok=True)
    manager._socket_path.parent.mkdir(parents=True, exist_ok=True)

    # Create a real AF_UNIX socket so start() sees it as a valid socket
    import socket as _socket

    sock = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
    try:
        sock.bind(str(manager._socket_path))
    except OSError:
        pass

    monkeypatch.setattr(daemon_manager_module, "ALLOWED_BASES", [allowed_base])

    if env_value is None:
        monkeypatch.delenv("TRIFECTA_LSP_REQUEST_TIMEOUT", raising=False)
    else:
        monkeypatch.setenv("TRIFECTA_LSP_REQUEST_TIMEOUT", env_value)

    captured_env: dict[str, str] = {}

    def fake_popen(*args: Any, **kwargs: Any) -> SimpleNamespace:
        del args
        captured_env.update(kwargs["env"])
        return SimpleNamespace(pid=9876, poll=lambda: None)

    monkeypatch.setattr(daemon_manager_module.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(daemon_manager_module.time, "sleep", lambda _value: None)

    started, msg = manager.start()

    assert started is True
    assert captured_env["TRIFECTA_LSP_REQUEST_TIMEOUT"] == expected
    sock.close()
