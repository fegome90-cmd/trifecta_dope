#### C.1.1 CLI Entry Point

**File:** `src/infrastructure/cli.py`

**Hooks:**
- [ ] Line 173: `telemetry = _get_telemetry(...)` → Add repo_sha + dirty flag to event context
- [ ] Line 279: `ctx.search` timing → Add `bytes_read_per_query`, `cache_hit_rate`
- [ ] Line 317: `ctx.get` timing → Add `bytes_read_per_get`, `disclosure_mode_used`
- [ ] Line 351: `ctx.validate` timing → No changes (no AST/LSP)
- [ ] Line 438: `ctx.stats` timing → No changes

**Implementation:**
```python
# At top of each command function
import time
start_ns = time.perf_counter_ns()
# ... operation ...
elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
telemetry.event(
    cmd_name,
    args_dict,
    result_dict,
    int(elapsed_ms),
    bytes_read=fs_adapter.total_bytes_read,  # NEW
    disclosure_mode="skeleton",  # NEW (if applicable)
)
```
