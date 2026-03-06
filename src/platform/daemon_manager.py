import os
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class DaemonStatus:
    running: bool
    pid: Optional[int] = None
    socket_path: Optional[Path] = None


class DaemonManager:
    DAEMON_TTL_IDLE = 300
    DAEMON_START_TIMEOUT = 5

    def __init__(self, runtime_dir: Path) -> None:
        self._runtime_dir = runtime_dir
        self._socket_path = runtime_dir / "daemon" / "socket"
        self._pid_path = runtime_dir / "daemon" / "pid"
        self._log_path = runtime_dir / "daemon" / "log"

    def start(self) -> bool:
        if self.is_running():
            return True
        self._runtime_dir.mkdir(parents=True, exist_ok=True)
        self._socket_path.parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.Popen(
            ["python", "-m", "trifecta", "daemon", "run"],
            cwd=self._runtime_dir,
            stdout=open(self._log_path, "a"),
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        for _ in range(self.DAEMON_START_TIMEOUT * 10):
            if self._socket_path.exists():
                self._pid_path.write_text(str(proc.pid))
                return True
            time.sleep(0.1)
        return False

    def stop(self) -> bool:
        if not self.is_running():
            return True
        try:
            pid = int(self._pid_path.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            for _ in range(50):
                if not self.is_running():
                    return True
                time.sleep(0.1)
            os.kill(pid, signal.SIGKILL)
            return True
        except (FileNotFoundError, ProcessLookupError, ValueError):
            return True
        finally:
            self._cleanup_files()

    def restart(self) -> bool:
        self.stop()
        return self.start()

    def status(self) -> DaemonStatus:
        pid = None
        if self._pid_path.exists():
            try:
                pid = int(self._pid_path.read_text().strip())
                os.kill(pid, 0)
            except (ProcessLookupError, ValueError):
                pid = None
        running = pid is not None and self._socket_path.exists()
        return DaemonStatus(
            running=running,
            pid=pid,
            socket_path=self._socket_path if running else None,
        )

    def is_running(self) -> bool:
        return self.status().running

    def _cleanup_files(self) -> None:
        for p in [self._pid_path, self._socket_path]:
            try:
                p.unlink()
            except FileNotFoundError:
                pass
