import pytest
import tempfile
import shutil
from pathlib import Path
from src.platform.daemon_manager import DaemonManager, DaemonStatus


class TestDaemonManagerLifecycle:
    @pytest.fixture
    def temp_dir(self):
        tmp = Path(tempfile.mkdtemp())
        yield tmp
        shutil.rmtree(tmp)

    @pytest.fixture
    def manager(self, temp_dir):
        runtime_dir = temp_dir / "runtime"
        runtime_dir.mkdir(parents=True, exist_ok=True)
        return DaemonManager(runtime_dir)

    def test_initial_status_not_running(self, manager):
        status = manager.status()
        assert status.running is False
        assert status.pid is None
        assert status.socket_path is None

    def test_status_after_stop(self, manager):
        manager.stop()
        status = manager.status()
        assert status.running is False

    def test_restart_when_not_running(self, manager):
        result = manager.restart()
        assert isinstance(result, bool)

    def test_stop_idempotent(self, manager):
        result1 = manager.stop()
        assert result1 is True

        result2 = manager.stop()
        assert result2 is True


class TestDaemonManagerSecurity:
    @pytest.fixture
    def temp_dir(self):
        tmp = Path(tempfile.mkdtemp())
        yield tmp
        shutil.rmtree(tmp)

    def test_start_with_invalid_path(self):
        invalid_path = Path("/tmp/completely/invalid/path/that/explodes")
        manager = DaemonManager(invalid_path)
        result = manager.start()
        assert result is False

    def test_status_with_nonexistent_runtime(self):
        runtime_dir = Path("/tmp/nonexistent/runtime/xyz123")
        manager = DaemonManager(runtime_dir)
        status = manager.status()
        assert status.running is False


class TestDaemonStatus:
    def test_daemon_status_dataclass(self):
        status = DaemonStatus(running=False, pid=None, socket_path=None)
        assert status.running is False
        assert status.pid is None

    def test_daemon_status_with_pid(self, tmp_path):
        socket_path = tmp_path / "socket"
        status = DaemonStatus(running=True, pid=12345, socket_path=socket_path)
        assert status.running is True
        assert status.pid == 12345
        assert status.socket_path == socket_path
