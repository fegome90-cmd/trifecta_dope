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
    monkeypatch.setattr(manager, "is_running", lambda: False)

    acquired = manager._acquire_singleton_lock()

    assert acquired is True
    assert stale_lock_path.exists() is True
    manager._release_singleton_lock()
    assert stale_lock_path.exists() is False


def test_start_releases_singleton_lock_after_success(
    allowed_runtime: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = DaemonManager(allowed_runtime)
    manager._runtime_dir.mkdir(parents=True, exist_ok=True)
    manager._socket_path.parent.mkdir(parents=True, exist_ok=True)
    manager._socket_path.write_text("")

    monkeypatch.setattr(
        daemon_manager_module.subprocess,
        "Popen",
        lambda *args, **kwargs: SimpleNamespace(pid=4321),
    )
    monkeypatch.setattr(daemon_manager_module.time, "sleep", lambda _value: None)

    started = manager.start()

    assert started is True
    assert manager._pid_path.read_text() == "4321"
    assert Path(str(manager._socket_path) + ".lock").exists() is False
