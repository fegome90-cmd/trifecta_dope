"""
Tests for helpers heartbeat functionality.
"""
import tempfile
from pathlib import Path

from src.domain.result import Ok, Err


class TestHeartbeat:
    """Test heartbeat mechanism for long-running WOs."""

    def test_update_lock_heartbeat(self):
        """Test updating lock heartbeat returns Ok result."""
        from scripts.helpers import update_lock_heartbeat

        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "test.lock"
            lock_path.write_text("Locked by ctx_wo_take.py at 2025-01-01T00:00:00Z\nPID: 12345\nUser: test\n")

            result = update_lock_heartbeat(lock_path)
            assert isinstance(result, Ok)
            assert result.unwrap() is True

    def test_update_lock_heartbeat_missing_lock(self):
        """Test updating heartbeat on non-existent lock returns Err."""
        from scripts.helpers import update_lock_heartbeat

        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "nonexistent.lock"

            result = update_lock_heartbeat(lock_path)
            assert isinstance(result, Err)
            error_msg = result.unwrap_err()
            assert "LOCK_NOT_FOUND" in error_msg

    def test_check_lock_validity_valid_lock(self):
        """Test checking lock validity for a valid lock."""
        from scripts.helpers import check_lock_validity

        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "test.lock"
            lock_path.write_text("PID: 12345\nUser: test\n")

            # This lock has no timestamp line, so should be invalid
            is_valid, metadata = check_lock_validity(lock_path)
            assert is_valid is False
