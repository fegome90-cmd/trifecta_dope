"""
File-locked wrapper for AstCache.

This wrapper adds deterministic file locking around any AstCache implementation
without modifying the underlying cache. Keeps OS concerns in infrastructure layer.
"""

from typing import Any, Optional, TYPE_CHECKING
from pathlib import Path
import time

if TYPE_CHECKING:
    from src.domain.ast_cache import AstCache, CacheStats
    from src.infrastructure.telemetry import Telemetry


class FileLockedAstCache:
    """
    Wrapper that adds file locking to any AstCache implementation.

    Value:
    - Deterministic timeout (no random OperationalError)
    - Telemetry on lock contention
    - Explicit control when daemon+CLI compete
    """

    def __init__(
        self,
        inner: "AstCache",
        lock_path: Path,
        telemetry: Optional["Telemetry"] = None,
        timeout: float = 2.0,
    ):
        """
        Initialize file-locked cache wrapper.

        Args:
            inner: The underlying cache implementation
            lock_path: Path to lock file (e.g., db_path.with_suffix('.lock'))
            telemetry: Optional telemetry for contention events
            timeout: Timeout in seconds for lock acquisition (default: 2s)
        """
        self._inner = inner
        self._lock_path = lock_path
        self._telemetry = telemetry
        self._timeout = timeout

    def _with_lock(self, operation: str, func):
        """
        Execute function with file lock held.

        Args:
            operation: Name of operation (for telemetry/errors)
            func: Function to execute under lock

        Raises:
            RuntimeError: If lock cannot be acquired within timeout
        """
        from filelock import FileLock, Timeout as LockTimeout

        lock = FileLock(str(self._lock_path), timeout=self._timeout)
        t0 = time.perf_counter_ns()

        try:
            with lock:
                return func()
        except LockTimeout as e:
            wait_ms = (time.perf_counter_ns() - t0) // 1_000_000

            if self._telemetry:
                self._telemetry.event(
                    cmd="ast.cache.lock_timeout",
                    args={"operation": operation},
                    result={"lock_path": str(self._lock_path), "timeout_sec": self._timeout},
                    timing_ms=wait_ms,
                )

            raise RuntimeError(
                f"Could not acquire cache lock for '{operation}' after {self._timeout}s. "
                f"Another process is using the cache."
            ) from e
        finally:
            # Emit lock wait time if telemetry available (even on success)
            if self._telemetry:
                wait_ms = (time.perf_counter_ns() - t0) // 1_000_000
                if wait_ms > 10:  # Only log if wait was non-trivial
                    self._telemetry.event(
                        cmd="ast.cache.lock_wait",
                        args={"operation": operation},
                        result={"lock_path": str(self._lock_path)},
                        timing_ms=wait_ms,
                    )

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with file lock."""
        return self._with_lock("get", lambda: self._inner.get(key))

    def set(self, key: str, value: Any) -> None:
        """Set value in cache with file lock."""
        self._with_lock("set", lambda: self._inner.set(key, value))

    def delete(self, key: str) -> bool:
        """Delete value from cache with file lock."""
        return self._with_lock("delete", lambda: self._inner.delete(key))

    def clear(self) -> None:
        """Clear cache with file lock."""
        self._with_lock("clear", lambda: self._inner.clear())

    def stats(self) -> "CacheStats":
        """Get cache stats (no lock needed - read-only metadata)."""
        return self._inner.stats()
