"""Platform runtime manager - skeleton only (no implementation).

This module defines the interface for runtime management.
Implementation will be added in future WOs.
"""

from pathlib import Path
from typing import Protocol


class RuntimeManager(Protocol):
    """Protocol defining runtime management interface."""

    def ensure_initialized(self, repo_id: str) -> Path:
        """Ensure runtime is initialized for repo."""
        ...

    def get_runtime_dir(self, repo_id: str) -> Path:
        """Get runtime directory for repo."""
        ...

    def is_initialized(self, repo_id: str) -> bool:
        """Check if runtime is initialized."""
        ...

    def cleanup(self, repo_id: str) -> None:
        """Cleanup runtime resources."""
        ...


class DaemonManager(Protocol):
    """Protocol defining daemon management interface."""

    def start(self, repo_id: str) -> bool:
        """Start daemon for repo."""
        ...

    def stop(self, repo_id: str) -> bool:
        """Stop daemon for repo."""
        ...

    def status(self, repo_id: str) -> dict[str, Any]:
        """Get daemon status."""
        ...

    def restart(self, repo_id: str) -> bool:
        """Restart daemon for repo."""
        ...


class HealthChecker(Protocol):
    """Protocol defining health check interface."""

    def check(self, repo_id: str) -> dict[str, Any]:
        """Perform health check."""
        ...
