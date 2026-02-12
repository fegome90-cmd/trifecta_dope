"""
Transaction management for WO operations.
Pure domain logic - defines rollback operations.
"""

from dataclasses import dataclass
from enum import StrEnum


class RollbackType(StrEnum):
    """Types of rollback operations for WO transactions.

    Each represents a compensating action that can undo
    a previously executed operation.
    """

    REMOVE_LOCK = "remove_lock"
    MOVE_WO_TO_PENDING = "move_wo_to_pending"
    REMOVE_WORKTREE = "remove_worktree"
    REMOVE_BRANCH = "remove_branch"


class TransactionError(Exception):
    """Exception raised for transaction invariant violations."""

    pass


@dataclass(frozen=True)
class RollbackOperation:
    """Represents a rollback operation."""

    name: str
    description: str
    rollback_type: RollbackType


@dataclass(frozen=True)
class Transaction:
    """Transaction with rollback capability."""

    wo_id: str
    operations: tuple[RollbackOperation, ...]
    is_committed: bool = False

    def add_operation(self, op: RollbackOperation) -> "Transaction":
        """Add operation to transaction (immutable).

        Raises:
            TransactionError: If transaction is already committed
        """
        if self.is_committed:
            raise TransactionError(
                f"Cannot modify committed transaction for WO {self.wo_id}. "
                f"Committed transactions are immutable."
            )
        return Transaction(
            wo_id=self.wo_id, operations=self.operations + (op,), is_committed=self.is_committed
        )

    def commit(self) -> "Transaction":
        """Mark transaction as committed.

        Returns:
            A new Transaction instance with is_committed=True

        Raises:
            TransactionError: If transaction is already committed
        """
        if self.is_committed:
            raise TransactionError(
                f"Transaction for WO {self.wo_id} is already committed. Cannot commit twice."
            )
        return Transaction(wo_id=self.wo_id, operations=self.operations, is_committed=True)

    def needs_rollback(self) -> bool:
        """Check if transaction needs rollback."""
        return not self.is_committed and len(self.operations) > 0
