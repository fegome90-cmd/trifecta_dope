"""
Transaction recovery tests.

Tests recovery scenarios for failed/crashed WO transactions.
Focuses on detecting and cleaning up inconsistent states.
"""

import tempfile
import yaml
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from src.domain.wo_entities import WorkOrder, WOState, Priority
from src.domain.wo_transactions import Transaction, RollbackOperation, RollbackType
from scripts.helpers import execute_rollback


class TestTransactionRecoveryScenarios:
    """Test recovery from various transaction failure scenarios."""

    def test_rollback_after_worktree_created(self):
        """Test rollback when branch creation fails after worktree is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "_ctx" / "jobs" / "running").mkdir(parents=True)
            (root / "_ctx" / "jobs" / "pending").mkdir(parents=True)  # Create pending directory
            (root.parent / ".worktrees" / "WO-0901").mkdir(parents=True, exist_ok=True)

            # Create a WO in running state
            running_path = root / "_ctx" / "jobs" / "running" / "WO-0901.yaml"
            wo_data = {
                "id": "WO-0901",
                "status": "running",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "owner": "testuser",
            }
            running_path.write_text(yaml.safe_dump(wo_data, sort_keys=False))

            # Create a lock
            lock_path = root / "_ctx" / "jobs" / "running" / "WO-0901.lock"
            lock_path.write_text("test lock")

            # Simulate transaction that acquired worktree but failed before branch
            tx = Transaction(
                wo_id="WO-0901",
                operations=(
                    RollbackOperation(
                        name="remove_lock",
                        description="Remove lock file",
                        rollback_type=RollbackType.REMOVE_LOCK,
                    ),
                    RollbackOperation(
                        name="cleanup_worktree",
                        description="Remove worktree directory",
                        rollback_type=RollbackType.REMOVE_WORKTREE,
                    ),
                    RollbackOperation(
                        name="move_to_pending",
                        description="Move WO back to pending",
                        rollback_type=RollbackType.MOVE_WO_TO_PENDING,
                    ),
                ),
            )

            # Mock cleanup_worktree to avoid git operations
            with patch("scripts.helpers.cleanup_worktree", return_value=True):
                result = execute_rollback(tx, root)

            # All operations should succeed
            assert result.is_partial_failure is False
            assert len(result.succeeded_ops) == 3

            # Verify cleanup
            assert not lock_path.exists(), "Lock should be removed"
            assert not running_path.exists(), "WO should be moved from running"

            pending_path = root / "_ctx" / "jobs" / "pending" / "WO-0901.yaml"
            assert pending_path.exists(), "WO should be in pending"

            # Verify WO state was reset
            pending_wo = yaml.safe_load(pending_path.read_text())
            assert pending_wo["status"] == "pending"
            assert pending_wo["started_at"] is None
            assert pending_wo["owner"] is None

    def test_rollback_after_branch_created(self):
        """Test rollback when lock fails after branch is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "_ctx" / "jobs" / "running").mkdir(parents=True)
            (root / "_ctx" / "jobs" / "pending").mkdir(parents=True)  # Create pending directory
            (root.parent / ".worktrees" / "WO-0902").mkdir(parents=True, exist_ok=True)

            # Create WO in running state
            running_path = root / "_ctx" / "jobs" / "running" / "WO-0902.yaml"
            wo_data = {
                "id": "WO-0902",
                "status": "running",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "owner": "testuser",
            }
            running_path.write_text(yaml.safe_dump(wo_data, sort_keys=False))

            # Transaction with worktree and branch cleanup
            tx = Transaction(
                wo_id="WO-0902",
                operations=(
                    RollbackOperation(
                        name="remove_worktree",
                        description="Remove worktree",
                        rollback_type=RollbackType.REMOVE_WORKTREE,
                    ),
                    RollbackOperation(
                        name="remove_branch",
                        description="Delete branch",
                        rollback_type=RollbackType.REMOVE_BRANCH,
                    ),
                    RollbackOperation(
                        name="move_to_pending",
                        description="Move WO to pending",
                        rollback_type=RollbackType.MOVE_WO_TO_PENDING,
                    ),
                ),
            )

            # Mock git operations
            with patch("scripts.helpers.cleanup_worktree", return_value=True):
                with patch("scripts.helpers.run_command") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)
                    result = execute_rollback(tx, root)

            assert result.is_partial_failure is False
            assert len(result.succeeded_ops) == 3

            # Verify WO moved to pending
            pending_path = root / "_ctx" / "jobs" / "pending" / "WO-0902.yaml"
            assert pending_path.exists()

    def test_partial_state_detection(self):
        """Test detection and cleanup of inconsistent WO state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "_ctx" / "jobs" / "running").mkdir(parents=True)
            (root / "_ctx" / "jobs" / "pending").mkdir(parents=True)

            # Scenario: WO is in running state but no lock exists (crashed after lock removal)
            running_path = root / "_ctx" / "jobs" / "running" / "WO-0903.yaml"
            wo_data = {
                "id": "WO-0903",
                "status": "running",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "owner": "testuser",
            }
            running_path.write_text(yaml.safe_dump(wo_data, sort_keys=False))

            # No lock exists - WO is in inconsistent state
            lock_path = root / "_ctx" / "jobs" / "running" / "WO-0903.lock"
            assert not lock_path.exists()

            # Rollback should handle missing lock gracefully
            tx = Transaction(
                wo_id="WO-0903",
                operations=(
                    RollbackOperation(
                        name="remove_lock",
                        description="Remove lock (already gone)",
                        rollback_type=RollbackType.REMOVE_LOCK,
                    ),
                    RollbackOperation(
                        name="move_to_pending",
                        description="Move WO to pending",
                        rollback_type=RollbackType.MOVE_WO_TO_PENDING,
                    ),
                ),
            )

            result = execute_rollback(tx, root)

            # Should succeed even though lock was already gone
            assert result.is_partial_failure is False
            assert len(result.succeeded_ops) == 2

            # Verify WO moved to pending
            pending_path = root / "_ctx" / "jobs" / "pending" / "WO-0903.yaml"
            assert pending_path.exists()

            pending_wo = yaml.safe_load(pending_path.read_text())
            assert pending_wo["status"] == "pending"

    def test_recover_from_incomplete_transaction(self):
        """Test recovery when transaction has partial operations applied."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "_ctx" / "jobs" / "running").mkdir(parents=True)
            (root / "_ctx" / "jobs" / "pending").mkdir(parents=True)
            (root.parent / ".worktrees" / "WO-0904").mkdir(parents=True, exist_ok=True)

            # Scenario: Worktree exists, WO is running, but branch creation failed
            running_path = root / "_ctx" / "jobs" / "running" / "WO-0904.yaml"
            wo_data = {
                "id": "WO-0904",
                "status": "running",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "owner": "testuser",
            }
            running_path.write_text(yaml.safe_dump(wo_data, sort_keys=False))

            # Transaction with worktree and move operations
            tx = Transaction(
                wo_id="WO-0904",
                operations=(
                    RollbackOperation(
                        name="remove_worktree",
                        description="Cleanup worktree",
                        rollback_type=RollbackType.REMOVE_WORKTREE,
                    ),
                    RollbackOperation(
                        name="move_to_pending",
                        description="Reset to pending",
                        rollback_type=RollbackType.MOVE_WO_TO_PENDING,
                    ),
                ),
            )

            with patch("scripts.helpers.cleanup_worktree", return_value=True):
                result = execute_rollback(tx, root)

            assert result.is_partial_failure is False
            assert len(result.succeeded_ops) == 2

            # Verify cleanup
            pending_path = root / "_ctx" / "jobs" / "pending" / "WO-0904.yaml"
            assert pending_path.exists()

    def test_rollback_with_multiple_failures(self):
        """Test rollback continues even when some operations fail."""
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "_ctx" / "jobs" / "running").mkdir(parents=True)
            (root / "_ctx" / "jobs" / "pending").mkdir(parents=True)
            (root.parent / ".worktrees" / "WO-0905").mkdir(
                parents=True, exist_ok=True
            )  # Create worktree so cleanup_worktree is called

            # Create lock
            lock_path = root / "_ctx" / "jobs" / "running" / "WO-0905.lock"
            lock_path.write_text("test lock")

            # Create WO in running state
            running_path = root / "_ctx" / "jobs" / "running" / "WO-0905.yaml"
            wo_data = {
                "id": "WO-0905",
                "status": "running",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "owner": "testuser",
            }
            running_path.write_text(yaml.safe_dump(wo_data, sort_keys=False))

            # Transaction with operations where some will fail
            tx = Transaction(
                wo_id="WO-0905",
                operations=(
                    RollbackOperation(
                        name="remove_lock",  # Will succeed
                        description="Remove lock",
                        rollback_type=RollbackType.REMOVE_LOCK,
                    ),
                    RollbackOperation(
                        name="cleanup_worktree",  # Will fail (mocked)
                        description="Cleanup worktree",
                        rollback_type=RollbackType.REMOVE_WORKTREE,
                    ),
                    RollbackOperation(
                        name="move_to_pending",  # Will succeed
                        description="Move to pending",
                        rollback_type=RollbackType.MOVE_WO_TO_PENDING,
                    ),
                ),
            )

            # Mock cleanup_worktree to simulate failure (raise exception)
            with patch(
                "scripts.helpers.cleanup_worktree",
                side_effect=Exception("Simulated cleanup failure"),
            ):
                result = execute_rollback(tx, root)

            # Should be partial failure (worktree cleanup failed)
            assert result.is_partial_failure is True
            assert len(result.succeeded_ops) == 2
            assert len(result.failed_ops) == 1

            # Verify successful operations completed
            assert not lock_path.exists()
            pending_path = root / "_ctx" / "jobs" / "pending" / "WO-0905.yaml"
            assert pending_path.exists()

    def test_committed_transaction_skip_rollback(self):
        """Test that committed transactions skip rollback entirely."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "_ctx" / "jobs" / "done").mkdir(parents=True)

            # Committed transaction should not rollback
            tx = Transaction(wo_id="WO-0906", operations=(), is_committed=True)

            result = execute_rollback(tx, root)

            assert result.is_partial_failure is False
            assert len(result.succeeded_ops) == 0
            assert len(result.failed_ops) == 0


class TestStateConsistency:
    """Test WO state consistency during and after rollback."""

    def test_rollback_maintains_wo_consistency(self):
        """Test that rollback leaves WO in a consistent state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "_ctx" / "jobs" / "running").mkdir(parents=True)
            (root / "_ctx" / "jobs" / "pending").mkdir(parents=True)

            # Create WO in running state with all required fields
            running_path = root / "_ctx" / "jobs" / "running" / "WO-0907.yaml"
            now = datetime.now(timezone.utc)
            wo_data = {
                "id": "WO-0907",
                "epic_id": "E-0001",
                "title": "Consistent WO",
                "priority": "medium",
                "status": "running",
                "started_at": now.isoformat(),
                "owner": "testuser",
                "dod_id": "DOD-DEFAULT",
                "dependencies": [],
                "finished_at": None,
                "branch": "feat/wo-WO-0907",
                "worktree": ".worktrees/WO-0907",
            }
            running_path.write_text(yaml.safe_dump(wo_data, sort_keys=False))

            tx = Transaction(
                wo_id="WO-0907",
                operations=(
                    RollbackOperation(
                        name="move_to_pending",
                        description="Move WO to pending",
                        rollback_type=RollbackType.MOVE_WO_TO_PENDING,
                    ),
                ),
            )

            result = execute_rollback(tx, root)
            assert result.is_partial_failure is False

            # Verify WO can be reconstructed as valid WorkOrder
            pending_path = root / "_ctx" / "jobs" / "pending" / "WO-0907.yaml"
            pending_wo = yaml.safe_load(pending_path.read_text())

            # Should be able to create WorkOrder with the pending data
            wo = WorkOrder(
                id=pending_wo["id"],
                epic_id=pending_wo["epic_id"],
                title=pending_wo["title"],
                priority=Priority.MEDIUM,
                status=WOState.PENDING,
                owner=pending_wo["owner"],
                dod_id=pending_wo["dod_id"],
                dependencies=(),
                started_at=None,
                finished_at=None,
                branch=None,
                worktree=None,
            )

            assert wo.status == WOState.PENDING
            assert wo.owner is None  # Should be cleared
            assert wo.started_at is None  # Should be cleared
