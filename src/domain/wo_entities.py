"""
Work Order domain entities and business rules.
Pure domain module - no IO, no external dependencies.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from src.domain.result import Result, Ok, Err


class WOState(Enum):
    """Canonical WO states."""
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    PARTIAL = "partial"  # NEW: Support partial completion


@dataclass(frozen=True)
class WOValidationError:
    """WO validation error details."""
    code: str
    message: str
    wo_id: Optional[str] = None


@dataclass(frozen=True)
class WorkOrder:
    """Work Order entity (immutable)."""
    id: str
    epic_id: str
    title: str
    priority: str
    status: WOState
    owner: Optional[str]
    dod_id: str
    dependencies: list[str]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    branch: Optional[str]
    worktree: Optional[str]

    def can_transition_to(self, new_state: WOState) -> Result[None, WOValidationError]:
        """Validate state transition is legal."""
        valid_transitions = {
            WOState.PENDING: [WOState.RUNNING],
            WOState.RUNNING: [WOState.DONE, WOState.FAILED, WOState.PARTIAL],
            WOState.PARTIAL: [WOState.RUNNING, WOState.DONE, WOState.FAILED],
            WOState.DONE: [],
            WOState.FAILED: [WOState.PENDING],
        }
        allowed = valid_transitions.get(self.status, [])
        if new_state not in allowed:
            return Err(WOValidationError(
                code="INVALID_STATE_TRANSITION",
                message=f"Cannot transition from {self.status.value} to {new_state.value}",
                wo_id=self.id
            ))
        return Ok(None)

    def validate_dependencies(self, completed_wo_ids: set[str]) -> Result[None, WOValidationError]:
        """Validate that all dependencies are satisfied."""
        unsatisfied = [dep for dep in self.dependencies if dep not in completed_wo_ids]
        if unsatisfied:
            return Err(WOValidationError(
                code="UNSATISFIED_DEPENDENCIES",
                message=f"Dependencies not satisfied: {', '.join(unsatisfied)}",
                wo_id=self.id
            ))
        return Ok(None)

    def is_stale(self, max_age_seconds: int = 3600) -> bool:
        """Check if WO is stale (started too long ago)."""
        if self.status != WOState.RUNNING or self.started_at is None:
            return False
        age = (datetime.now(timezone.utc) - self.started_at).total_seconds()
        return age >= max_age_seconds
