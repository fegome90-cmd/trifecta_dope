"""
Tests for WO transaction management.
Pure domain logic - no mocks, no IO.
"""


class TestTransactionCommit:
    """Test transaction lifecycle."""

    def test_transaction_commit(self):
        from src.domain.wo_transactions import Transaction, RollbackOperation

        tx = Transaction(wo_id="WO-TEST", operations=[], is_committed=False)
        assert not tx.needs_rollback()

        tx = tx.add_operation(RollbackOperation(
            name="test_op", description="Test", rollback_type="remove_lock"
        ))
        assert tx.needs_rollback()

        tx = tx.commit()
        assert not tx.needs_rollback()
        assert tx.is_committed

    def test_add_operation_is_immutable(self):
        from src.domain.wo_transactions import Transaction, RollbackOperation

        tx1 = Transaction(wo_id="WO-TEST", operations=[], is_committed=False)
        tx2 = tx1.add_operation(RollbackOperation(
            name="test_op", description="Test", rollback_type="remove_lock"
        ))

        # Original transaction unchanged
        assert len(tx1.operations) == 0
        assert len(tx2.operations) == 1
