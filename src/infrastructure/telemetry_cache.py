"""
Telemetry wrapper for AstCache.

This module provides a decorator pattern wrapper that adds telemetry
to any AstCache implementation without modifying the Protocol.
"""

import time
from typing import Any, Optional, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from src.domain.ast_cache import AstCache, CacheStats
    from src.infrastructure.telemetry import Telemetry


class TelemetryAstCache:
    """
    Wraps any AstCache and emits telemetry events for all operations.

    This wrapper preserves the AstCache Protocol while adding observability.
    Events emitted:
    - ast.cache.hit: Value found in cache
    - ast.cache.miss: Value not found in cache
    - ast.cache.write: New value written
    - ast.cache.delete: Entry deleted
    - ast.cache.clear: Full cache cleared
    """

    def __init__(
        self, inner: "AstCache", telemetry: "Telemetry", segment_id: str, redact_paths: bool = True
    ):
        """
        Initialize telemetry wrapper.

        Args:
            inner: The actual cache implementation to wrap
            telemetry: Telemetry instance for event emission
            segment_id: Segment identifier for context
            redact_paths: Whether to redact sensitive paths in events
        """
        self._inner = inner
        self._tel = telemetry
        self._segment_id = segment_id
        self._backend = inner.__class__.__name__
        self._redact = redact_paths

    def _redact_path(self, path: Optional[Path]) -> str:
        """Redact sensitive portions of file paths."""
        if path is None:
            return "[NONE]"
        if not self._redact:
            return str(path)

        path_str = str(path)
        # Redact home directory
        home = str(Path.home())
        if home in path_str:
            return path_str.replace(home, "[HOME]")
        return path_str

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with telemetry."""
        t0 = time.perf_counter_ns()
        value = self._inner.get(key)
        timing_ms = max(1, (time.perf_counter_ns() - t0) // 1_000_000)

        status = "hit" if value is not None else "miss"

        # Emit telemetry event
        self._tel.event(
            cmd=f"ast.cache.{status}",
            args={"cache_key": key},
            result={
                "backend": self._backend,
                "segment_id": self._segment_id,
            },
            timing_ms=timing_ms,
        )

        return value

    def set(self, key: str, value: Any) -> None:
        """Set value in cache with telemetry."""
        t0 = time.perf_counter_ns()
        self._inner.set(key, value)
        timing_ms = max(1, (time.perf_counter_ns() - t0) // 1_000_000)

        self._tel.event(
            cmd="ast.cache.write",
            args={"cache_key": key},
            result={
                "backend": self._backend,
                "segment_id": self._segment_id,
            },
            timing_ms=timing_ms,
        )

    def delete(self, key: str) -> bool:
        """Delete value from cache with telemetry."""
        t0 = time.perf_counter_ns()
        result = self._inner.delete(key)
        timing_ms = max(1, (time.perf_counter_ns() - t0) // 1_000_000)

        self._tel.event(
            cmd="ast.cache.delete",
            args={"cache_key": key},
            result={
                "backend": self._backend,
                "segment_id": self._segment_id,
                "existed": result,
            },
            timing_ms=timing_ms,
        )

        return result

    def clear(self) -> None:
        """Clear all cache with telemetry."""
        t0 = time.perf_counter_ns()
        self._inner.clear()
        timing_ms = max(1, (time.perf_counter_ns() - t0) // 1_000_000)

        self._tel.event(
            cmd="ast.cache.clear",
            args={},
            result={
                "backend": self._backend,
                "segment_id": self._segment_id,
            },
            timing_ms=timing_ms,
        )

    def stats(self) -> "CacheStats":
        """Get cache stats (no telemetry - stats are for telemetry itself)."""
        return self._inner.stats()
