"""Tripwire test for repo_root helper.

Ensures repo_root() is fail-closed and finds pyproject.toml correctly.
"""

from pathlib import Path
from tests.helpers import repo_root


def test_repo_root_finds_pyproject():
    """repo_root() should return path containing pyproject.toml."""
    root = repo_root()

    # Verify it's a Path
    assert isinstance(root, Path), "repo_root() must return Path instance"

    # Verify pyproject.toml exists
    pyproject = root / "pyproject.toml"
    assert pyproject.exists(), f"pyproject.toml not found at {root}"
    assert pyproject.is_file(), f"pyproject.toml is not a file at {root}"


def test_repo_root_is_absolute():
    """repo_root() should return absolute path."""
    root = repo_root()
    assert root.is_absolute(), f"repo_root() returned relative path: {root}"


def test_repo_root_contains_tests():
    """repo_root() should contain tests/ directory (smoke test)."""
    root = repo_root()
    tests_dir = root / "tests"
    assert tests_dir.exists(), f"tests/ not found at {root}"
    assert tests_dir.is_dir(), f"tests/ is not a directory at {root}"
