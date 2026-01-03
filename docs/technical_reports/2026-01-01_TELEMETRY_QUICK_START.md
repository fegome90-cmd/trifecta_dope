# Telemetry Instrumentation: Quick Start Guide

**Date:** 2026-01-01  
**For:** Implementation Team  
**Status:** Ready to build  
**Duration:** 4–5 days (4 sequential tickets)

---

## ONE-PAGE SUMMARY

### What We're Doing
Instrument Trifecta's **existing telemetry system** (`_ctx/telemetry/events.jsonl + metrics.json + last_run.json`) to measure AST/LSP performance WITHOUT creating a second system.

### Key Deliverables
| Metric | Where | How to Query |
|--------|-------|--------------|
| **AST parse latency** | events.jsonl | `jq 'select(.cmd=="ast.parse") | .timing_ms'` |
| **LSP ready time** | last_run.json | `jq '.latencies."lsp.ready".p50_ms'` |
| **Bytes read by mode** | last_run.json | `jq '.file_read'` → skeleton/excerpt/raw totals |
| **Fallback rate** | last_run.json | `jq '.lsp.lsp_timeout_rate'` |
| **Cache hit rate** | last_run.json | `jq '.ast.ast_cache_hit_rate'` |

### No Breaking Changes
- Existing CLI args unchanged
- Old events still valid
- New fields additive only

---

## CRITICAL RULES (REMEMBER!)

1. **Monotonic timing:** Always use `time.perf_counter_ns()` for relative durations
   ```python
   start_ns = time.perf_counter_ns()
   # ... operation ...
   elapsed_ms = int((time.perf_counter_ns() - start_ns) / 1_000_000)
   ```

2. **Relative paths only:** No absolute paths in telemetry
   ```python
   # WRONG:
   telemetry.event("ast.parse", {"file": "/Users/alice/my_code.py"}, ...)

   # RIGHT:
   telemetry.event("ast.parse", {"file": "src/domain/models.py"}, ...)
   ```

3. **Extended fields in `event()`:** Merge kwargs into JSON payload
   ```python
   telemetry.event(
       "ctx.search",
       {"query": "test"},
       {"hits": 2},
       145,  # timing_ms
       bytes_read=1024,       # NEW
       disclosure_mode="skeleton",  # NEW
   )
   ```

4. **LSP READY definition:** Initialize + (diagnostics OR definition success)
   ```
   lsp.spawn → lsp.initialize → [lsp.ready]
                                   (when publishDiagnostics received OR first definition_response)
   ```

---

## IMPLEMENTATION SEQUENCE

### ✅ PREREQUISITE: Read & Understand
- [ ] Read [2026-01-01_TELEMETRY_EXTENSION_AUDIT.md](2026-01-01_TELEMETRY_EXTENSION_AUDIT.md)
  - [ ] Phase A: Current system architecture
  - [ ] Phase B: Design of extension
  - [ ] Phase C: Hook points with file:line references
  - [ ] Phase D: Redaction/security rules

### 📋 TICKET 1: Core Telemetry (2 hours)
**File:** `src/infrastructure/telemetry.py`

**Changes:**
1. Line 113: Extend `event()` to accept `**extra_fields`
2. Line 145: Merge extra_fields into payload dict
3. Line 245: Add AST/LSP/file_read summaries to `flush()`

**Tests:**
- `test_telemetry_extra_fields_serialized`
- `test_telemetry_summary_calculations`

**Verify:**
```bash
cd /workspaces/trifecta_dope
python -m pytest tests/unit/test_telemetry_ast_lsp.py::TestTelemetryExtension -v
```

### 📦 TICKET 2: AST+LSP Module (16 hours)
**File:** `src/infrastructure/ast_lsp.py` (NEW)

**Classes to implement:**
1. `SkeletonMapBuilder` (300 lines)
   - `parse_python(code, file_path)` → SkeletonMap
   - Uses tree-sitter for parsing
   - Emits `ast.parse` event with monotonic timing

2. `LSPClient` (200 lines)
   - `__init__(telemetry, pyright_binary)`
   - `initialize(workspace_path)`
   - `definition(file_path, line, col)` → response (or timeout)
   - Emits `lsp.spawn`, `lsp.initialize`, `lsp.definition`, `lsp.timeout` events

3. `Selector` (100 lines)
   - `resolve_symbol(symbol_query)` → {file, line, kind}
   - Parses `sym://python/module/Name`
   - Emits `selector.resolve` event

**Dependencies to install:**
```bash
pip install tree-sitter tree-sitter-python
```

**Tests:**
- `test_skeleton_parse_perf_counter_ns`
- `test_lsp_timeout_fallback`
- `test_selector_resolve_symbol`

**Verify:**
```bash
python -m pytest tests/unit/test_ast_lsp.py -v
python -c "from src.infrastructure.ast_lsp import SkeletonMapBuilder, LSPClient, Selector; print('✓ Imports OK')"
```

### 🎯 TICKET 3: CLI + FileSystem (8 hours)
**Files:** `src/infrastructure/cli.py` + `src/infrastructure/file_system.py`

**Changes:**
1. cli.py line 279 (ctx.search):
   - Change `time.time()` → `time.perf_counter_ns()`
   - Add `bytes_read=file_system.total_bytes_read` to event()
   - Add `disclosure_mode=None` to event()

2. cli.py line 317 (ctx.get):
   - Same as search, but `disclosure_mode=mode`

