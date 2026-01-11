"""
Tests for WO domain entities business logic.
Pure domain logic - no mocks, no IO.
"""
import pytest
from datetime import datetime, timezone


class TestWOStateTransitions:
    """Test WO state transition validation."""

    def test_pending_to_running_valid(self):
        from src.domain.wo_entities import WorkOrder, WOState
        wo = WorkOrder(
            id="WO-0001", epic_id="E-0001", title="Test", priority="P2",
            status=WOState.PENDING, owner=None, dod_id="DOD-DEFAULT",
            dependencies=[], started_at=None, finished_at=None,
            branch=None, worktree=None
        )
        result = wo.can_transition_to(WOState.RUNNING)
        assert result.is_ok()

    def test_invalid_transition_fails(self):
        from src.domain.wo_entities import WorkOrder, WOState
        wo = WorkOrder(
            id="WO-0001", epic_id="E-0001", title="Test", priority="P2",
            status=WOState.DONE, owner=None, dod_id="DOD-DEFAULT",
            dependencies=[], started_at=None, finished_at=None,
            branch=None, worktree=None
        )
        result = wo.can_transition_to(WOState.PENDING)
        assert result.is_err()
        error = result.unwrap_err()
        assert error.code == "INVALID_STATE_TRANSITION"
