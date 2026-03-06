import tempfile
from pathlib import Path
from src.platform.repo_store import RepoStore


def test_cross_repo_isolation():
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        store = RepoStore(temp_path / "repos.db")
        repos = []

        for i in range(3):
            repo_dir = temp_path / f"repo_{i}"
            repo_dir.mkdir(parents=True, exist_ok=True)
            record = store.add(f"repo_{i}", repo_dir)
            repos.append(record)

        all_repos = store.list_all()
        assert len(all_repos) == 3

        for i in range(3):
            entry = store.get(f"repo_{i}")
            assert entry is not None
            assert entry.repo_id == f"repo_{i}"

        repo_ids = [r.repo_id for r in repos]
        assert len(set(repo_ids)) == 3
