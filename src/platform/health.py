from dataclasses import dataclass
from pathlib import Path


@dataclass
class HealthResult:
    healthy: bool
    score: float
    checks: dict[str, bool]


class HealthChecker:
    def __init__(self, runtime_dir: Path) -> None:
        self._runtime_dir = runtime_dir

    def check(self) -> HealthResult:
        checks = {}
        checks["runtime_exists"] = self._runtime_dir.exists()
        checks["daemon_healthy"] = self._check_daemon()
        score = sum(checks.values()) / len(checks) * 100
        return HealthResult(healthy=all(checks.values()), score=score, checks=checks)

    def _check_daemon(self) -> bool:
        socket_path = self._runtime_dir / "daemon" / "socket"
        pid_path = self._runtime_dir / "daemon" / "pid"
        if not socket_path.exists() or not pid_path.exists():
            return False
        try:
            import os

            pid = int(pid_path.read_text().strip())
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, PermissionError, ValueError):
            return False
