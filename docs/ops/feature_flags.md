# Feature Flags

This document documents feature flags available in Trifecta for controlling runtime behavior.

## TRIFECTA_AST_PERSIST

Controls the AST cache backend strategy - persistent (SQLite) vs ephemeral (in-memory).

### Overview

| Value | Backend | Behavior | Use Case |
|-------|---------|----------|----------|
| `1` | `SQLiteCache` (via `FileLockedAstCache`) | Persists AST data to disk, survives process restart | Dev CLI, long-running sessions |
| `0` or unset | `InMemoryLRUCache` | Ephemeral cache, process-scoped | Tests, CI, short-lived operations |

### Decision Logic

The cache backend is selected in `src/infrastructure/factories.py:get_ast_cache()`:

```python
should_persist = persist or os.environ.get("TRIFECTA_AST_PERSIST", "0") == "1"

if should_persist:
    cache = SQLiteCache(...)  # FileLockedAstCache wrapper
else:
    cache = InMemoryLRUCache(...)
```

Priority:
1. Explicit `persist=True` parameter overrides env var
2. `TRIFECTA_AST_PERSIST=1` enables persistence
3. Default (unset or `0`) uses in-memory cache

### Default Values by Environment

| Environment | Default | Rationale |
|-------------|---------|-----------|
| **Dev CLI** (via `.envrc`) | `1` | Survive shell restarts, warm cache |
| **Tests** (pytest-env) | `0` | Isolation, no side-effects |
| **CI** | `0` | Clean slate, reproducibility |
| **Production** | TBD | Pending operational requirements |

### Usage Examples

```bash
# Enable persistence (Dev CLI default)
export TRIFECTA_AST_PERSIST=1
uv run trifecta ast symbols "sym://python/mod/src.domain.result" --segment .

# Disable persistence (explicit rollback)
TRIFECTA_AST_PERSIST=0 uv run trifecta ast symbols "sym://python/mod/src.domain.result" --segment .

# Check current setting
echo $TRIFECTA_AST_PERSIST  # Prints "1" or "0" or empty
```

### Telemetry Observability

When persistence is enabled, the following telemetry events are emitted:

| Event | Meaning |
|-------|---------|
| `ast.cache.hit` | Value found in cache (persisted or in-memory) |
| `ast.cache.miss` | Value not found, will be fetched and cached |
| `ast.cache.write` | New value written to cache (persistence only) |

Monitoring cache hit rate via telemetry:
```bash
# Analyze cache effectiveness
python scripts/telemetry_diagnostic.py | grep "ast.cache"
```

### Rollback Procedure

To rollback from persistent to ephemeral cache:

1. **Disable the flag**:
   ```bash
   export TRIFECTA_AST_PERSIST=0
   # OR edit .envrc and set: export TRIFECTA_AST_PERSIST=0
   ```

2. **Clear existing cache** (optional, removes persisted data):
   ```bash
   rm -rf .trifecta/cache/cache_*.db
   ```

3. **Verify backend**:
   ```bash
   # Should show "InMemoryLRUCache" in telemetry output
   TRIFECTA_TELEMETRY_DIR=/tmp/tel uv run trifecta ast symbols "..." --segment .
   cat /tmp/tel/events.jsonl | jq '.result.backend'
   ```

### Verification Gate

Use the official verification script to confirm backend selection:

```bash
# Test both backends
./eval/scripts/gate_ast_persist_backend.sh
```

### Implementation Reference

- **Factory**: `src/infrastructure/factories.py:get_ast_cache()`
- **Cache Implementations**: `src/infrastructure/cache/`
- **Gate Script**: `eval/scripts/gate_ast_persist_backend.sh`
- **Epic**: E-0001 (AST Cache Operability)
- **WO**: WO-0012 (Persistence Feature Flag)

---

## Future Flags

*(Reserved for future feature flags)*

### TRIFECTA_TELEMETRY_DISABLED

Planned flag to globally disable telemetry without removing events from code.

Status: **Not yet implemented** - use `TRIFECTA_NO_TELEMETRY=1` for tests.
