## Phase 2: SQLite (Futuro)

Cuando el context pack crezca, migrar chunks a SQLite:

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

**Beneficios**:
- Búsqueda O(1) por ID
- Soporte para miles de chunks
- Preparado para full-text search (BM25)
