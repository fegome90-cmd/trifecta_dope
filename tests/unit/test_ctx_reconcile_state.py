import subprocess
from pathlib import Path
from unittest.mock import patch
import sys

sys.path.insert(0, "scripts")

from ctx_reconcile_state import check_running_metadata


def test_reconcile_detects_running_without_lock():
    result = subprocess.run(
        ["python", "scripts/ctx_reconcile_state.py", "--fixtures", "running_without_lock"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "RUNNING_WITHOUT_LOCK" in result.stdout


def test_reconcile_detects_lock_without_running_wo():
    result = subprocess.run(
        ["python", "scripts/ctx_reconcile_state.py", "--fixtures", "lock_without_running_wo"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "LOCK_WITHOUT_RUNNING_WO" in result.stdout


def test_reconcile_detects_running_wo_without_worktree():
    result = subprocess.run(
        ["python", "scripts/ctx_reconcile_state.py", "--fixtures", "running_wo_without_worktree"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "RUNNING_WO_WITHOUT_WORKTREE" in result.stdout


def test_reconcile_apply_regenerates_lock_only_with_apply_flag():
    result = subprocess.run(
        ["python", "scripts/ctx_reconcile_state.py", "--fixtures", "running_without_lock"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "would_create_lock" in result.stdout


def test_reconcile_never_moves_states_without_force():
    result = subprocess.run(
        [
            "python",
            "scripts/ctx_reconcile_state.py",
            "--fixtures",
            "running_wo_without_worktree",
            "--apply",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "requires --force" in result.stdout


def test_reconcile_detects_duplicate_wo_id_across_states():
    result = subprocess.run(
        ["python", "scripts/ctx_reconcile_state.py", "--fixtures", "duplicate_wo_id_across_states"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "DUPLICATE_WO_ID" in result.stdout


def test_reconcile_detects_invalid_schema_and_refuses_apply():
    result = subprocess.run(
        ["python", "scripts/ctx_reconcile_state.py", "--fixtures", "invalid_schema"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "WO_INVALID_SCHEMA" in result.stdout

    result_apply = subprocess.run(
        ["python", "scripts/ctx_reconcile_state.py", "--fixtures", "invalid_schema", "--apply"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result_apply.returncode != 0
    assert "apply refused" in result_apply.stdout


def test_check_running_metadata_all_present():
    """WO with complete metadata returns None."""
    wo = {
        "id": "WO-0001",
        "status": "running",
        "owner": "testuser",
        "branch": "feat/wo-WO-0001",
        "worktree": ".worktrees/WO-0001",
        "started_at": "2026-01-13T12:00:00",
    }
    root = Path("/fake/root")
    issue = check_running_metadata(wo, Path("/fake/wo.yaml"), set(), root)
    assert issue is None


def test_check_running_metadata_missing_all_fields():
    """WO without metadata infers from system."""
    wo = {
        "id": "WO-0001",
        "status": "running",  # Has status, but missing other fields
        # Missing: owner, branch, worktree, started_at
    }
    root = Path("/fake/root")
    worktrees = {"/fake/root/.worktrees/WO-0001"}

    with (
        patch("scripts.metadata_inference.check_lock_validity") as mock_lock,
        patch("scripts.metadata_inference.get_worktrees_from_git") as mock_git,
    ):
        # Mock lock metadata
        mock_lock.return_value = (True, {"user": "testuser"})
        # Mock git worktrees
        mock_git.return_value = {
            "WO-0001": {
                "path": ".worktrees/WO-0001",
                "branch": "feat/wo-WO-0001",
                "commit": "abc123",
            }
        }

        # Create mock lock file
        with patch("scripts.metadata_inference.Path") as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.read_text.return_value = (
                "Locked by ctx_wo_take.py at 2026-01-13T12:00:00\nUser: testuser\n"
            )
            mock_path.return_value.stat.return_value.st_mtime = 1705166400

            issue = check_running_metadata(wo, Path("/fake/wo.yaml"), worktrees, root)

    assert issue is not None
    assert issue.code == "RUNNING_WITHOUT_METADATA"
    assert issue.wo_id == "WO-0001"
    assert issue.inferred is not None
    assert issue.inferred["owner"] == "testuser"
    assert issue.inferred["branch"] == "feat/wo-WO-0001"
    assert "started_at" in issue.inferred


def test_check_running_metadata_cannot_infer():
    """WO without metadata returns CANNOT_INFER_METADATA when inference fails."""
    wo = {
        "id": "WO-0001",
        "status": "pending",
    }
    root = Path("/fake/root")

    with (
        patch("scripts.metadata_inference.check_lock_validity") as mock_lock,
        patch("scripts.metadata_inference.get_worktrees_from_git") as mock_git,
    ):
        # Mock lock as invalid
        mock_lock.return_value = (False, None)
        # Mock git as empty
        mock_git.return_value = {}

        with patch("scripts.metadata_inference.Path") as mock_path:
            mock_path.return_value.exists.return_value = False

            issue = check_running_metadata(wo, Path("/fake/wo.yaml"), set(), root)

    assert issue is not None
    assert issue.code == "CANNOT_INFER_METADATA"
    assert issue.severity == "P1"
    assert issue.next_steps is not None
    assert len(issue.next_steps) > 0
