"""Unit tests for path conversion logic in ctx_wo_take.py."""

import tempfile
from pathlib import Path
import os
import shutil
import subprocess

import yaml

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
            assert relative.startswith(expected_prefix), (
                f"For {repo_rel}, expected prefix {expected_prefix}, got {relative}"
            )


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


def _prepare_ctx_sandbox(tmp_path: Path) -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    fixture_root = repo_root / "tests" / "fixtures" / "ctx"
    sandbox_root = tmp_path / "ctx"
    shutil.copytree(fixture_root, sandbox_root)

    subprocess.run(["git", "init"], cwd=sandbox_root, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=sandbox_root,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=sandbox_root,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "checkout", "-b", "main"],
        cwd=sandbox_root,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "add", "."], cwd=sandbox_root, check=True, capture_output=True, text=True
    )
    subprocess.run(
        ["git", "commit", "-m", "fixture baseline"],
        cwd=sandbox_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return sandbox_root


def _run_take(repo_root: Path, sandbox_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python", "scripts/ctx_wo_take.py", *args, "--root", str(sandbox_root)],
        capture_output=True,
        text=True,
        check=False,
        cwd=repo_root,
    )


def test_take_fails_immediate_validation_for_semantic_error(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    sandbox_root = _prepare_ctx_sandbox(tmp_path)
    wo_path = sandbox_root / "_ctx" / "jobs" / "pending" / "WO-0001.yaml"
    wo_data = yaml.safe_load(wo_path.read_text(encoding="utf-8"))
    wo_data["status"] = "running"
    wo_path.write_text(yaml.safe_dump(wo_data, sort_keys=False), encoding="utf-8")

    result = _run_take(repo_root, sandbox_root, "WO-0001")
    output = result.stdout + result.stderr

    assert result.returncode == 1
    assert "Immediate WO validation failed for WO-0001" in output
    assert (sandbox_root / "_ctx" / "jobs" / "pending" / "WO-0001.yaml").exists()
    assert not (sandbox_root / "_ctx" / "jobs" / "running" / "WO-0001.yaml").exists()
    assert not (sandbox_root / "_ctx" / "jobs" / "running" / "WO-0001.lock").exists()


def test_take_fails_immediate_validation_for_schema_error_even_with_force(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    sandbox_root = _prepare_ctx_sandbox(tmp_path)
    wo_path = sandbox_root / "_ctx" / "jobs" / "pending" / "WO-0001.yaml"
    wo_data = yaml.safe_load(wo_path.read_text(encoding="utf-8"))
    wo_data.pop("dod_id", None)
    wo_path.write_text(yaml.safe_dump(wo_data, sort_keys=False), encoding="utf-8")

    result = _run_take(repo_root, sandbox_root, "WO-0001", "--force")
    output = result.stdout + result.stderr

    assert result.returncode == 1
    assert (
        "Schema validation failed" in output
        or "Immediate WO validation failed for WO-0001" in output
    )
    assert (sandbox_root / "_ctx" / "jobs" / "pending" / "WO-0001.yaml").exists()
    assert not (sandbox_root / "_ctx" / "jobs" / "running" / "WO-0001.yaml").exists()
    assert not (sandbox_root / "_ctx" / "jobs" / "running" / "WO-0001.lock").exists()
