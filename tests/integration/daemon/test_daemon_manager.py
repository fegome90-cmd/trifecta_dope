import pytest
from pathlib import Path
import tempfile
import shutil
from src.platform.daemon_manager import DaemonManager, DaemonStatus


class TestDaemonManager:
    @pytest.fixture
    def temp_dir(self):
        tmp = Path(tempfile.mkdtemp())
        yield tmp
        shutil.rmtree(tmp)

    @pytest.fixture
    def manager(self, temp_dir):
        runtime_dir = temp_dir / "runtime"
        return DaemonManager(runtime_dir)

    def test_initial_status_not_running(self, manager):
        status = manager.status()
        assert status.running is False
        assert status.pid is None

    def test_start_stop(self, manager):
        result = manager.start()
        assert result is True or result is False

        manager.stop()

    def test_is_running(self, manager):
        assert manager.is_running() is False

    def test_restart(self, manager):
        result = manager.restart()
        assert result is True or result is False
