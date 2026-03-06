import pytest
import tempfile
import shutil
from pathlib import Path
from src.platform.repo_store import RepoStore
from src.platform.contracts import compute_repo_id, get_repo_runtime_dir


class TestRepoStoreIdempotence:
    @pytest.fixture
    def temp_dir(self):
        tmp = Path(tempfile.mkdtemp())
        yield tmp
        shutil.rmtree(tmp)

    @pytest.fixture
    def store(self, temp_dir):
        db_path = temp_dir / "test.db"
        return RepoStore(db_path)

    def test_add_idempotent(self, store):
        path = Path("/tmp/test-idempotent")
        record1 = store.add("repo-idempotent", path)
        assert record1.repo_id == "repo-idempotent"

        record2 = store.add("repo-idempotent", path)
        assert record2.repo_id == "repo-idempotent"

        repos = store.list_all()
        assert len(repos) == 1

    def test_double_delete(self, store):
        store.add("to-delete", Path("/tmp/delete"))
        deleted1 = store.delete("to-delete")
        assert deleted1 is True

        deleted2 = store.delete("to-delete")
        assert deleted2 is False


class TestRepoStoreEdgeCases:
    @pytest.fixture
    def temp_dir(self):
        tmp = Path(tempfile.mkdtemp())
        yield tmp
        shutil.rmtree(tmp)

    @pytest.fixture
    def store(self, temp_dir):
        db_path = temp_dir / "test.db"
        return RepoStore(db_path)

    def test_get_nonexistent(self, store):
        result = store.get("nonexistent")
        assert result is None


class TestSecurityValidation:
    def test_invalid_repo_id_with_slash(self):
        with pytest.raises(ValueError, match="Invalid repo_id"):
            get_repo_runtime_dir("repo/with/slash")

    def test_invalid_repo_id_with_backslash(self):
        with pytest.raises(ValueError, match="Invalid repo_id"):
            get_repo_runtime_dir("repo\\with\\backslash")

    def test_invalid_repo_id_with_dotdot(self):
        with pytest.raises(ValueError, match="Invalid repo_id"):
            get_repo_runtime_dir("repo/../etc")

    def test_valid_repo_id(self):
        result = get_repo_runtime_dir("valid_repo_id")
        assert "valid_repo_id" in str(result)

    def test_compute_repo_id_stable(self):
        path1 = Path("/tmp/test-repo")
        id1 = compute_repo_id(path1)

        id2 = compute_repo_id(path1)
        assert id1 == id2

        id3 = compute_repo_id(path1.resolve())
        assert id1 == id3
