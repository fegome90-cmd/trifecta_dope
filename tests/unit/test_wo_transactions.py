"""
Tests for WO transaction management.
Pure domain logic - no mocks, no IO.
"""

from src.domain.wo_transactions import Transaction, RollbackOperation, RollbackType, TransactionError
import pytest


class TestTransactionCommit:
    """Test transaction lifecycle."""

    def test_transaction_commit(self):
        tx = Transaction(wo_id="WO-TEST", operations=(), is_committed=False)
        assert not tx.needs_rollback()

        tx = tx.add_operation(RollbackOperation(
            name="test_op", description="Test", rollback_type=RollbackType.REMOVE_LOCK
        ))
        assert tx.needs_rollback()

        tx = tx.commit()
        assert not tx.needs_rollback()
        assert tx.is_committed

    def test_add_operation_is_immutable(self):
        tx1 = Transaction(wo_id="WO-TEST", operations=(), is_committed=False)
        tx2 = tx1.add_operation(RollbackOperation(
            name="test_op", description="Test", rollback_type=RollbackType.REMOVE_LOCK
        ))

        # Original transaction unchanged
        assert len(tx1.operations) == 0
        assert len(tx2.operations) == 1

    def test_cannot_add_operation_to_committed_transaction(self):
        """Test that adding operations to committed transaction raises error."""
        tx = Transaction(
            wo_id="WO-TEST",
            operations=(),
            is_committed=True
        )

        with pytest.raises(TransactionError, match="Cannot modify committed transaction"):
            tx.add_operation(RollbackOperation(
                name="test_op", description="Test", rollback_type=RollbackType.REMOVE_LOCK
            ))

    def test_cannot_commit_twice(self):
        """Test that committing twice raises error."""
        tx = Transaction(
            wo_id="WO-TEST",
            operations=(),
            is_committed=False
        )

        tx_committed = tx.commit()
        assert tx_committed.is_committed

        with pytest.raises(TransactionError, match="already committed"):
            tx_committed.commit()
