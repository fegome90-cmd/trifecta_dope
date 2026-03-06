"""Platform-layer exceptions for Trifecta V1 runtime.

These exceptions handle errors related to:
- Repository registration and lookup
- Daemon lifecycle management
- Runtime state and health
"""

from pathlib import Path


class PlatformError(Exception):
    """Base exception for all platform-related errors."""

    pass


class RepoNotFoundError(PlatformError):
    """Raised when a requested repository is not found in the registry."""

    def __init__(self, repo_id: str, message: str | None = None):
        self.repo_id = repo_id
        if message is None:
            message = f"Repository not found: '{repo_id}'"
        super().__init__(message)


class SegmentNotFoundError(PlatformError):
    """Raised when a segment cannot be resolved from the given path."""

    def __init__(self, path: Path | str, message: str | None = None):
        self.path = Path(path)
        if message is None:
            message = f"Segment not found at path: '{self.path}'"
        super().__init__(message)


class DaemonError(PlatformError):
    """Base exception for daemon-related errors."""

    pass


class DaemonStartError(DaemonError):
    """Raised when the daemon fails to start."""

    def __init__(self, reason: str, message: str | None = None):
        self.reason = reason
        if message is None:
            message = f"Failed to start daemon: {reason}"
        super().__init__(message)


class DaemonStopError(DaemonError):
    """Raised when the daemon fails to stop."""

    def __init__(self, reason: str, message: str | None = None):
        self.reason = reason
        if message is None:
            message = f"Failed to stop daemon: {reason}"
        super().__init__(message)


class DaemonNotRunningError(DaemonError):
    """Raised when daemon operation requires running daemon but it's not active."""

    def __init__(self, repo_id: str | None = None, message: str | None = None):
        self.repo_id = repo_id
        if message is None:
            if repo_id:
                message = f"Daemon not running for repository: '{repo_id}'"
            else:
                message = "Daemon is not running"
        super().__init__(message)


class HealthCheckError(PlatformError):
    """Raised when health check fails."""

    def __init__(self, check_name: str, message: str | None = None):
        self.check_name = check_name
        if message is None:
            message = f"Health check failed: {check_name}"
        super().__init__(message)


class RuntimeError(PlatformError):
    """Base exception for runtime-related errors."""

    pass


class RuntimeNotInitializedError(RuntimeError):
    """Raised when runtime is accessed before initialization."""

    def __init__(self, repo_id: str, message: str | None = None):
        self.repo_id = repo_id
        if message is None:
            message = f"Runtime not initialized for repository: '{repo_id}'"
        super().__init__(message)


class StorageError(PlatformError):
    """Base exception for storage-related errors."""

    pass


class DatabaseError(StorageError):
    """Raised when database operation fails."""

    def __init__(self, db_path: Path, reason: str, message: str | None = None):
        self.db_path = db_path
        self.reason = reason
        if message is None:
            message = f"Database error at '{db_path}': {reason}"
        super().__init__(message)
