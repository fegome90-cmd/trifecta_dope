import sqlite3
from pathlib import Path


class IndexUseCase:
    def __init__(self, runtime_dir: Path) -> None:
        self._runtime_dir = runtime_dir
        self._search_db = runtime_dir / "search.db"

    def execute(self, segment_path: Path) -> dict:
        self._init_search_db()
        indexed_files = self._index_segment(segment_path)
        return {"status": "ok", "indexed": indexed_files}

    def _init_search_db(self) -> None:
        self._search_db.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._search_db)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS search_fts USING fts5(file, content, tokenize='porter')"
        )
        conn.commit()
        conn.close()

    def _index_segment(self, segment_path: Path) -> int:
        count = 0
        conn = sqlite3.connect(self._search_db)
        for py_file in segment_path.rglob("*.py"):
            if "_ctx" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                content = py_file.read_text(errors="ignore")
                conn.execute(
                    "INSERT INTO search_fts (file, content) VALUES (?, ?)",
                    (str(py_file), content),
                )
                count += 1
            except Exception:
                pass
        conn.commit()
        conn.close()
        return count
