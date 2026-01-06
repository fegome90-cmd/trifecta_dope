# P0 AST Persistence - Inventory Report

**Date**: 2026-01-06
**Evidence**: `_ctx/logs/wo0005_p0_ast/`

## 1. Inventory Table

| File | Line | Component | Function | Persisted? | Risk |
|------|------|-----------|----------|------------|------|
| `src/domain/ast_cache.py` | 204 | `SQLiteCache` | Core Implementation | YES | High (Schema evolution, locking) |
| `src/domain/ast_cache.py` | 78 | `InMemoryLRUCache` | Fallback / Default | NO | Low (Ephemeral) |
| `src/infrastructure/cli_ast.py` | 40 | `_get_cache` | Factory (SQLite) | YES | Med (Path construction) |
| `src/infrastructure/cli_ast.py` | 51 | `symbols` CLI | Entry Point (`--persist-cache`) | Optional | Med (User intent) |
| `src/application/ast_parser.py` | 50 | `SkeletonMapBuilder` | AST Generation | Agnostic | Low (Depends on cache injection) |
| `src/application/pr2_context_searcher.py` | 67 | `PR2ContextSearcher` | Usage (hardcoded segment_id) | Unknown | High (Implicit dependency) |
| `src/infrastructure/lsp_daemon.py` | 25 | `LSPDaemon` | Usage (segment_id) | NO | Med (Recomputes on startup?) |
| `src/infrastructure/segment_utils.py` | 31 | `compute_segment_id` | Naming (hashing) | N/A | High (Key stability) |

## 2. Findings

### Persistence Status
- **SQLiteCache** exists and is implemented with `sqlite3`.
- **Integration**: Linked in `cli_ast.py` via `--persist-cache` flag.
- **Default**: Default behavior is `InMemoryLRUCache` (ephemeral), meaning **no cross-run persistence** by default.

### Segmentation Logic
- Uses `compute_segment_id` (hashing absolute path) or `normalize_segment_id` (directory name).
- `cli_ast.py` uses `str(root)` as `segment_id`, which might conflict with other parts using hashed IDs.

### Risks
1. **Parallel Usage**: `SQLiteCache` has basic table creation but no WAL mode explicit configuration seen in `_init_db`.
2. **Schema**: Fixed schema (`key`, `value`, `created_at`...). hardcoded.
3. **Serialization**: Uses `json.dumps` for values. If AST nodes are complex objects, they must support `to_dict()`. `AstCache.set` handles `dataclass` and `to_dict`.
