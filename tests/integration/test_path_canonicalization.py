import tempfile
from pathlib import Path
from src.platform.repo_store import RepoStore
import pytest


def test_symlink_equivalence():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        repo_dir = tmpdir_path / "my_repo"
        repo_dir.mkdir(parents=True, exist_ok=True)

        link_dir = tmpdir_path / "link_to_repo"
        link_dir.symlink_to(repo_dir)

        store = RepoStore(tmpdir_path / "test.db")
        store.add("repo-001", repo_dir)

        with pytest.raises(ValueError, match="repo already registered at"):
            store.add("repo-002", link_dir)


def test_relative_path_equivalence():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        repo_dir = tmpdir_path / "my_repo"
        repo_dir.mkdir(parents=True, exist_ok=True)

        relative_path = tmpdir_path / ".." / tmpdir_path.name / "my_repo"

        store = RepoStore(tmpdir_path / "test.db")
        store.add("repo-001", repo_dir)

        with pytest.raises(ValueError, match="repo already registered at"):
            store.add("repo-002", relative_path)


def test_duplicate_rejection():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        repo_dir = tmpdir_path / "my_repo"
        repo_dir.mkdir(parents=True, exist_ok=True)

        store = RepoStore(tmpdir_path / "test.db")
        record1 = store.add("repo-001", repo_dir)

        with pytest.raises(ValueError, match="repo already registered at"):
            store.add("repo-002", repo_dir)