# Exploration: WO-0043 Persistence Graph / Vector Store

## Current State
- **GraphStore EXISTS**: `src/infrastructure/graph_store.py` — full SQLite graph with nodes (function/class defs) + edges (calls/imports), per-segment isolation, fuzzy search, caller/callee traversal.
- **GraphIndexer EXISTS**: `src/application/graph_indexer.py` — builds graph from Python AST.
- **GraphService EXISTS**: `src/application/graph_service.py` — high-level API with status/search/callers/callees.
- **SQLiteCache EXISTS**: `src/domain/ast_cache.py` — LRU SQLite cache with protocol pattern (`AstCache`).
- **ContextService**: Keyword-based heuristic scoring (identity + body / log normalization). ~13ms latency. JSON+RAM authority.
- **SearchOracleUseCase**: Fuses PRIME + AST + (gated) LSP signals. **No graph or vector signal yet.**
- **NO vector/embedding infrastructure**: System explicitly avoids embeddings-first per README principles.
- **Storage deps**: Only `sqlite3` (stdlib) + `filelock`. No SQLAlchemy, no vector DBs.

## Affected Areas
- `src/infrastructure/graph_store.py` — Already has nodes/edges schema. May need enrichment (docstrings, type_refs).
- `src/application/graph_indexer.py` — Currently AST-only. Could extract richer relationships.
- `src/application/oracle_use_case.py` — Does NOT use graph signal. Natural integration point.
- `src/application/context_service.py` — Search scoring is heuristic keyword. Could add graph-awareness.
- `src/domain/graph_models.py` — `GraphNode`/`GraphEdge` frozen dataclasses. May need extension.
- `src/domain/ast_cache.py` — `AstCache` protocol pattern. Reusable for new store types.
- `src/infrastructure/factories.py` — Factory pattern for cache creation. Extend for vector store.

## Approaches

### 1. Extend GraphStore + Graph-Aware Oracle (Recommended)
Enrich existing graph (docstrings, type references, import chains) and wire GraphService into OracleUseCase as 4th signal.
- **Pros**: No new dependencies, leverages existing infrastructure, graph already works.
- **Cons**: Still keyword-based, no semantic search.
- **Effort**: Medium

### 2. SQLite Vector Extension (sqlean/vector)
Add embedding column to nodes, use SQLite vector extension for similarity search.
- **Pros**: Single DB, minimal new deps, SQLite-native.
- **Cons**: sqlean compilation complexity, embedding model dependency.
- **Effort**: Medium-High

### 3. Separate Vector Store + Link to Pack
New `VectorStore` class, separate DB, linked via `chunk_id` to `context_pack.json`.
- **Pros**: Clean separation of concerns, doesn't touch existing graph.
- **Cons**: New subsystem to maintain, potential sync issues.
- **Effort**: High

## Recommendation
**Approach 1**. The graph infrastructure already exists and works. The highest-ROI move is enriching it (docstrings, type_refs, import_depth) and wiring it into the Oracle as a 4th signal. Vector embeddings can come later as an additive layer.

## Risks
- Graph enrichment may balloon DB size if not careful with metadata.
- Oracle latency budget: adding graph signal must stay under 50ms total.
- Embedding model choice (if pursued) affects cold-start time and disk footprint.

## Ready for Proposal
Yes.
