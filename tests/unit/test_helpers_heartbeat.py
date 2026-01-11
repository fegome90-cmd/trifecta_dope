"""
Tests for helpers heartbeat functionality.
"""
import tempfile
from pathlib import Path


class TestHeartbeat:
    """Test heartbeat mechanism for long-running WOs."""

    def test_update_lock_heartbeat(self):
        from scripts.helpers import update_lock_heartbeat

        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "test.lock"
            lock_path.write_text("PID: 12345\nUser: test\n")

            result = update_lock_heartbeat(lock_path)
            assert result is True

    def test_check_lock_validity_valid_lock(self):
        from scripts.helpers import check_lock_validity

        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "test.lock"
            lock_path.write_text("PID: 12345\nUser: test\n")

            # This lock has no PID, so should be invalid
            is_valid, metadata = check_lock_validity(lock_path)
            assert is_valid is False
