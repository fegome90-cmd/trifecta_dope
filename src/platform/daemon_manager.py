import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class DaemonStatus:
    running: bool
    pid: Optional[int] = None
    socket_path: Optional[Path] = None


ALLOWED_BASES = [
    Path("~/.local/share/trifecta").expanduser().resolve(),
    Path("~/.config/trifecta").expanduser().resolve(),
    Path("~/.cache/trifecta").expanduser().resolve(),
]


def is_runtime_dir_allowed(path: Path, allowed_bases: Optional[list[Path]] = None) -> bool:
    try:
        resolved = path.resolve()
        bases = ALLOWED_BASES if allowed_bases is None else allowed_bases
        return any(resolved.is_relative_to(base.resolve()) for base in bases)
    except Exception:
        return False


def _is_path_safe(path: Path) -> bool:
    return is_runtime_dir_allowed(path, ALLOWED_BASES)


class DaemonManager:
    DAEMON_TTL_IDLE = 300
    DAEMON_START_TIMEOUT = 5

    def __init__(self, runtime_dir: Path, repo_root: Optional[Path] = None) -> None:
        self._runtime_dir = runtime_dir
        self._repo_root = repo_root if repo_root is not None else runtime_dir
        self._socket_path = runtime_dir / "daemon" / "socket"
        self._pid_path = runtime_dir / "daemon" / "pid"
        self._log_path = runtime_dir / "daemon" / "log"

    def start(self) -> bool:
        """Start daemon. Returns True if daemon is running after call.

        Note: Returns True both if daemon was already running and if
        it was just started. Use is_running() before start() to distinguish.
        """
        if self.is_running():
            return True
        if not _is_path_safe(self._runtime_dir):
            return False

        self._runtime_dir.mkdir(parents=True, exist_ok=True)
        self._socket_path.parent.mkdir(parents=True, exist_ok=True)

        # Fase 4: singleton lock to prevent concurrent starts
        if not self._acquire_singleton_lock():
            return False

        log_file = self._log_path.open("a")
        python_exe = sys.executable
        import src.infrastructure.cli as cli_module

        cli_path = Path(cli_module.__file__)
        env = os.environ.copy()
        env["TRIFECTA_RUNTIME_DIR"] = str(self._runtime_dir)
        env["TRIFECTA_REPO_ROOT"] = str(self._repo_root.resolve())
        # Pass TTL if configured (Fase 4 hardening)
        if self.DAEMON_TTL_IDLE > 0:
            env["TRIFECTA_DAEMON_TTL"] = str(self.DAEMON_TTL_IDLE)
        proc = subprocess.Popen(
            [python_exe, str(cli_path), "daemon", "run"],
            cwd=str(self._runtime_dir),
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            env=env,
        )
        try:
            for _ in range(self.DAEMON_START_TIMEOUT * 10):
                if self._socket_path.exists():
                    self._pid_path.write_text(str(proc.pid))
                    return True
                time.sleep(0.1)
            return False
        finally:
            self._release_singleton_lock()

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
            time.sleep(0.1)
            return not self.is_running()
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
            except (ProcessLookupError, PermissionError, ValueError):
                pid = None
        running = pid is not None and self._socket_path.exists()
        return DaemonStatus(
            running=running,
            pid=pid,
            socket_path=self._socket_path if running else None,
        )

    def is_running(self) -> bool:
        return self.status().running

    def _acquire_singleton_lock(self) -> bool:
        """Acquire exclusive lock to prevent concurrent daemon starts.

        Uses socket bind as atomic singleton check. If bind fails,
        another instance is already running, or a stale lock path exists.

        Returns:
            True if lock acquired, False if another instance holds it.
        """
        import socket as _socket

        lock_path = Path(str(self._socket_path) + ".lock")

        def _bind_lock() -> _socket.socket:
            lock_socket = _socket.socket(_socket.AF_UNIX, _socket.SOCK_DGRAM)
            lock_socket.bind(str(lock_path))
            return lock_socket

        try:
            self._singleton_lock = _bind_lock()
            return True
        except OSError:
            if lock_path.exists() and not self.is_running():
                try:
                    lock_path.unlink()
                    self._singleton_lock = _bind_lock()
                    return True
                except OSError:
                    pass
            return False

    def _release_singleton_lock(self) -> None:
        """Release singleton lock."""
        if hasattr(self, "_singleton_lock") and self._singleton_lock:
            try:
                self._singleton_lock.close()
            except Exception:
                pass
            lock_path = str(self._socket_path) + ".lock"
            try:
                Path(lock_path).unlink()
            except FileNotFoundError:
                pass

    def _cleanup_files(self) -> None:
        for p in [self._pid_path, self._socket_path]:
            try:
                p.unlink()
            except FileNotFoundError:
                pass
