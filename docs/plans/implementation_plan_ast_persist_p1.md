# AST Persistence P1 - Implementation Plan (Retrospective)

**Date**: 2026-01-06  
**SHA**: `354afb6`  
**Status**: ✅ VERIFIED (Gates 1-3 PASSED)

---

## Objetivo

Eliminar "works when injected" del AST cache. Implementar factory centralizada con wiring operable vía `TRIFECTA_AST_PERSIST` env var y `--persist-cache` flag.

---

## Arquitectura Final

### Factory Pattern (Single Source of Truth)

**Ubicación**: `src/infrastructure/factories.py`

```python
def get_ast_cache(
    persist: bool = False,
    segment_id: str = ".",
    max_entries: int = 10000,
    max_bytes: int = 100 * 1024 * 1024,
) -> AstCache
```

**Decisiones de persistencia**:
1. Si `persist=True` explícitamente → SQLiteCache
2. Si `TRIFECTA_AST_PERSIST=1` → SQLiteCache
3. Default → InMemoryLRUCache

### Wiring Points

1. **CLI** (`src/infrastructure/cli_ast.py`):
   - Comando `trifecta ast symbols --persist-cache`
   - Usa `get_ast_cache(persist=persist_cache, segment_id=str(root))`

2. **PR2 Context Searcher** (`src/application/pr2_context_searcher.py`):
   - Cuando cache es None → `get_ast_cache(segment_id=str(workspace_root))`
   - Respeta env var automáticamente

### Path Determinism

**SQLite Location**: `.trifecta/cache/ast_cache_{segment_id}.db`

**Segment ID Sanitization**:
```python
safe_id = segment_id.replace("/", "_").replace("\\", "_").replace(":", "_")
```

---

## Invariantes

1. **Single Source**: Solo `get_ast_cache()` construye instancias de cache
2. **Env Var Priority**: `TRIFECTA_AST_PERSIST=1` activa persistencia global
3. **Flag Override**: `--persist-cache` en CLI fuerza SQLite independiente de env
4. **Path Stability**: Mismo `segment_id` → mismo DB file (determinista)

---

## Riesgos Identificados

| Riesgo | Mitigación | Estado |
|--------|-----------|--------|
| **Locks SQLite** | WAL mode no configurado explícitamente | ⚠️ TODO (P2) |
| **Corrupción DB** | Sin checksums/validation | ⚠️ TODO (P2) |
| **Concurrencia CLI/Daemon** | Sin file locks | ⚠️ TODO (P2) |
| **Path Variability** | Sanitización implementada | ✅ DONE |
| **Segment ID Drift** | Factory toma `str(root)` consistente | ✅ DONE |

---

## Acceptance Criteria (DoD)

- [x] Factory `get_ast_cache()` implementada
- [x] CLI wired a factory
- [x] PR2 wired a factory
- [x] E2E test `test_ast_cache_persist_cross_run_cli.py` (2/2 PASSED)
- [x] Env var `TRIFECTA_AST_PERSIST` funcional
- [x] Clean worktree verification (Gate 2 PASSED)
- [x] SQLite path determinista verificado

---

## Testing Strategy

### Unit Tests (P0)
- `tests/integration/test_ast_sqlite_cache_roundtrip.py` (2/2 PASSED)

### E2E Tests (P1)
- `tests/integration/test_ast_cache_persist_cross_run_cli.py`:
  1. `test_ast_persistence_cross_run`: Verifica hit en segundo run
  2. `test_ast_persistence_env_var_control`: Verifica que sin env = no DB

### Verification Gates
1. **Gate 1**: Main repo pytest
2. **Gate 2**: Clean worktree /tmp
3. **Gate 3**: Evidence signals (factory usage, hit status, DB creation)

---

## Next Phase (P2 - Hardening)

1. **Observability**: Telemetry para cache_hit/cache_miss rates
2. **Multi-Process**: File locks para CLI + daemon concurrente
3. **Corruption Recovery**: Checksums + fallback a rebuild
4. **Size Management**: TTL, LRU eviction stats, DB size monitoring
5. **Migrations**: Schema versioning para SQLite
