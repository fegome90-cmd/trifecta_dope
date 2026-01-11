"""
Transaction management for WO operations.
Pure domain logic - defines rollback operations.
"""
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class RollbackOperation:
    """Represents a rollback operation."""
    name: str
    description: str
    rollback_type: str  # "remove_lock", "move_wo", "delete_worktree", etc.


@dataclass(frozen=True)
class Transaction:
    """Transaction with rollback capability."""
    wo_id: str
    operations: List[RollbackOperation]
    is_committed: bool = False

    def add_operation(self, op: RollbackOperation) -> "Transaction":
        """Add operation to transaction (immutable)."""
        return Transaction(
            wo_id=self.wo_id,
            operations=self.operations + [op],
            is_committed=self.is_committed
        )

    def commit(self) -> "Transaction":
        """Mark transaction as committed."""
        return Transaction(
            wo_id=self.wo_id,
            operations=self.operations,
            is_committed=True
        )

    def needs_rollback(self) -> bool:
        """Check if transaction needs rollback."""
        return not self.is_committed and len(self.operations) > 0
