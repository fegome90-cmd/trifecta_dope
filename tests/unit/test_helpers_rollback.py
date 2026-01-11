"""
Tests for helpers rollback functionality.
"""
import tempfile
from pathlib import Path


class TestRollbackExecution:
    """Test transaction rollback execution."""

    def test_execute_rollback_remove_lock(self):
        from scripts.helpers import execute_rollback
        from src.domain.wo_transactions import Transaction, RollbackOperation

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "_ctx" / "jobs" / "running").mkdir(parents=True)

            # Create test lock
            lock_path = root / "_ctx" / "jobs" / "running" / "WO-TEST.lock"
            lock_path.write_text("test lock")

            tx = Transaction(
                wo_id="WO-TEST",
                operations=[
                    RollbackOperation(name="test", description="Test", rollback_type="remove_lock")
                ]
            )

            all_succeeded, failed_ops = execute_rollback(tx, root)
            assert all_succeeded is True
            assert len(failed_ops) == 0
            assert not lock_path.exists()

    def test_execute_rollback_committed_noop(self):
        from scripts.helpers import execute_rollback
        from src.domain.wo_transactions import Transaction

        # Committed transaction should not rollback
        tx = Transaction(wo_id="WO-TEST", operations=[], is_committed=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            all_succeeded, failed_ops = execute_rollback(tx, Path(tmpdir))
            assert all_succeeded is True
            assert len(failed_ops) == 0
