# WO-P2.1: AST Cache Telemetry Implementation Plan

**Date**: 2026-01-06  
**Status**: ACTIVE  
**Priority**: P0 (Blocks global enable)

---

## Objective

Integrate audit-grade telemetry into AST cache to track every operation. Required for debugging, performance analysis, and verifying P1 works in production.

---

## Design Decision: Wrapper Pattern

**Why not modify AstCache Protocol?**
- Protocol is clean (get/set/delete/clear/stats)
- Adding telemetry dependency breaks clean architecture
- Existing code uses Protocol, not concrete classes

**Solution**: Telemetry Wrapper
```python
class TelemetryAstCache:
    """Wraps any AstCache and emits telemetry events."""
    def __init__(self, inner: AstCache, telemetry: Telemetry, segment_id: str):
        self._inner = inner
        self._tel = telemetry
        self._segment_id = segment_id
        self._backend = inner.__class__.__name__  # "SQLiteCache" or "InMemoryLRUCache"
    
    def get(self, key: str) -> Optional[Any]:
        t0 = time.perf_counter_ns()
        value = self._inner.get(key)
        timing_ms = (time.perf_counter_ns() - t0) // 1_000_000
        
        status = "hit" if value is not None else "miss"
        self._tel.event(
            cmd=f"ast.cache.{status}",
            args={"cache_key": key},
            result={"backend": self._backend, "segment_id": self._segment_id},
            timing_ms=timing_ms
        )
        return value
```

---

## Implementation Tasks

### Task 1: Create Wrapper Class

**File**: `src/infrastructure/telemetry_cache.py` (new)

**Implementation**:
- `TelemetryAstCache` wraps `AstCache` Protocol
- Emits on `get()`, `set()`, `delete()`, `clear()`
- Delegates stats() unchanged (no telemetry needed)

**Events**:
- `ast.cache.hit`: Value found
- `ast.cache.miss`: Value not found
- `ast.cache.write`: New value written
- `ast.cache.delete`: Entry deleted
- `ast.cache.clear`: Full cache cleared

**Schema**:
```json
{
  "cmd": "ast.cache.hit",
  "args": {
    "cache_key": "segment_id:file.py:hash:v1"
  },
  "result": {
    "backend": "SQLiteCache",
    "segment_id": "trifecta_dope",
    "db_path": "[REDACTED]"  // Only if SQLite
  },
  "timing_ms": 2
}
```

---

### Task 2: Update Factory

**File**: `src/infrastructure/factories.py`

**Changes**:
```python
def get_ast_cache(
    persist: bool = False,
    segment_id: str = ".",
    telemetry: Optional[Telemetry] = None,  # NEW
    max_entries: int = 10000,
    max_bytes: int = 100 * 1024 * 1024,
) -> AstCache:
    # ... existing logic ...
    
    cache = SQLiteCache(...) if should_persist else InMemoryLRUCache(...)
    
    # Wrap if telemetry available
    if telemetry:
        from src.infrastructure.telemetry_cache import TelemetryAstCache
        return TelemetryAstCache(cache, telemetry, segment_id)
    
    return cache
```

---

### Task 3: Wire Telemetry in Consumers

**File 1**: `src/infrastructure/cli_ast.py`

```python
@ast_app.command("symbols")
def symbols(...):
    telemetry = _get_telemetry(telemetry_level)
    cache = get_ast_cache(
        persist=persist_cache, 
        segment_id=str(root),
        telemetry=telemetry  # NEW
    )
```

**File 2**: `src/application/pr2_context_searcher.py`

```python
class PR2ContextSearcher:
    def __init__(self, workspace_root: Path, tel: Telemetry, ...):
        if cache is None:
            from src.infrastructure.factories import get_ast_cache
            cache = get_ast_cache(
                segment_id=str(workspace_root),
                telemetry=tel  # NEW
            )
```

---

### Task 4: E2E Test

**File**: `tests/integration/test_ast_cache_telemetry.py` (new)

**Test Case 1**: Verify events appear
```python
def test_ast_cache_telemetry_events(fresh_cli_workspace):
    """Verify cache operations emit telemetry events."""
    cwd = fresh_cli_workspace
    
    # Run 1: Cold (expect miss)
    res1 = run_ast_symbols(cwd, "sym://python/mod/target", telemetry="lite")
    
    # Check events.jsonl
    events_file = cwd / "_ctx/telemetry/events.jsonl"
    assert events_file.exists()
    
    events = [json.loads(line) for line in events_file.read_text().splitlines()]
    miss_events = [e for e in events if e.get("cmd") == "ast.cache.miss"]
    assert len(miss_events) > 0
    
    # Run 2: Warm (expect hit)
    res2 = run_ast_symbols(cwd, "sym://python/mod/target", telemetry="lite")
    
    events = [json.loads(line) for line in events_file.read_text().splitlines()]
    hit_events = [e for e in events if e.get("cmd") == "ast.cache.hit"]
    assert len(hit_events) > 0
```

**Test Case 2**: Verify schema
```python
def test_ast_cache_event_schema(fresh_cli_workspace):
    """Verify telemetry events have correct schema."""
    # ... run command ...
    
    hit_event = hit_events[0]
    assert "args" in hit_event
    assert "cache_key" in hit_event["args"]
    assert "result" in hit_event
    assert "backend" in hit_event["result"]
    assert hit_event["result"]["backend"] in ("SQLiteCache", "InMemoryLRUCache")
```

---

## Acceptance Criteria (DoD)

- [ ] `TelemetryAstCache` wrapper implemented
- [ ] Factory accepts `telemetry` parameter
- [ ] CLI wired to pass telemetry
- [ ] PR2 wired to pass telemetry
- [ ] E2E test verifies events appear (miss → hit)
- [ ] Event schema includes: backend, segment_id, cache_key, timing_ms
- [ ] No performance degradation (< 5ms overhead)
- [ ] All existing tests still pass

---

## Success Metrics

**After WO-P2.1**:
- `jq 'select(.cmd | startswith("ast.cache"))' _ctx/telemetry/events.jsonl` shows events
- Cache hit rate measurable in production
- Debug issues traceable via cache_key + segment_id

---

## Security Note

**Path Redaction**: If `db_path` is emitted, redact user/home paths:
```python
def redact_path(path: Path) -> str:
    return str(path).replace(str(Path.home()), "[HOME]")
```
