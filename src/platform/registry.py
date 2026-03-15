"""Platform registry - contract only (no implementation).

This module defines the interface for the repository registry.
Implementation lives in repo_store.py (WO-0043).
"""

from pathlib import Path
from typing import Protocol


class RepoRecord:
    """Immutable record of a registered repository."""

    _repo_id: str
    _root_path: Path
    _created_at: str
    _last_accessed: str | None
    __slots__ = ("_repo_id", "_root_path", "_created_at", "_last_accessed")

    def __init__(
        self, repo_id: str, root_path: Path, created_at: str, last_accessed: str | None = None
    ):
        object.__setattr__(self, "_repo_id", repo_id)
        object.__setattr__(self, "_root_path", root_path)
        object.__setattr__(self, "_created_at", created_at)
        object.__setattr__(self, "_last_accessed", last_accessed)

    @property
    def repo_id(self) -> str:
        return self._repo_id

    @property
    def root_path(self) -> Path:
        return self._root_path

    @property
    def created_at(self) -> str:
        return self._created_at

    @property
    def last_accessed(self) -> str | None:
        return self._last_accessed


class Registry(Protocol):
    """Protocol defining the registry interface."""

    def add(self, repo_id: str, root_path: Path) -> RepoRecord:
        """Register a repository."""
        ...

    def get(self, repo_id: str) -> RepoRecord | None:
        """Get repository by ID."""
        ...

    def list_all(self) -> list[RepoRecord]:
        """List all registered repositories."""
        ...

    def delete(self, repo_id: str) -> bool:
        """Remove repository from registry."""
        ...
