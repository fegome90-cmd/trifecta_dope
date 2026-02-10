"""Unit tests for path conversion logic in ctx_wo_take.py."""
import tempfile
from pathlib import Path
import os

from scripts.paths import get_worktree_path


def test_worktree_relative_path_conversion():
    """Test conversion from absolute to relative path for git commands."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir) / "repo"
        repo_root.mkdir()

        # Simulate the path conversion logic
        auto_worktree = get_worktree_path(repo_root, "WO-0001")

        # Test relative path calculation (same as ctx_wo_take.py line 302)
        worktree = os.path.relpath(auto_worktree, repo_root)

        # Should be "../.worktrees/WO-0001"
        assert worktree == "../.worktrees/WO-0001"


def test_worktree_relative_path_nested_repo():
    """Test relative path when repo is in nested directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Repo at /tmp/test/deep/repo
        repo_root = Path(tmpdir) / "test" / "deep" / "repo"
        repo_root.mkdir(parents=True)

        auto_worktree = get_worktree_path(repo_root, "WO-0001")
        worktree = os.path.relpath(auto_worktree, repo_root)

        # Worktree is at /tmp/test/deep/.worktrees/WO-0001 (sibling of repo)
        # Relative to /tmp/test/deep/repo: ../.worktrees/WO-0001
        assert worktree == "../.worktrees/WO-0001"


def test_worktree_relative_path_depth_variation():
    """Test relative paths with different nesting depths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        test_cases = [
            ("repo", "../.worktrees"),
            ("a/repo", "../.worktrees"),
            ("a/b/repo", "../.worktrees"),
            ("a/b/c/repo", "../.worktrees"),
        ]

        for repo_rel, expected_prefix in test_cases:
            repo_root = base / repo_rel
            repo_root.mkdir(parents=True)

            worktree_path = get_worktree_path(repo_root, "WO-TEST")
            relative = os.path.relpath(worktree_path, repo_root)

            # Worktree is always at sibling level (repo_root.parent/.worktrees/)
            # So relative path is always ../.worktrees/
            assert relative.startswith(expected_prefix), \
                f"For {repo_rel}, expected prefix {expected_prefix}, got {relative}"


def test_worktree_absolute_to_roundtrip():
    """Test that relative path can be converted back to absolute."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir) / "repo"
        repo_root.mkdir()

        auto_worktree = get_worktree_path(repo_root, "WO-0001")
        relative_path = os.path.relpath(auto_worktree, repo_root)

        # Roundtrip: relative -> absolute using repo_root
        reconstructed = (repo_root / relative_path).resolve()
        
        # Should match the original worktree path
        assert reconstructed == auto_worktree.resolve()
