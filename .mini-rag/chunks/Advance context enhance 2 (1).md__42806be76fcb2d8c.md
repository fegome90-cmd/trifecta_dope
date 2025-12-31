### Phase gates

**Phase 1 (MVP)**: Schema v1 + fence-aware chunking + stable IDs + `ctx.search`/`ctx.get` + validation

**Phase 2 (Incremental)**: SQLite backend + incremental ingestion by sha256 + FTS5/BM25 search

**Phase 3 (AST/LSP)**: Skeleton + symbols + diagnostics + `get_symbol`/`get_window` modes

Don’t move to the next phase until metrics prove the current phase works.
