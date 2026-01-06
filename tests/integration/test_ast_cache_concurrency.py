"""
Test de concurrencia para AST cache.

Este test debe FALLAR sin file locks y PASAR con locks.
"""

import pytest
import multiprocessing
import time
from pathlib import Path
from src.domain.ast_cache import SQLiteCache


def worker_write(db_path_str, worker_id, iterations):
    """Worker que escribe al cache repetidamente."""
    db_path = Path(db_path_str)
    cache = SQLiteCache(db_path)

    for i in range(iterations):
        key = f"worker_{worker_id}_key_{i}"
        value = {"data": f"value_{i}", "worker": worker_id}
        cache.set(key, value)
        time.sleep(0.001)  # Pequeño delay para aumentar contención


def test_concurrent_writes_no_corruption(tmp_path):
    """
    RED test: Sin file locks, este test debe fallar (DB corrupta o race condition).
    GREEN test: Con file locks, debe pasar.

    Ejecuta 2 workers escribiendo 20 entries cada uno.
    """
    db_path = tmp_path / "concurrent_test.db"

    # Spawn 2 workers
    iterations = 20
    workers = [
        multiprocessing.Process(target=worker_write, args=(str(db_path), 0, iterations)),
        multiprocessing.Process(target=worker_write, args=(str(db_path), 1, iterations)),
    ]

    for w in workers:
        w.start()
    for w in workers:
        w.join()

    # Verify DB is not corrupted
    cache = SQLiteCache(db_path)
    stats = cache.stats()

    # Should have exactly 40 entries (20 from each worker)
    assert stats.entries == iterations * 2, (
        f"Expected {iterations * 2} entries, got {stats.entries}"
    )

    # Verify we can read all keys
    for worker_id in range(2):
        for i in range(iterations):
            key = f"worker_{worker_id}_key_{i}"
            value = cache.get(key)
            assert value is not None, f"Missing key: {key}"
            assert value["worker"] == worker_id


def test_lock_timeout_behavior(tmp_path):
    """
    Test que lock timeout emite error claro.

    Este test simula que el lock está tomado y verifica que:
    1. Se lanza RuntimeError
    2. El mensaje es claro
    """
    from filelock import FileLock

    db_path = tmp_path / "timeout_test.db"
    lock_path = db_path.with_suffix(".lock")

    # Hold lock manually
    lock = FileLock(str(lock_path), timeout=0.1)
    lock.acquire()

    try:
        # Try to use cache (should timeout)
        cache = SQLiteCache(db_path, lock_timeout=0.5)
        with pytest.raises(RuntimeError, match="Could not acquire cache lock"):
            cache.set("key", "value")
    finally:
        lock.release()


def test_concurrent_stress(tmp_path):
    """
    Stress test: 50 iteraciones concurrentes deben pasar todas.

    Este es el criterio de aceptación brutal del usuario.
    """
    db_path = tmp_path / "stress_test.db"

    iterations = 50
    workers = [
        multiprocessing.Process(target=worker_write, args=(str(db_path), i, 5))
        for i in range(10)  # 10 workers, 5 writes each
    ]

    for w in workers:
        w.start()
    for w in workers:
        w.join()

    # Verify 50 total entries
    cache = SQLiteCache(db_path)
    stats = cache.stats()
    assert stats.entries == iterations, f"Expected {iterations} entries, got {stats.entries}"
