"""
Tests for helpers rollback functionality.

Tests the rollback execution with RollbackResult tracking and RollbackType enum.
"""
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.domain.wo_transactions import Transaction, RollbackOperation, RollbackType


class TestRollbackExecution:
    """Test transaction rollback execution."""

    def test_execute_rollback_remove_lock(self):
        """Test rollback of lock removal operation."""
        from scripts.helpers import execute_rollback

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "_ctx" / "jobs" / "running").mkdir(parents=True)

            # Create test lock
            lock_path = root / "_ctx" / "jobs" / "running" / "WO-TEST.lock"
            lock_path.write_text("test lock")

            tx = Transaction(
                wo_id="WO-TEST",
                operations=(
                    RollbackOperation(
                        name="test",
                        description="Test",
                        rollback_type=RollbackType.REMOVE_LOCK
                    ),
                )
            )

            result = execute_rollback(tx, root)
            assert result.is_partial_failure is False
            assert len(result.succeeded_ops) == 1
            assert result.succeeded_ops[0] == "test"
            assert len(result.failed_ops) == 0
            assert not lock_path.exists()

    def test_execute_rollback_committed_noop(self):
        """Test that committed transactions skip rollback."""
        from scripts.helpers import execute_rollback

        # Committed transaction should not rollback
        tx = Transaction(wo_id="WO-TEST", operations=(), is_committed=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            result = execute_rollback(tx, Path(tmpdir))
            assert result.is_partial_failure is False
            assert len(result.succeeded_ops) == 0
            assert len(result.failed_ops) == 0

    def test_execute_rollback_move_wo_to_pending(self):
        """Test rollback moving WO from running back to pending."""
        from scripts.helpers import execute_rollback
        import yaml

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "_ctx" / "jobs" / "running").mkdir(parents=True)
            (root / "_ctx" / "jobs" / "pending").mkdir(parents=True)

            # Create test WO in running state
            running_path = root / "_ctx" / "jobs" / "running" / "WO-TEST.yaml"
            wo_data = {
                "id": "WO-TEST",
                "status": "running",
                "started_at": "2025-01-01T00:00:00Z",
                "owner": "testuser"
            }
            running_path.write_text(yaml.safe_dump(wo_data, sort_keys=False))

            tx = Transaction(
                wo_id="WO-TEST",
                operations=(
                    RollbackOperation(
                        name="move_to_pending",
                        description="Move WO to pending",
                        rollback_type=RollbackType.MOVE_WO_TO_PENDING
                    ),
                )
            )

            result = execute_rollback(tx, root)
            assert result.is_partial_failure is False
            assert len(result.succeeded_ops) == 1

            # Verify WO was moved to pending
            pending_path = root / "_ctx" / "jobs" / "pending" / "WO-TEST.yaml"
            assert pending_path.exists()
            assert not running_path.exists()

            # Verify status was reset
            pending_wo = yaml.safe_load(pending_path.read_text())
            assert pending_wo["status"] == "pending"
            assert pending_wo["started_at"] is None
            assert pending_wo["owner"] is None

    def test_execute_rollback_remove_worktree(self):
        """Test rollback of worktree removal (mock test)."""
        from scripts.helpers import execute_rollback

        tx = Transaction(
            wo_id="WO-TEST",
            operations=(
                RollbackOperation(
                    name="cleanup_worktree",
                    description="Remove worktree",
                    rollback_type=RollbackType.REMOVE_WORKTREE
                ),
            )
        )

        # Mock cleanup_worktree to avoid actual git operations
        with patch("scripts.helpers.cleanup_worktree", return_value=True) as mock_cleanup:
            with tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir)
                (root / ".worktrees" / "WO-TEST").mkdir(parents=True)

                result = execute_rollback(tx, root)
                assert result.is_partial_failure is False
                assert len(result.succeeded_ops) == 1
                mock_cleanup.assert_called_once_with(root, "WO-TEST")

    def test_execute_rollback_remove_branch(self):
        """Test rollback of branch removal (mock test)."""
        from scripts.helpers import execute_rollback

        tx = Transaction(
            wo_id="WO-TEST",
            operations=(
                RollbackOperation(
                    name="delete_branch",
                    description="Remove branch",
                    rollback_type=RollbackType.REMOVE_BRANCH
                ),
            )
        )

        # Mock run_command to avoid actual git operations
        with patch("scripts.helpers.run_command") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            with tempfile.TemporaryDirectory() as tmpdir:
                result = execute_rollback(tx, Path(tmpdir))
                assert result.is_partial_failure is False
                assert len(result.succeeded_ops) == 1
                mock_run.assert_called_once()

    def test_execute_rollback_partial_failure(self):
        """Test rollback tracks partial failures correctly."""
        from scripts.helpers import execute_rollback

        # Create transaction with multiple operations
        tx = Transaction(
            wo_id="WO-TEST",
            operations=(
                RollbackOperation(
                    name="good_op",
                    description="Good operation",
                    rollback_type=RollbackType.REMOVE_LOCK
                ),
                RollbackOperation(
                    name="bad_op",
                    description="Bad operation with unknown rollback type",
                    # Use an invalid rollback type by directly setting a value
                    # that's not in the enum - this will trigger a failure
                    rollback_type="unknown_invalid_type"  # type: ignore
                ),
            )
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "_ctx" / "jobs" / "running").mkdir(parents=True)

            result = execute_rollback(tx, root)
            assert result.is_partial_failure is True
            assert len(result.succeeded_ops) == 1
            assert "good_op" in result.succeeded_ops
            assert len(result.failed_ops) == 1
            assert result.failed_ops[0][0] == "bad_op"
