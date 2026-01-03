#### 1. **Caching Local** (SQLite, no Redis)

**De**: orchestrator/redis-cache  
**Para Trifecta**: Cache incremental de chunks

```python
# _ctx/context.db (SQLite)
class ContextCache:
    def __init__(self, db_path: Path):
        self.db = sqlite3.connect(db_path)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS files (
                path TEXT PRIMARY KEY,
                sha256 TEXT,
                mtime REAL,
                chars INTEGER
            )
        """)

    def needs_rebuild(self, path: Path) -> bool:
        """Check if file changed since last ingest."""
        current_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        cached = self.db.execute(
            "SELECT sha256 FROM files WHERE path = ?",
            (str(path),)
        ).fetchone()
        return not cached or cached[0] != current_sha
```

**ROI**: Alto. Reduce tiempo de ingest, hace packs estables.

---
