"""
Registry Protocol - Abstract interface for repository registry.

This module defines the protocol (interface) for registry operations.
Implementation (repo_store.py) comes in WO-0043.

Author: Trifecta Team
Date: 2026-03-06
"""

from abc import abstractmethod
from pathlib import Path
from typing import Any, Protocol


class Registry(Protocol):
    """
    Protocol for repository registry operations.

    All registry implementations must implement this interface.
    """

    @abstractmethod
    def register(self, repo_root: Path, metadata: dict[str, Any]) -> None:
        """Register a repository in the registry."""
        ...

    @abstractmethod
    def unregister(self, repo_id: str) -> None:
        """Remove a repository from the registry."""
        ...

    @abstractmethod
    def get(self, repo_id: str) -> dict[str, Any] | None:
        """Get repository metadata by ID."""
        ...

    @abstractmethod
    def list_all(self) -> list[dict[str, Any]]:
        """List all registered repositories."""
        ...

    @abstractmethod
    def update(self, repo_id: str, metadata: dict[str, Any]) -> None:
        """Update repository metadata."""
        ...


class RegistryFactory:
    """Factory for creating registry instances."""

    @staticmethod
    def create(registry_type: str = "sqlite", **kwargs: Any) -> Registry:
        """
        Create a registry instance.

        Args:
            registry_type: Type of registry ("sqlite", "memory")
            **kwargs: Additional configuration

        Returns:
            Registry implementation instance
        """
        if registry_type == "memory":
            from trifecta.platform.memory_registry import MemoryRegistry

            return MemoryRegistry(**kwargs)
        elif registry_type == "sqlite":
            from trifecta.platform.repo_store import SQLiteRegistry

            return SQLiteRegistry(**kwargs)
        else:
            raise ValueError(f"Unknown registry type: {registry_type}")
