import os
from pathlib import Path
import pytest
from src.domain.segment_resolver import get_repo_root, get_home_path

def test_get_repo_root_finds_pyproject(tmp_path):
    """Should find the repo root where pyproject.toml exists."""
    repo_root = (tmp_path / "repo").resolve()
    repo_root.mkdir()
    (repo_root / "pyproject.toml").touch()
    
    sub_dir = repo_root / "src" / "sub"
    sub_dir.mkdir(parents=True)
    
    # We need to monkeypatch CWD to the sub_dir
    original_cwd = os.getcwd()
    os.chdir(sub_dir)
    try:
        resolved = get_repo_root()
        assert resolved == repo_root
    finally:
        os.chdir(original_cwd)

def test_get_repo_root_falls_back_to_cwd_if_not_found(tmp_path):
    """Should return resolved CWD if no pyproject.toml is found up the tree."""
    empty_dir = (tmp_path / "empty").resolve()
    empty_dir.mkdir()
    
    original_cwd = os.getcwd()
    os.chdir(empty_dir)
    try:
        resolved = get_repo_root()
        assert resolved == empty_dir
    finally:
        os.chdir(original_cwd)

def test_get_home_path_default():
    """Should return current user home by default."""
    assert get_home_path() == Path.home()

def test_get_home_path_override(monkeypatch, tmp_path):
    """Should allow override via TRIFECTA_HOME."""
    fake_home = (tmp_path / "fake_home").resolve()
    fake_home.mkdir()
    monkeypatch.setenv("TRIFECTA_HOME", str(fake_home))
    assert get_home_path() == fake_home

def test_repo_root_fixture(repo_root):
    """RED: Verify repo_root fixture returns a Path and points to current repo."""
    assert isinstance(repo_root, Path)
    assert (repo_root / "pyproject.toml").exists()

def test_fake_home_fixture(fake_home):
    """RED: Verify fake_home fixture isolates HOME environment."""
    home = Path.home().resolve()
    assert home == fake_home.resolve()
    # Check if we can create a file there
    test_file = fake_home / "test.txt"
    test_file.write_text("hello")
    assert test_file.exists()
