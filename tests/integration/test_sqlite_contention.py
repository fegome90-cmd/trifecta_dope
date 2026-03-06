import sqlite3
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.platform.repo_store import RepoStore
import pytest


def test_concurrent_writers_no_corruption():
    """Test that N concurrent writers complete without corruption."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        db_path = temp_path / "test.db"

        store = RepoStore(db_path)
        num_writers = 10
        successful_writes = []
        failed_writes = []

        def writer(writer_id: int):
            try:
                repo_dir = temp_path / f"repo_{writer_id}"
                repo_dir.mkdir(parents=True, exist_ok=True)
                record = store.add(f"repo_{writer_id}", repo_dir)
                return (True, writer_id, record)
            except Exception as e:
                return (False, writer_id, str(e))

        with ThreadPoolExecutor(max_workers=num_writers) as executor:
            futures = [executor.submit(writer, i) for i in range(num_writers)]
            for future in as_completed(futures):
                success, writer_id, result = future.result()
                if success:
                    successful_writes.append((writer_id, result))
                else:
                    failed_writes.append((writer_id, result))

        all_repos = store.list_all()

        assert len(all_repos) == num_writers, f"Expected {num_writers} repos, got {len(all_repos)}"

        repo_ids = [r.repo_id for r in all_repos]
        assert len(set(repo_ids)) == num_writers, "Duplicate repo_ids found"

        for repo in all_repos:
            retrieved = store.get(repo.repo_id)
            assert retrieved is not None
            assert retrieved.repo_id == repo.repo_id
            assert retrieved.root_path == repo.root_path


def test_contention_policy_documented():
    """Test that SQLite handles contention via serialization (Option B)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        db_path = temp_path / "test.db"

        store = RepoStore(db_path)

        repo_dir = temp_path / "shared_repo"
        repo_dir.mkdir(parents=True, exist_ok=True)

        num_writers = 5
        successful_writes = []

        def writer_same_path(writer_id: int):
            try:
                record = store.add(f"repo_{writer_id}", repo_dir)
                return (True, writer_id, record)
            except ValueError as e:
                return (False, writer_id, str(e))

        with ThreadPoolExecutor(max_workers=num_writers) as executor:
            futures = [executor.submit(writer_same_path, i) for i in range(num_writers)]
            for future in as_completed(futures):
                success, writer_id, result = future.result()
                if success:
                    successful_writes.append((writer_id, result))

        assert len(successful_writes) >= 1, "At least one writer should succeed"

        all_repos = store.list_all()
        unique_paths = set(r.root_path for r in all_repos)
        assert len(unique_paths) == 1, "All repos should have the same canonical path"


def test_database_integrity_after_contention():
    """Test that DB integrity is maintained after concurrent writes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        db_path = temp_path / "test.db"

        store = RepoStore(db_path)
        num_writers = 20

        def writer(writer_id: int):
            repo_dir = temp_path / f"repo_{writer_id}"
            repo_dir.mkdir(parents=True, exist_ok=True)
            return store.add(f"repo_{writer_id}", repo_dir)

        with ThreadPoolExecutor(max_workers=num_writers) as executor:
            futures = [executor.submit(writer, i) for i in range(num_writers)]
            for future in as_completed(futures):
                future.result()

        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA integrity_check")
        result = conn.execute("PRAGMA integrity_check").fetchone()
        conn.close()

        assert result[0] == "ok", f"DB integrity check failed: {result[0]}"

        all_repos = store.list_all()
        assert len(all_repos) == num_writers

        for repo in all_repos:
            assert repo.repo_id is not None
            assert repo.root_path is not None
            assert repo.created_at is not None
