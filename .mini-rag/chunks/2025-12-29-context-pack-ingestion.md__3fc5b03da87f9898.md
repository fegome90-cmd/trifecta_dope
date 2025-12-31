## Phase 2: SQLite Runtime (Future)

When context packs grow large:

1. **`context.db`** (SQLite per project)
   ```sql
   CREATE TABLE chunks (
     id TEXT PRIMARY KEY,
     doc TEXT,
     title_path TEXT,
     text TEXT,
     source_path TEXT,
     heading_level INTEGER,
     char_count INTEGER,
     line_count INTEGER,
     start_line INTEGER,
     end_line INTEGER
   );
   CREATE INDEX idx_chunks_doc ON chunks(doc);
   CREATE INDEX idx_chunks_title_path ON chunks(title_path);
   ```

2. **Runtime Tools**
   - `get_context(id)` → O(1) lookup
   - `search_context(query, k)` → BM25 or full-text search

3. **JSON changes**
   - Keep `index` and metadata in JSON
   - Move `chunks.text` to SQLite (or separate files)

---
