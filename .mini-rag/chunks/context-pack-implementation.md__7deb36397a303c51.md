-- Futuro: Full-text search
CREATE VIRTUAL TABLE chunks_fts USING fts5(
    id UNINDEXED,
    title_path,
    text,
    content='chunks',
    content_rowid='rowid'
);
```

**Beneficios**:
- Búsqueda O(1) por ID
- Soporte para miles de chunks sin degradación
- Full-text search con BM25 (mejor que grep)
- Query optimization automático
- Preparado para embedding vectors (futuro v2.0)

**Decisiones de Diseño a Tomar**:
- ¿Mantener JSON como fallback? (para portabilidad)
- ¿Migrar índice también a SQLite o solo chunks?
- ¿Usar SQLite en memoria para queries frecuentes?

**Referencias**:
- Ver `docs/research/braindope.md` para ideas de Progressive Disclosure
- Relacionado con v2.0 roadmap (embeddings + reranking
## Index (Available Sections)
{format_index(context_pack['index'])}

To get full content of any section, use: get_context(chunk_id)
"""
```