3. file_system.py:
   - Add `self.total_bytes_read = 0` in `__init__()`
   - Track bytes per read: `self.total_bytes_read += len(content.encode())`
   - Increment counters: `telemetry.incr(f"file_read_{mode}_bytes_total", bytes_read)`

**Tests:**
- `test_cli_search_emits_bytes_read`
- `test_cli_get_emits_disclosure_mode`

**Verify:**
```bash
python -m pytest tests/unit/test_cli_instrumentation.py -v
python -m src.infrastructure.cli ctx search --segment . --query "test" --telemetry lite
# Check _ctx/telemetry/events.jsonl for bytes_read field
cat _ctx/telemetry/events.jsonl | jq '.[] | select(.cmd=="ctx.search") | {cmd, bytes_read}'
```

### ✅ TICKET 4: Tests + Integration (16 hours)
**Files:** `tests/unit/test_telemetry_ast_lsp.py` + `tests/integration/test_lsp_instrumentation.py`

**Test coverage:**
- Monotonic clock verification
- Relative path redaction
- LSP READY trigger
- Fallback on timeout
- Bytes aggregation
- Summary percentile math
- Concurrent safety

**Run full suite:**
```bash
cd /workspaces/trifecta_dope
pytest tests/ --cov=src --cov-report=term-missing
# Target: >80% coverage
```

**Example: Validate percentiles work**
```bash
python -c "
from tests.fixtures.synthetic_telemetry import test_summary_percentile_validation
test_summary_percentile_validation()
print('✓ Percentile math validated')
"
```

---

## CHECKLIST FOR DAY 1 (BEFORE YOU START)

- [ ] Clone/cd into `/workspaces/trifecta_dope`
- [ ] Read AUDIT doc completely
- [ ] Verify Python 3.12+: `python --version`
- [ ] Create branch: `git checkout -b feat/telemetry-instrumentation`
- [ ] Install tree-sitter: `pip install tree-sitter tree-sitter-python`
- [ ] Verify test framework: `pytest --version` (should be installed)
- [ ] Run baseline tests: `pytest tests/ -q` (capture output for comparison)

---

## QUICK REFERENCE: Hook Points

| Component | File | Line | What to do |
|-----------|------|------|-----------|
| CLI search | cli.py | 279 | Use perf_counter_ns, add bytes_read, flush on error |
| CLI get | cli.py | 317 | Use perf_counter_ns, add bytes_read + disclosure_mode |
| Telemetry event | telemetry.py | 113 | Accept `**extra_fields`, merge into payload |
| Telemetry flush | telemetry.py | 245 | Add AST/LSP/file_read summaries |
| AST parse | ast_lsp.py | NEW | SkeletonMapBuilder.parse_python() with perf_counter_ns |
| LSP init | ast_lsp.py | NEW | LSPClient.__init__() spawn + telemetry.event("lsp.spawn") |
| LSP definition | ast_lsp.py | NEW | LSPClient.definition() with timeout 500ms + fallback |
| File read | file_system.py | ~ | Track total_bytes_read per mode |

---

## EXAMPLE: First Event You'll Emit

After implementing Ticket 1 + 2:

```json
{
  "ts": "2026-01-01T12:34:56.789012+00:00",
  "run_id": "run_1767123456",
  "segment": "/workspaces/trifecta_dope",
  "cmd": "ast.parse",
  "args": {"file": "src/domain/models.py"},
  "result": {"functions": 12, "classes": 3, "status": "ok"},
  "timing_ms": 42,
  "tokens": {...},
  "warnings": [],
  "skeleton_bytes": 8192,
  "reduction_ratio": 0.0234
}
```

And in last_run.json:

```json
{
  "run_id": "run_1767123456",
  "latencies": {
    "ast.parse": {
      "count": 15,
      "p50_ms": 38.0,
      "p95_ms": 52.0,
      "max_ms": 73.0
    }
  },
  "ast": {
    "ast_parse_count": 15,
    "ast_cache_hit_count": 11,
    "ast_cache_hit_rate": 0.733
  }
}
```

---

## IF STUCK

### "perf_counter_ns() not available"
→ Ensure Python 3.7+ (introduced in 3.3, widely available in 3.7+)

### "tree-sitter import fails"
→ Run: `pip install tree-sitter tree-sitter-python`

### "Test passes locally but fails in CI"
→ Check PYTHONPATH: `export PYTHONPATH=/workspaces/trifecta_dope:$PYTHONPATH`

### "Events not logging to events.jsonl"
→ Check telemetry level: `telemetry = Telemetry(path, level="lite")` (level must not be "off")

### "Relative path redaction confused"
→ Use: `try: path.relative_to(segment_root) except ValueError: path.name`

### "Timeout mechanism not working"
→ Ensure LSPClient uses: `timeout_ms=500`, raises `TimeoutError`, falls back to Tree-sitter

---

## NEXT STEPS (AFTER ALL 4 TICKETS DONE)

1. **Merge to main:** All 4 PRs approved and merged
2. **Update docs:** Create or update `docs/telemetry.md` with event specs
3. **Generate example data:** Run a few commands, save sanitized events.jsonl + last_run.json
4. **Tag release:** Create release notes mentioning telemetry instrumentation
5. **Monitor:** First week post-deployment, watch for lock_skipped warnings

---

**Go build! 🚀**

Questions? Refer to:
- **Architecture:** TELEMETRY_EXTENSION_AUDIT.md Phase A–G
- **Implementation:** TELEMETRY_PR_PLAN.md Tickets 1–4  
- **Quick answers:** This doc
