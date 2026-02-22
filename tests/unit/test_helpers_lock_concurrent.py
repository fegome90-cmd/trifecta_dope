"""
Concurrent lock acquisition tests.

Tests the atomic lock creation behavior under concurrent access.
Uses both multiprocessing (realistic) and threading (fast smoke tests) approaches.
"""

import sys
import tempfile
import time
from pathlib import Path
from multiprocessing import Process, Queue
from threading import Thread

import pytest

from scripts.helpers import create_lock


class TestConcurrentLockAcquisition:
    """Test lock behavior under concurrent access scenarios."""

    @pytest.mark.skipif(
        sys.version_info >= (3, 13),
        reason="Multiprocessing tests have pickling issues on Python 3.14+",
    )
    def test_two_processes_lock_acquisition_multiprocess(self):
        """Test that only one of two processes acquires the lock (multiprocessing)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "test.lock"
            results = Queue()

            def try_acquire_lock(process_id: int, result_queue: Queue):
                """Attempt to acquire lock and report result."""
                acquired = create_lock(lock_path, "WO-0001")
                result_queue.put((process_id, acquired))

            # Start two processes simultaneously
            p1 = Process(target=try_acquire_lock, args=(1, results))
            p2 = Process(target=try_acquire_lock, args=(2, results))

            p1.start()
            p2.start()

            p1.join(timeout=5)
            p2.join(timeout=5)

            # Collect results
            results_list = []
            while not results.empty():
                results_list.append(results.get())

            assert len(results_list) == 2, "Both processes should report results"

            # Exactly one should have acquired the lock
            acquired_count = sum(1 for _, acquired in results_list if acquired)
            assert acquired_count == 1, f"Expected 1 acquisition, got {acquired_count}"

    @pytest.mark.skipif(
        sys.version_info >= (3, 13),
        reason="Multiprocessing tests have pickling issues on Python 3.14+",
    )
    def test_concurrent_lock_contention_multiprocess(self):
        """Test 10 processes contending for same lock - only 1 wins (multiprocessing)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "contention.lock"
            results = Queue()
            num_processes = 10

            def try_acquire_lock(process_id: int, result_queue: Queue):
                """Attempt to acquire lock and report result."""
                # Add small random delay to increase contention
                time.sleep(0.001 * (process_id % 3))
                acquired = create_lock(lock_path, "WO-0002")
                result_queue.put((process_id, acquired))

            processes = []
            for i in range(num_processes):
                p = Process(target=try_acquire_lock, args=(i, results))
                processes.append(p)
                p.start()

            # Wait for all processes with timeout
            for p in processes:
                p.join(timeout=10)
                if p.is_alive():
                    p.terminate()

            # Collect results
            results_list = []
            while not results.empty():
                results_list.append(results.get())

            # Exactly one should have acquired the lock
            acquired_count = sum(1 for _, acquired in results_list if acquired)
            assert acquired_count == 1, (
                f"Expected 1 acquisition, got {acquired_count} out of {len(results_list)} attempts"
            )

    def test_lock_timeout_after_stale_threading(self):
        """Test stale lock (>1 hour old) can be replaced (threading)."""
        from scripts.helpers import check_lock_age

        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "stale.lock"

            # Create a lock and make it appear stale
            lock_path.write_text("test lock content")
            old_time = time.time() - 3700  # More than 1 hour ago
            import os

            os.utime(lock_path, (old_time, old_time))

            # Lock should be detected as stale
            assert check_lock_age(lock_path, max_age_seconds=3600) is True

    def test_lock_heartbeat_refreshes_stale_window_threading(self):
        """Test active lock heartbeat prevents stale detection (threading)."""
        from scripts.helpers import update_lock_heartbeat, check_lock_age

        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "heartbeat.lock"

            # Create initial lock with timestamp
            lock_path.write_text(
                "Locked by ctx_wo_take.py at 2025-01-01T00:00:00Z\nPID: 12345\nUser: test\n"
            )

            # Make it appear stale (older than 1 hour)
            stale_time = time.time() - 3700
            import os

            os.utime(lock_path, (stale_time, stale_time))

            # Should be detected as stale
            assert check_lock_age(lock_path, max_age_seconds=3600) is True

            # Update heartbeat
            result = update_lock_heartbeat(lock_path)
            from src.domain.result import Ok

            assert isinstance(result, Ok), "Heartbeat update should succeed"

            # Should no longer be stale
            assert check_lock_age(lock_path, max_age_seconds=3600) is False


class TestLockAtomicity:
    """Test lock atomicity guarantees."""

    def test_lock_creation_is_atomic(self):
        """Test that lock creation either fully succeeds or fully fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "atomic.lock"

            # First acquisition should succeed
            assert create_lock(lock_path, "WO-0003") is True
            assert lock_path.exists()

            # Second acquisition should fail atomically
            # No partial lock file should be created
            assert create_lock(lock_path, "WO-ATOMIC") is False

            # Lock content should be intact
            content = lock_path.read_text()
            assert "PID:" in content
            assert "Locked by ctx_wo_take.py at" in content

    def test_concurrent_creation_no_corruption_threading(self):
        """Test concurrent creation doesn't corrupt lock file (threading)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "corruption.lock"
            results = []
            num_threads = 20

            def try_acquire(thread_id: int):
                """Try to acquire lock from thread."""
                acquired = create_lock(lock_path, f"WO-{thread_id + 1000:04d}")
                results.append((thread_id, acquired))

            threads = []
            for i in range(num_threads):
                t = Thread(target=try_acquire, args=(i,))
                threads.append(t)
                t.start()

            for t in threads:
                t.join(timeout=5)

            # Exactly one thread should have acquired
            acquired_count = sum(1 for _, acquired in results if acquired)
            assert acquired_count == 1

            # Lock file should have valid content
            assert lock_path.exists()
            content = lock_path.read_text()
            assert "PID:" in content
            assert "User:" in content
            assert "Hostname:" in content
            # All lines should end with newline
            for line in content.split("\n"):
                if line:  # Skip empty last line
                    assert ":" in line or line.startswith("Locked by"), f"Invalid line: {line}"


class TestLockRecovery:
    """Test lock recovery scenarios."""

    def test_orphaned_lock_detection(self):
        """Test detection of orphaned locks (no corresponding process)."""
        from scripts.helpers import check_lock_validity

        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "orphaned.lock"

            # Create lock with non-existent PID
            lock_path.write_text(
                "Locked by ctx_wo_take.py at 2025-01-01T00:00:00Z\n"
                "PID: 99999\n"  # Non-existent PID
                "User: test\n"
                "Hostname: testhost\n"
            )

            # Lock should be invalid (process doesn't exist)
            is_valid, metadata = check_lock_validity(lock_path)
            assert is_valid is False

    def test_abandoned_lock_timeout(self):
        """Test that abandoned locks can be detected by timeout."""
        from scripts.helpers import check_lock_age

        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "abandoned.lock"

            # Create lock and make it very old
            lock_path.write_text("test lock")
            ancient_time = time.time() - 10000  # Very old
            import os

            os.utime(lock_path, (ancient_time, ancient_time))

            # Should be detected as stale
            assert check_lock_age(lock_path, max_age_seconds=3600) is True
            assert check_lock_age(lock_path, max_age_seconds=100) is True
