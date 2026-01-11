"""
Contractual tests for FileLockedAstCache.

These tests verify the **contract** of file locking, not just "it doesn't crash".
"""

import pytest
import time
from pathlib import Path
from filelock import FileLock
from src.domain.ast_cache import SQLiteCache
from src.infrastructure.file_locked_cache import FileLockedAstCache


# Module-level worker for multiprocessing (avoids pickling issues)
def _concurrent_worker(db_path_str, lock_path_str, worker_id):
    """Worker for concurrent writes test."""
    db_path = Path(db_path_str)
    lock_path = Path(lock_path_str)
    inner = SQLiteCache(db_path)
    cache = FileLockedAstCache(inner=inner, lock_path=lock_path, timeout=5.0)

    for i in range(10):
        cache.set(f"worker_{worker_id}_key_{i}", {"worker": worker_id, "i": i})
        time.sleep(0.001)


def test_lock_timeout_contract(tmp_path):
    """
    Contract: If lock is held, operation MUST fail deterministically within timeout.

    This is the value of P2.2: determinism, not "SQLite didn't crash".
    """
    db_path = tmp_path / "test.db"
    lock_path = db_path.with_suffix(".lock")

    # Create cache
    inner = SQLiteCache(db_path)
    cache = FileLockedAstCache(inner=inner, lock_path=lock_path, timeout=0.5)

    # Hold lock externally (simulating daemon)
    external_lock = FileLock(str(lock_path), timeout=10)
    external_lock.acquire()

    try:
        # Attempt operation (should timeout)
        t0 = time.perf_counter()
        with pytest.raises(RuntimeError, match="Could not acquire cache lock"):
            cache.set("key", "value")
        elapsed = time.perf_counter() - t0

        # Verify timeout was deterministic (within ±0.2s of expected)
        assert 0.3 < elapsed < 0.7, f"Expected ~0.5s timeout, got {elapsed:.2f}s"
    finally:
        external_lock.release()


def test_lock_contention_telemetry(tmp_path):
    """
    Contract: Telemetry MUST show lock contention events.

    This enables observability in production.
    """
    from unittest.mock import Mock

    db_path = tmp_path / "test.db"
    lock_path = db_path.with_suffix(".lock")

    # Create cache with telemetry mock
    telemetry_mock = Mock()
    inner = SQLiteCache(db_path)
    cache = FileLockedAstCache(
        inner=inner, lock_path=lock_path, telemetry=telemetry_mock, timeout=0.5
    )

    # Hold lock externally
    external_lock = FileLock(str(lock_path), timeout=10)
    external_lock.acquire()

    try:
        # Attempt operation (will timeout)
        with pytest.raises(RuntimeError):
            cache.set("key", "value")

        # Verify telemetry was called with timeout event
        assert telemetry_mock.event.called
        calls = [call for call in telemetry_mock.event.call_args_list]
        timeout_calls = [c for c in calls if c[1]["cmd"] == "ast.cache.lock_timeout"]

        assert len(timeout_calls) > 0, "Expected lock_timeout telemetry event"
        assert timeout_calls[0][1]["args"]["operation"] == "set"
    finally:
        external_lock.release()


def test_lock_success_fast_path(tmp_path):
    """
    Contract: When lock is available, operations succeed normally.
    """
    db_path = tmp_path / "test.db"
    lock_path = db_path.with_suffix(".lock")

    inner = SQLiteCache(db_path)
    cache = FileLockedAstCache(inner=inner, lock_path=lock_path, timeout=2.0)

    # Operations should succeed
    cache.set("key1", {"data": "value1"})
    value = cache.get("key1")

    assert value == {"data": "value1"}
    assert cache.delete("key1") is True
    assert cache.get("key1") is None


def test_lock_concurrent_writes_deterministic(tmp_path):
    """
    Contract: Multiple processes writing MUST NOT corrupt DB.

    With locks, this should be 100% deterministic.
    """
    import multiprocessing

    db_path = tmp_path / "concurrent.db"
    lock_path = db_path.with_suffix(".lock")

    # Spawn 2 workers
    workers = [
        multiprocessing.Process(target=_concurrent_worker, args=(str(db_path), str(lock_path), 0)),
        multiprocessing.Process(target=_concurrent_worker, args=(str(db_path), str(lock_path), 1)),
    ]

    for w in workers:
        w.start()
    for w in workers:
        w.join()

    # Verify all 20 entries exist
    inner = SQLiteCache(db_path)
    cache = FileLockedAstCache(inner=inner, lock_path=lock_path, timeout=2.0)
    stats = cache.stats()

    assert stats.entries == 20, f"Expected 20 entries, got {stats.entries}"
