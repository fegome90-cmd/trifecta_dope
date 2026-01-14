"""
Work Order domain entities and business rules.
Pure domain module - no IO, no external dependencies.
"""
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, StrEnum
from typing import Optional

from src.domain.result import Result, Ok, Err


# Pattern for valid WO IDs (WO-XXXX format)
WO_ID_PATTERN = re.compile(r"^WO-\d{4}$", re.IGNORECASE)


class WOState(Enum):
    """Canonical WO states."""
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    PARTIAL = "partial"  # NEW: Support partial completion


class Priority(StrEnum):
    """Valid priority levels for Work Orders.

    Ordered from highest to lowest urgency.
    """
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class Governance:
    """Governance metadata for work orders."""
    must: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate Governance invariants."""
        # Validate all must references are valid WO IDs
        for dep in self.must:
            if not dep or not WO_ID_PATTERN.match(dep):
                raise ValueError(f"Invalid WO ID in governance.must: '{dep}'. Expected format: WO-XXXX")


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
    priority: Priority
    status: WOState
    owner: Optional[str]
    dod_id: str
    dependencies: tuple[str, ...]
    governance: Optional[Governance] = None
    run_ids: tuple[str, ...] = field(default_factory=tuple)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None  # Separate from finished_at for closure tracking
    branch: Optional[str] = None
    worktree: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate WorkOrder invariants after construction.

        Raises:
            ValueError: If any invariant is violated
        """
        # Validate ID format (WO-XXXX)
        if not self.id or not WO_ID_PATTERN.match(self.id):
            raise ValueError(f"Invalid WO ID format: '{self.id}'. Expected format: WO-XXXX")

        # Validate DoD ID is non-empty
        if not self.dod_id or not self.dod_id.strip():
            raise ValueError(f"DoD ID cannot be empty: '{self.dod_id}'")

        # Validate title is non-empty
        if not self.title or not self.title.strip():
            raise ValueError(f"Title cannot be empty for WO: {self.id}")

        # Validate no self-dependencies
        if self.id in self.dependencies:
            raise ValueError(f"WO cannot depend on itself: {self.id} has self-dependency")

        # Validate temporal consistency: if RUNNING, must have started_at
        if self.status == WOState.RUNNING and self.started_at is None:
            raise ValueError(f"WO {self.id} has status RUNNING but no started_at timestamp")

        # Validate temporal consistency: if DONE/FAILED/PARTIAL, must have finished_at
        if self.status in (WOState.DONE, WOState.FAILED, WOState.PARTIAL):
            if self.finished_at is None:
                raise ValueError(f"WO {self.id} has status {self.status.value} but no finished_at timestamp")
            # Ensure finished_at is after started_at
            if self.started_at and self.finished_at < self.started_at:
                raise ValueError(
                    f"WO {self.id} finished_at ({self.finished_at}) is before started_at ({self.started_at})"
                )

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
