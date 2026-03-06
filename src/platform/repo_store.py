import sqlite3
import datetime
from dataclasses import dataclass
from datetime import timezone
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class RepoRecord:
    repo_id: str
    root_path: Path
    created_at: str
    last_accessed: Optional[str] = None


class RepoStore:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._db_path)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS repos ("
            "repo_id TEXT PRIMARY KEY, "
            "root_path TEXT NOT NULL, "
            "created_at TEXT NOT NULL, "
            "last_accessed TEXT"
            ")"
        )
        conn.commit()
        conn.close()

    def add(self, repo_id: str, root_path: Path) -> RepoRecord:
        canonical_path = Path(root_path).resolve()
        now = datetime.datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(self._db_path)
        existing = conn.execute(
            "SELECT root_path FROM repos WHERE root_path = ?", (str(canonical_path),)
        )
        if existing.fetchone():
            conn.close()
            raise ValueError(f"repo already registered at {canonical_path}")
        conn.execute(
            "INSERT OR REPLACE INTO repos (repo_id, root_path, created_at, last_accessed) VALUES (?, ?, ?, ?)",
            (repo_id, str(canonical_path), now, now),
        )
        conn.commit()
        conn.close()
        return RepoRecord(
            repo_id=repo_id, root_path=canonical_path, created_at=now, last_accessed=now
        )

    def get(self, repo_id: str) -> Optional[RepoRecord]:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT * FROM repos WHERE repo_id = ?", (repo_id,))
        row = cur.fetchone()
        conn.close()
        if row is None:
            return None
        return RepoRecord(
            repo_id=row["repo_id"],
            root_path=Path(row["root_path"]),
            created_at=row["created_at"],
            last_accessed=row["last_accessed"],
        )

    def list_all(self) -> list[RepoRecord]:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT * FROM repos ORDER BY last_accessed DESC")
        rows = cur.fetchall()
        conn.close()
        return [
            RepoRecord(
                repo_id=row["repo_id"],
                root_path=Path(row["root_path"]),
                created_at=row["created_at"],
                last_accessed=row["last_accessed"],
            )
            for row in rows
        ]

    def delete(self, repo_id: str) -> bool:
        conn = sqlite3.connect(self._db_path)
        cur = conn.execute("DELETE FROM repos WHERE repo_id = ?", (repo_id,))
        conn.commit()
        deleted = cur.rowcount > 0
        conn.close()
        return deleted
