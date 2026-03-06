import sqlite3
import tempfile
from pathlib import Path
from src.platform.repo_store import RepoStore
import pytest


def test_new_db_has_schema_version_1():
    """Test that a new DB is created with schema_version=1."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        db_path = temp_path / "test.db"

        store = RepoStore(db_path)

        conn = sqlite3.connect(db_path)
        cur = conn.execute("SELECT version FROM schema_version")
        row = cur.fetchone()
        conn.close()

        assert row is not None
        assert row[0] == 1


def test_db_without_schema_version_fails_closed():
    """Test that DB without schema_version table fails with explicit error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        db_path = temp_path / "test.db"

        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE repos ("
            "repo_id TEXT PRIMARY KEY, "
            "root_path TEXT NOT NULL, "
            "created_at TEXT NOT NULL, "
            "last_accessed TEXT"
            ")"
        )
        conn.commit()
        conn.close()

        with pytest.raises(RuntimeError, match="schema version mismatch: expected 1, got none"):
            RepoStore(db_path)


def test_db_with_wrong_schema_version_fails_closed():
    """Test that DB with wrong schema_version fails with explicit error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        db_path = temp_path / "test.db"

        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE repos ("
            "repo_id TEXT PRIMARY KEY, "
            "root_path TEXT NOT NULL, "
            "created_at TEXT NOT NULL, "
            "last_accessed TEXT"
            ")"
        )
        conn.execute("CREATE TABLE schema_version (version INTEGER)")
        conn.execute("INSERT INTO schema_version VALUES (2)")
        conn.commit()
        conn.close()

        with pytest.raises(RuntimeError, match="schema version mismatch: expected 1, got 2"):
            RepoStore(db_path)
