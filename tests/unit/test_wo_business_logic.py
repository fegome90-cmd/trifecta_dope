"""
Tests for WO domain entities business logic.
Pure domain logic - no mocks, no IO.
"""
import pytest
from datetime import datetime, timezone

from src.domain.wo_entities import WorkOrder, WOState, Priority


class TestWOStateTransitions:
    """Test WO state transition validation."""

    def test_pending_to_running_valid(self):
        wo = WorkOrder(
            id="WO-0001", epic_id="E-0001", title="Test", priority=Priority.MEDIUM,
            status=WOState.PENDING, owner=None, dod_id="DOD-DEFAULT",
            dependencies=(), started_at=None, finished_at=None,
            branch=None, worktree=None
        )
        result = wo.can_transition_to(WOState.RUNNING)
        assert result.is_ok()

    def test_invalid_transition_fails(self):
        now = datetime.now(timezone.utc)
        wo = WorkOrder(
            id="WO-0001", epic_id="E-0001", title="Test", priority=Priority.MEDIUM,
            status=WOState.DONE, owner=None, dod_id="DOD-DEFAULT",
            dependencies=(), started_at=now, finished_at=now,
            branch=None, worktree=None
        )
        result = wo.can_transition_to(WOState.PENDING)
        assert result.is_err()
        error = result.unwrap_err()
        assert error.code == "INVALID_STATE_TRANSITION"


class TestWODependencyValidation:
    """Test dependency validation logic."""

    def test_no_dependencies_always_valid(self):
        wo = WorkOrder(
            id="WO-0001", epic_id="E-0001", title="Test", priority=Priority.MEDIUM,
            status=WOState.PENDING, owner=None, dod_id="DOD-DEFAULT",
            dependencies=(), started_at=None, finished_at=None,
            branch=None, worktree=None
        )
        result = wo.validate_dependencies(set())
        assert result.is_ok()

    def test_unsatisfied_dependencies_invalid(self):
        wo = WorkOrder(
            id="WO-0001", epic_id="E-0001", title="Test", priority=Priority.MEDIUM,
            status=WOState.PENDING, owner=None, dod_id="DOD-DEFAULT",
            dependencies=("WO-0002", "WO-0003"), started_at=None, finished_at=None,
            branch=None, worktree=None
        )
        result = wo.validate_dependencies({"WO-0002"})
        assert result.is_err()
        error = result.unwrap_err()
        assert error.code == "UNSATISFIED_DEPENDENCIES"

    def test_satisfied_dependencies_valid(self):
        wo = WorkOrder(
            id="WO-0001", epic_id="E-0001", title="Test", priority=Priority.MEDIUM,
            status=WOState.PENDING, owner=None, dod_id="DOD-DEFAULT",
            dependencies=("WO-0002", "WO-0003"), started_at=None, finished_at=None,
            branch=None, worktree=None
        )
        result = wo.validate_dependencies({"WO-0002", "WO-0003"})
        assert result.is_ok()


class TestWOStaleDetection:
    """Test stale WO detection."""

    def test_non_running_wo_never_stale(self):
        wo = WorkOrder(
            id="WO-0001", epic_id="E-0001", title="Test", priority=Priority.MEDIUM,
            status=WOState.PENDING, owner=None, dod_id="DOD-DEFAULT",
            dependencies=(), started_at=None, finished_at=None,
            branch=None, worktree=None
        )
        assert not wo.is_stale(max_age_seconds=0)

    def test_running_wo_not_stale(self):
        wo = WorkOrder(
            id="WO-0001", epic_id="E-0001", title="Test", priority=Priority.MEDIUM,
            status=WOState.RUNNING, owner=None, dod_id="DOD-DEFAULT",
            dependencies=(), started_at=datetime.now(timezone.utc), finished_at=None,
            branch=None, worktree=None
        )
        assert not wo.is_stale(max_age_seconds=3600)

    def test_running_wo_is_stale(self):
        # Create a WO started 2 hours ago
        started = datetime.now(timezone.utc).timestamp() - 7200
        wo = WorkOrder(
            id="WO-0001", epic_id="E-0001", title="Test", priority=Priority.MEDIUM,
            status=WOState.RUNNING, owner=None, dod_id="DOD-DEFAULT",
            dependencies=(), started_at=datetime.fromtimestamp(started, tz=timezone.utc),
            finished_at=None, branch=None, worktree=None
        )
        assert wo.is_stale(max_age_seconds=3600)
