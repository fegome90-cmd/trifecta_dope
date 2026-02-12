"""Unit tests for scripts.paths module."""

import tempfile
from pathlib import Path
import pytest
import os

from scripts.paths import get_worktree_path


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


def test_get_worktree_path_parent_not_exists():
    """Test that FileNotFoundError is raised when parent doesn't exist."""
    # Create a scenario where parent doesn't exist
    # Use a non-existent path inside temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a deep path that doesn't exist
        non_existent = Path(tmpdir) / "does" / "not" / "exist" / "repo"

        with pytest.raises(FileNotFoundError) as exc_info:
            get_worktree_path(non_existent, "WO-0001")

        assert "parent directory does not exist" in str(exc_info.value)


def test_get_worktree_path_parent_not_writable(monkeypatch):
    """Test that PermissionError is raised when parent is not writable."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir) / "repo"
        repo_root.mkdir()

        # Mock os.access to return False for write permission
        def mock_access(path, mode):
            if path == repo_root.parent and mode == os.W_OK:
                return False
            return True

        monkeypatch.setattr(os, "access", mock_access)

        with pytest.raises(PermissionError) as exc_info:
            get_worktree_path(repo_root, "WO-0001")

        assert "not writable" in str(exc_info.value)


def test_get_worktree_path_repo_at_filesystem_root():
    """Test edge case: repo at filesystem root (no parent)."""
    # This is a rare edge case - repo at / (filesystem root)
    # In this case, parent would be / which should exist
    repo_root = Path("/")

    # This should not raise, since / exists
    # Note: may fail with PermissionError in actual tests since / is not writable
    with pytest.raises(PermissionError):
        get_worktree_path(repo_root, "WO-0001")
