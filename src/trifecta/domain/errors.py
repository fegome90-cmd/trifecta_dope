"""
Platform Error Definitions.

Base error classes and specific exceptions for platform operations.

Author: Trifecta Team
Date: 2026-03-06
"""

from __future__ import annotations


class PlatformError(Exception):
    """Base exception for all platform-related errors."""

    def __init__(self, message: str, **kwargs: object) -> None:
        super().__init__(message)
        self.context = kwargs


class RepoNotFoundError(PlatformError):
    """Raised when a repository cannot be found."""

    def __init__(self, repo_path: str | None = None, repo_id: str | None = None) -> None:
        if repo_path:
            message = f"Repository not found at path: {repo_path}"
        elif repo_id:
            message = f"Repository not found with id: {repo_id}"
        else:
            message = "Repository not found"
        super().__init__(message, repo_path=repo_path, repo_id=repo_id)
        self.repo_path = repo_path
        self.repo_id = repo_id


class SegmentNotFoundError(PlatformError):
    """Raised when a segment cannot be found."""

    def __init__(
        self,
        segment_path: str | None = None,
        segment_id: str | None = None,
    ) -> None:
        if segment_path:
            message = f"Segment not found at path: {segment_path}"
        elif segment_id:
            message = f"Segment not found with id: {segment_id}"
        else:
            message = "Segment not found"
        super().__init__(message, segment_path=segment_path, segment_id=segment_id)
        self.segment_path = segment_path
        self.segment_id = segment_id


class RegistryError(PlatformError):
    """Raised when a registry operation fails."""

    def __init__(self, message: str, operation: str | None = None) -> None:
        super().__init__(message, operation=operation)
        self.operation = operation


class DaemonError(PlatformError):
    """Raised when a daemon operation fails."""

    def __init__(
        self,
        message: str,
        daemon_id: str | None = None,
        operation: str | None = None,
    ) -> None:
        super().__init__(message, daemon_id=daemon_id, operation=operation)
        self.daemon_id = daemon_id
        self.operation = operation


class ConfigurationError(PlatformError):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str, config_key: str | None = None) -> None:
        super().__init__(message, config_key=config_key)
        self.config_key = config_key
