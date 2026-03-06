from pathlib import Path

from src.platform.daemon_manager import DaemonManager
from src.platform.health import HealthChecker


class DaemonUseCase:
    def __init__(self, runtime_dir: Path) -> None:
        self._manager = DaemonManager(runtime_dir)
        self._health = HealthChecker(runtime_dir)

    def start(self) -> dict:
        ok = self._manager.start()
        return {"status": "ok" if ok else "error", "running": ok}

    def stop(self) -> dict:
        ok = self._manager.stop()
        return {"status": "ok", "running": not ok}

    def restart(self) -> dict:
        ok = self._manager.restart()
        return {"status": "ok" if ok else "error", "running": ok}

    def status(self) -> dict:
        status = self._manager.status()
        health = self._health.check()
        return {
            "status": "ok",
            "running": status.running,
            "pid": status.pid,
            "socket": str(status.socket_path) if status.socket_path else None,
            "health": {"healthy": health.healthy, "score": health.score},
        }
