"""
Runtime Manager - Orchestrator for platform runtime.

This module provides the skeleton interface for runtime management.
Implementation comes in WO-0043.

Author: Trifecta Team
Date: 2026-03-06
"""

from abc import ABC, abstractmethod
from typing import Any


class RuntimeManager(ABC):
    """
    Abstract runtime manager for platform operations.

    Manages: daemon lifecycle, health checks, recovery operations.
    """

    @abstractmethod
    def start(self, segment_id: str) -> None:
        """Start runtime for a segment."""
        ...

    @abstractmethod
    def stop(self, segment_id: str) -> None:
        """Stop runtime for a segment."""
        ...

    @abstractmethod
    def restart(self, segment_id: str) -> None:
        """Restart runtime for a segment."""
        ...

    @abstractmethod
    def status(self, segment_id: str) -> dict[str, Any]:
        """Get runtime status for a segment."""
        ...

    @abstractmethod
    def health_check(self, segment_id: str) -> bool:
        """Perform health check for a segment."""
        ...

    @abstractmethod
    def recover(self, segment_id: str) -> None:
        """Attempt to recover a failed runtime."""
        ...


class RuntimeManagerFactory:
    """Factory for creating runtime manager instances."""

    @staticmethod
    def create(manager_type: str = "daemon", **kwargs: Any) -> RuntimeManager:
        """
        Create a runtime manager instance.

        Args:
            manager_type: Type of manager ("daemon", "embedded")
            **kwargs: Additional configuration

        Returns:
            RuntimeManager implementation instance
        """
        if manager_type == "daemon":
            from trifecta.platform.daemon_runtime import DaemonRuntimeManager

            return DaemonRuntimeManager(**kwargs)
        elif manager_type == "embedded":
            from trifecta.platform.embedded_runtime import EmbeddedRuntimeManager

            return EmbeddedRuntimeManager(**kwargs)
        else:
            raise ValueError(f"Unknown manager type: {manager_type}")
