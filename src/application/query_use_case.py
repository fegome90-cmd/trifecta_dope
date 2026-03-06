import sqlite3
from pathlib import Path


class QueryUseCase:
    def __init__(self, runtime_dir: Path) -> None:
        self._runtime_dir = runtime_dir
        self._search_db = runtime_dir / "search.db"

    def execute(self, query: str, limit: int = 10) -> dict:
        if not self._search_db.exists():
            return {"status": "error", "message": "No index found. Run index first."}
        conn = sqlite3.connect(self._search_db)
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT file, snippet(search_fts, 1, '<b>', '</b>', '...', 64) as snippet "
            "FROM search_fts WHERE search_fts MATCH ? ORDER BY rank LIMIT ?",
            (query, limit),
        )
        results = [dict(row) for row in cur.fetchall()]
        conn.close()
        return {"status": "ok", "query": query, "results": results, "count": len(results)}
