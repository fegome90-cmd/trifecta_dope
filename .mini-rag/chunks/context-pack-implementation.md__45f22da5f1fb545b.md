# Should only have: Intro, Middle, End
    assert "Intro" in chunk_titles
    assert "Middle" in chunk_titles
    assert "End" in chunk_titles
    assert "Inside fence should not split" not in chunk_titles
```

---

## Métricas de Producción

### debug_terminal (Real)

```bash
$ python scripts/ingest_trifecta.py --segment debug_terminal
[ok] Context Pack generated:
    • 34 chunks
    • 5 digest entries
    • 34 index entries
    → /Users/felipe_gonzalez/Developer/agent_h/debug_terminal/_ctx/context_pack.json
```

### Digest Output
 - Ideas Avanzadas)

> **💡 Idea Original para Escalabilidad**
>
> Esta sección describe una **propuesta futura** para cuando el context pack crezca.
> Actualmente (v1.0), usamos JSON simple que funciona bien para <100 chunks.
>
> **Estado actual**: JSON en `_ctx/context_pack.json`  
> **Roadmap**: SQLite cuando superemos ~200 chunks o necesitemos búsqueda compleja

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
