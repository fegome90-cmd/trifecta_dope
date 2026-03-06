import pytest
from pathlib import Path
import tempfile
import shutil
from src.platform.repo_store import RepoStore, RepoRecord


class TestRepoStore:
    @pytest.fixture
    def temp_dir(self):
        tmp = Path(tempfile.mkdtemp())
        yield tmp
        shutil.rmtree(tmp)

    @pytest.fixture
    def store(self, temp_dir):
        db_path = temp_dir / "test.db"
        return RepoStore(db_path)

    def test_add_and_get(self, store):
        record = store.add("test-repo-123", Path("/tmp/test"))
        assert record.repo_id == "test-repo-123"
        assert record.root_path == Path("/tmp/test")

        retrieved = store.get("test-repo-123")
        assert retrieved is not None
        assert retrieved.repo_id == "test-repo-123"

    def test_list_all(self, store):
        store.add("repo-1", Path("/tmp/repo1"))
        store.add("repo-2", Path("/tmp/repo2"))

        repos = store.list_all()
        assert len(repos) == 2

    def test_delete(self, store):
        store.add("to-delete", Path("/tmp/delete"))
        assert store.get("to-delete") is not None

        deleted = store.delete("to-delete")
        assert deleted is True
        assert store.get("to-delete") is None
