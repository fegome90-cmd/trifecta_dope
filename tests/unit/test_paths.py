"""Unit tests for scripts.paths module."""
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch

from scripts.paths import (
    get_worktree_path,
    get_lock_path,
    get_wo_pending_path,
    get_wo_running_path,
    get_wo_done_path,
    get_wo_failed_path,
    get_branch_name,
    validate_wo_paths,
    ensure_wo_directories,
    PathValidationResult,
)


def test_get_worktree_path_outside_repo():
    """Test that worktrees are created outside the repository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Simulate repo at /tmp/test_repo
        repo_root = Path(tmpdir) / "test_repo"
        repo_root.mkdir()

        # Worktree should be at /tmp/.worktrees/WO-0001
        worktree_path = get_worktree_path(repo_root, "WO-0001")
        expected = Path(tmpdir) / ".worktrees" / "WO-0001"

        assert worktree_path == expected
        # Verify worktree is NOT inside repo
        assert not worktree_path.is_relative_to(repo_root)


def test_get_worktree_path_multiple_wos():
    """Test that multiple WO paths are correctly generated."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir) / "repo"
        repo_root.mkdir()

        wo_ids = ["WO-0001", "WO-0002", "WO-0018A"]
        for wo_id in wo_ids:
            path = get_worktree_path(repo_root, wo_id)
            assert path == Path(tmpdir) / ".worktrees" / wo_id
            assert not path.is_relative_to(repo_root)


def test_get_worktree_path_mkdir_fails():
    """Test that PermissionError is raised when .worktrees cannot be created."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir) / "repo"
        repo_root.mkdir()

        # Mock Path.mkdir to raise OSError (simulates permission denied)
        with patch.object(Path, 'mkdir', side_effect=OSError("[Errno 13] Permission denied")):
            with pytest.raises(PermissionError, match="Cannot create .worktrees directory"):
                get_worktree_path(repo_root, "WO-0001")


def test_get_worktree_path_creates_dotworktrees():
    """Test that .worktrees directory is created when calling get_worktree_path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir) / "repo"
        repo_root.mkdir()

        worktrees_dir = Path(tmpdir) / ".worktrees"

        # Verify .worktrees doesn't exist initially
        assert not worktrees_dir.exists()

        # Call get_worktree_path - should create .worktrees
        worktree_path = get_worktree_path(repo_root, "WO-0001")

        # Verify .worktrees was created
        assert worktrees_dir.exists()
        assert worktree_path == worktrees_dir / "WO-0001"


def test_get_worktree_path_parent_missing():
    """Test that FileNotFoundError is raised when parent doesn't exist."""
    # Create a path where parent doesn't exist (in a temp dir that we won't create)
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a non-existent parent path
        nonexistent_repo = Path(tmpdir) / "nonexistent" / "repo"

        with pytest.raises(FileNotFoundError, match="parent directory does not exist"):
            get_worktree_path(nonexistent_repo, "WO-0001")


def test_get_lock_path():
    """Test lock path generation."""
    repo_root = Path("/dev/repo")
    lock_path = get_lock_path(repo_root, "WO-0001")
    expected = Path("/dev/repo/_ctx/jobs/running/WO-0001.lock")
    assert lock_path == expected


def test_get_wo_pending_path():
    """Test pending WO path generation."""
    repo_root = Path("/dev/repo")
    wo_path = get_wo_pending_path(repo_root, "WO-0001")
    expected = Path("/dev/repo/_ctx/jobs/pending/WO-0001.yaml")
    assert wo_path == expected


def test_get_wo_running_path():
    """Test running WO path generation."""
    repo_root = Path("/dev/repo")
    wo_path = get_wo_running_path(repo_root, "WO-0001")
    expected = Path("/dev/repo/_ctx/jobs/running/WO-0001.yaml")
    assert wo_path == expected


def test_get_wo_done_path():
    """Test done WO path generation."""
    repo_root = Path("/dev/repo")
    wo_path = get_wo_done_path(repo_root, "WO-0001")
    expected = Path("/dev/repo/_ctx/jobs/done/WO-0001.yaml")
    assert wo_path == expected


def test_get_wo_failed_path():
    """Test failed WO path generation."""
    repo_root = Path("/dev/repo")
    wo_path = get_wo_failed_path(repo_root, "WO-0001")
    expected = Path("/dev/repo/_ctx/jobs/failed/WO-0001.yaml")
    assert wo_path == expected


def test_get_branch_name():
    """Test branch name generation."""
    assert get_branch_name("WO-0001") == "feat/wo-WO-0001"
    assert get_branch_name("WO-0018A") == "feat/wo-WO-0018A"


def test_validate_wo_paths_valid():
    """Test path validation with all directories present."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir) / "repo"
        ensure_wo_directories(repo_root)

        result = validate_wo_paths(repo_root, "WO-0001")
        assert result.is_valid
        assert result.error_message is None
        assert result.missing_paths == ()


def test_validate_wo_paths_missing():
    """Test path validation with missing directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir) / "repo"
        repo_root.mkdir()
        # Create _ctx/jobs but not state directories
        (repo_root / "_ctx" / "jobs").mkdir(parents=True)

        result = validate_wo_paths(repo_root, "WO-0001")
        assert not result.is_valid
        assert result.error_message is not None
        assert len(result.missing_paths) == 4  # pending, running, done, failed


def test_ensure_wo_directories():
    """Test that ensure_wo_directories creates missing directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir) / "repo"
        repo_root.mkdir()

        created = ensure_wo_directories(repo_root)

        # Should have created 5 directories
        assert len(created) == 5

        # Verify all directories exist
        assert (repo_root / "_ctx" / "jobs").exists()
        assert (repo_root / "_ctx" / "jobs" / "pending").exists()
        assert (repo_root / "_ctx" / "jobs" / "running").exists()
        assert (repo_root / "_ctx" / "jobs" / "done").exists()
        assert (repo_root / "_ctx" / "jobs" / "failed").exists()


def test_ensure_wo_directories_idempotent():
    """Test that ensure_wo_directories is idempotent."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir) / "repo"
        repo_root.mkdir()

        # First call creates directories
        created1 = ensure_wo_directories(repo_root)
        assert len(created1) == 5

        # Second call should create nothing
        created2 = ensure_wo_directories(repo_root)
        assert len(created2) == 0


def test_path_validation_result_valid():
    """Test PathValidationResult.valid() factory."""
    result = PathValidationResult.valid()
    assert result.is_valid
    assert result.error_message is None
    assert result.missing_paths == ()


def test_path_validation_result_invalid():
    """Test PathValidationResult.invalid() factory."""
    missing_paths = (Path("/a"), Path("/b"))
    result = PathValidationResult.invalid("Test error", *missing_paths)

    assert not result.is_valid
    assert result.error_message == "Test error"
    assert result.missing_paths == missing_paths
