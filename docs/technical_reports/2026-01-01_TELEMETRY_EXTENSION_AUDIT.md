# Telemetry Extension Audit v1: AST+LSP Instrumentation Plan

**Date:** 2026-01-01  
**Role:** Senior Engineer / Telemetry Auditor  
**Status:** FINAL - Ready for Implementation  
**Scope:** Instrument AST/LSP latencies, bytes_read, fallbacks in EXISTING telemetry system (no parallel pipelines)

---

## PHASE A: DISCOVERY - CURRENT SYSTEM AUDIT

### A.1 Telemetry Architecture (As-Is)

**Sink Location:** `_ctx/telemetry/` (within segment directory)

```
_ctx/telemetry/
├── events.jsonl          # Append-only log of discrete events (rotated at 5MB)
├── events.1.jsonl        # Rotation backup (if >5MB)
├── events.2.jsonl        # Older backup
├── metrics.json          # Cumulative counters (aggregated across all runs)
└── last_run.json         # Summary of last execution (latencies, tokens, pack_state)
```

**Class:** `src/infrastructure/telemetry.py` line 16: `class Telemetry`

**Key Methods:**
| Method | Purpose | Called From | Evidence |
|--------|---------|-------------|----------|
| `__init__(segment_path, level, run_id)` | Initialize telemetry, create dirs | cli.py:51 `_get_telemetry()` | ✅ CONFIRMED |
| `event(cmd, args, result, timing_ms, warnings)` | Log discrete event to events.jsonl | cli.py:182+ (search, get, validate, etc.) | ✅ CONFIRMED |
| `observe(cmd, ms)` | Record latency in microseconds | cli.py:279 (ctx.search), 317 (ctx.get), 351 (ctx.validate) | ✅ CONFIRMED |
| `incr(name, n=1)` | Increment counter in memory | Used by use_cases (not yet in CLI commands) | ⏳ SPARSE |
| `flush()` | Persist metrics.json + last_run.json | cli.py:188, 203, 220, etc. | ✅ CONFIRMED |

### A.2 Event Format (JSONL)

**Example from events.jsonl line 1:**
```json
{
  "ts": "2025-12-29T22:06:52.060304+00:00",
  "run_id": "run_1767046012",
  "segment": "/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope",
  "cmd": "ctx.sync",
  "args": {"segment": "."},
  "result": {"status": "ok"},
  "timing_ms": 2,
  "warnings": []
}
```

**Fields:**
- `ts` (ISO 8601 UTC): Event timestamp (wall-clock, NOT monotonic)
- `run_id` (str): Unique identifier per CLI invocation (format: `run_{unix_timestamp}`)
- `segment` (str): Absolute path to target segment
- `cmd` (str): Command name (e.g., "ctx.search", "ctx.get", "ctx.sync")
- `args` (dict): Sanitized arguments (truncated to 120 chars max per `_sanitize_args`)
- `result` (dict): Output summary (status, hit count, chunks returned, etc.)
- `timing_ms` (int): Total elapsed time in milliseconds
- `warnings` (list): List of warning strings (max 5 in last_run.json)

**Note:** `args` field currently EXCLUDES sensitive data:
- Query/task text: truncated to 120 chars (line 206: `safe[k] = v[:120]`)
- IDs, segments, limits: passed as-is
- Unknown args: silently dropped (line 213: "Skip unknown args for safety")

### A.3 Aggregation Format (last_run.json)

**Example from last_run.json (truncated):**
```json
{
  "run_id": "run_1767232876",
  "ts": "2026-01-01T02:01:16.990404+00:00",
  "metrics_delta": {
    "ctx_stats_count": 1
  },
  "latencies": {
    "ctx.stats": {
      "count": 1,
      "p50_ms": 7.0,
      "p95_ms": 7.0,
      "max_ms": 7.0
    }
  },
  "tokens": {},
  "top_warnings": [],
  "pack_state": {
    "pack_sha": "365c67055285ad84",
    "pack_mtime": 1767230435.5603714
  }
}
```

**Key observations:**
- `latencies[cmd]` includes: count, p50_ms, p95_ms, max_ms (calculated in `flush()` line 231-242)
- Percentiles calculated on-the-fly from in-memory `self.latencies[cmd]` array (stored in **microseconds**, converted to ms in output)
- `pack_sha` is 16-char hash of context_pack.json (for stale detection)
- `pack_mtime` is float (Unix seconds) for mtime tracking

### A.4 Concurrency & Locking

**Lock Mechanism:** POSIX fcntl (non-blocking, fail-safe)

**Code:** `telemetry.py` lines 258-276:
```python
def _write_jsonl(self, filename: str, data: Dict[str, Any]) -> None:
    """Append to JSONL with rotation and locking."""
    path = self.telemetry_dir / filename
    self._rotate_if_needed(path)

    import fcntl
    try:
        with open(path, "a", encoding="utf-8") as f:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except (IOError, OSError):
                # Lock busy: skip write to avoid corruption
                print("Telemetry skipped: lock busy", file=sys.stderr)
                self.warnings.append("telemetry_lock_skipped")
                return  # ← SKIP WRITE if busy (fail-safe, lossy)
```

**Behavior:**
- Non-blocking lock (LOCK_NB); if lock held, skip write and log warning
- **This is LOSSY**: If concurrent writes happen, some events are dropped
- **Acceptable for**: Sampling-grade telemetry (metrics counters)
- **NOT acceptable for**: Critical events (LSP ready, command boundaries, bytes_read)

**Mitigation for MVP:** Use existing `telemetry.event()` which uses this lock, but add a **fallback queue** for critical events (see Phase B).

### A.5 Timing Precision

**Current:** Uses `time.time()` wall-clock (millisecond precision)

**Example from cli.py:279:**
```python
start_time = time.time()
# ... operation ...
telemetry.observe("ctx.search", int((time.time() - start_time) * 1000))
```

**Issue:** `time.time()` is affected by NTP adjustments, clock skew, etc.

**For AST/LSP:** MUST use monotonic clock (`time.perf_counter_ns()`) for relative durations.

### A.6 Sampling & Drop Rates

**Current sampling:** None for events; all events logged unless lock busy.

**Drop rate:** Measured by `telemetry_lock_skipped` warnings in top_warnings (line 245).

**Acceptable drop rate for MVP:** <2% (telemetry is non-critical; if dropped, not catastrophic).

---

## PHASE B: DESIGN - MINIMAL EXTENSION

### B.1 New Event Types (extend, don't duplicate)

**No new files.** All events go to `events.jsonl` with new `cmd` values:

| Event Type | cmd | Trigger | Fields |
|------------|-----|---------|--------|
| AST skeleton parse | `ast.parse` | SkeletonMapBuilder.parse_python() | file_path_rel, reduction_ratio, skeleton_bytes |
| AST skeleton cache | `ast.cache` | Cache hit/miss | file_path_rel, cache_hit, prev_sha |
| Symbol selector resolve | `selector.resolve` | Selector.resolve_symbol() | symbol_query, resolved, matches_count, ambiguous |
| LSP spawn | `lsp.spawn` | LSPClient.__init__() subprocess spawn | pyright_binary, cold_start_flag |
| LSP initialize | `lsp.initialize` | LSP initialize response received | workspace_initialized, capabilities_received |
| LSP ready | `lsp.ready` | publishDiagnostics OR first hover success | ready_via (diagnostics\|hover), cumulative_ms |
| LSP definition request | `lsp.definition` | textDocument/definition response | symbol_name, resolved, file_path_rel, line_no |
| LSP timeout | `lsp.timeout` | LSP request exceeds 500ms | request_type, timeout_ms, fallback_to |
| LSP diagnostics | `lsp.diagnostics` | publishDiagnostics notification received | first_diag_count, redacted_snippet_hash |
| File read | `file.read` | FileSystemAdapter.read_*() | file_path_rel, read_mode (skeleton\|excerpt\|raw), bytes_read, duration_ms |

### B.2 Extended Fields in Existing Events

**Modify `event()` signature to accept optional structured fields:**

```python
def event(
    self,
    cmd: str,
    args: Dict[str, Any],
    result: Dict[str, Any],
    timing_ms: int,
    warnings: List[str] | None = None,
    **extra_fields  # NEW: accept arbitrary kwargs for extensibility
) -> None:
```

**Usage example:**
```python
telemetry.event(
    "ctx.search",
    {"query": "context routing"},
    {"hits": 2, "returned_ids": [...]},
    timing_ms=145,
    bytes_read=8192,              # NEW
    disclosure_mode="excerpt",    # NEW
    cache_hit_rate=0.87           # NEW
)
```

**Payload becomes:**
```json
{
  "ts": "2025-12-30...",
  "run_id": "run_...",
  "cmd": "ctx.search",
  "args": {"query": "context routing"},
  "result": {"hits": 2, ...},
  "timing_ms": 145,
  "bytes_read": 8192,             # ← NEW FIELD
  "disclosure_mode": "excerpt",   # ← NEW FIELD
  "cache_hit_rate": 0.87          # ← NEW FIELD
}
```

### B.3 Metrics Counter Extensions

**Existing counters (metrics.json):**
- `ctx_build_count`, `ctx_search_count`, `ctx_get_count`, etc.

**New counters (via `telemetry.incr()`):**
| Counter | Semantics | Incremented Where |
|---------|-----------|-------------------|
| `ast_parse_count` | Total skeleton parses | SkeletonMapBuilder.parse_python() |
| `ast_cache_hit_count` | Cache hits | SkeletonMapBuilder (cache layer) |
| `selector_resolve_count` | Symbol resolutions attempted | Selector.resolve_symbol() |
| `selector_resolve_success_count` | Resolutions succeeded | Selector.resolve_symbol() (on success) |
| `lsp_spawn_count` | LSP processes spawned | LSPClient.__init__() |
| `lsp_ready_count` | LSP reached ready state | DiagnosticsCollector._on_ready() |
| `lsp_timeout_count` | LSP requests timed out | LSPClient.request() on timeout |
| `lsp_fallback_count` | Fallback to Tree-sitter triggered | LSPClient.request() (on timeout or error) |
| `file_read_skeleton_bytes_total` | Total bytes via skeleton mode | FileSystemAdapter.read_*(..., mode="skeleton") |
| `file_read_excerpt_bytes_total` | Total bytes via excerpt mode | FileSystemAdapter.read_*(..., mode="excerpt") |
| `file_read_raw_bytes_total` | Total bytes via raw mode | FileSystemAdapter.read_*(..., mode="raw") |

### B.4 Definition of "LSP READY"

**NOT:** A custom LSP request (doesn't exist in protocol)

**IS:** One of the following:
1. `initialized` request completed AND `publishDiagnostics` notification received for any file
2. `initialized` request completed AND successful `textDocument/definition` response

**Code trigger points:**
```python
# Condition A: After initialize response
lsp_client.on_notification("textDocument/publishDiagnostics", ...)
# Condition B: After successful definition request
lsp_client.send_request("textDocument/definition", ...)
```

**Telemetry:**
```python
# In DiagnosticsCollector
if (self.initialized and self.first_diagnostics_received) or \
   (self.initialized and self.first_definition_success):
    telemetry.event(
        "lsp.ready",
        {"pyright_binary": "pyright-langserver"},
        {"ready_via": "diagnostics" or "definition"},
        timing_ms=cumulative_from_spawn,
    )
```

### B.5 Monotonic Timing (CRITICAL)

**Use `time.perf_counter_ns()` for all AST/LSP relative durations:**

```python
import time

start_ns = time.perf_counter_ns()  # Monotonic clock, nanoseconds
# ... operation ...
elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000

telemetry.observe("lsp.definition", int(elapsed_ms))
```

**NOT `time.time()` for relative intervals!**

**Store as:** Integer milliseconds in `timing_ms` field (for backward compatibility).

---

## PHASE C: IMPLEMENTATION CHECKLIST

### C.1 Hook Points (Where to Instrument)

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

#### C.1.2 AST Layer (NEW Module)

**File:** `src/infrastructure/ast_lsp.py` (NEW)

**Hooks in SkeletonMapBuilder:**
```python
class SkeletonMapBuilder:
    def __init__(self, telemetry: Telemetry):
        self.telemetry = telemetry

    def parse_python(self, code: str, file_path: Path) -> SkeletonMap:
        start_ns = time.perf_counter_ns()
        skeleton = self._do_parse(code)
        elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000

        self.telemetry.event(
            "ast.parse",
            {"file": str(file_path.relative_to(...))},
            {"functions": len(skeleton.functions), "classes": len(skeleton.classes)},
            int(elapsed_ms),
            skeleton_bytes=len(json.dumps(skeleton)),
            reduction_ratio=len(json.dumps(skeleton)) / len(code)
        )
        self.telemetry.incr("ast_parse_count")
        return skeleton
```

#### C.1.3 LSP Manager (NEW Module)

**File:** `src/infrastructure/ast_lsp.py`

**Hooks in LSPClient:**
```python
class LSPClient:
    def __init__(self, telemetry: Telemetry):
        self.telemetry = telemetry
        self.spawn_time_ns = time.perf_counter_ns()

        self.telemetry.event(
            "lsp.spawn",
            {"pyright_binary": PYRIGHT_BIN},
            {"subprocess_pid": self.process.pid},
            0,  # timing_ms will be updated on ready
        )
        self.telemetry.incr("lsp_spawn_count")

    def send_request(self, method: str, params: dict) -> dict:
        start_ns = time.perf_counter_ns()
        try:
            response = self._do_send(method, params)
            elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000

            self.telemetry.event(
                f"lsp.{method.split('/')[-1]}",
                {"method": method, "params_hash": hash(str(params))},
                {"success": True, "response_keys": list(response.keys())},
                int(elapsed_ms),
            )
            return response
        except TimeoutError:
            elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000

            self.telemetry.event(
                "lsp.timeout",
                {"method": method},
                {"timeout_ms": 500},
                int(elapsed_ms),
                fallback_to="tree_sitter"
            )
            self.telemetry.incr("lsp_timeout_count")
            raise
```

#### C.1.4 File System Adapter

**File:** `src/infrastructure/file_system.py`

**Hook in read methods:**
```python
class FileSystemAdapter:
    def read_file_at_mode(self, path: Path, mode: str) -> str:
        start_ns = time.perf_counter_ns()
        content = self._do_read(path, mode)
        elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000

        bytes_read = len(content.encode('utf-8'))
        self.total_bytes_read += bytes_read

        self.telemetry.incr(f"file_read_{mode}_bytes_total", bytes_read)

        return content
```

### C.2 Telemetry Module Changes

**File:** `src/infrastructure/telemetry.py`

**Modifications:**
1. [ ] Line 113: Extend `event()` signature to accept `**extra_fields`
2. [ ] Line 145: Merge `extra_fields` into `payload` dict before write
3. [ ] Add comment documenting new AST/LSP event types
4. [ ] No changes to `observe()`, `incr()`, `flush()` (backward compatible)

**Code diff (minimal):**
```python
def event(
    self,
    cmd: str,
    args: Dict[str, Any],
    result: Dict[str, Any],
    timing_ms: int,
    warnings: List[str] | None = None,
    **extra_fields,  # NEW
) -> None:
    """Log a discrete event with optional extended fields."""
    if not self.enabled:
        return

    if warnings:
        self.warnings.extend(warnings)

    safe_args = self._sanitize_args(args)
    tokens = self._estimate_token_usage(cmd, args, result)

    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "run_id": self.run_id,
        "segment": str(self.segment_path),
        "cmd": cmd,
        "args": safe_args,
        "result": result,
        "timing_ms": timing_ms,
        "tokens": tokens,
        "warnings": warnings or [],
        **extra_fields,  # NEW: merge arbitrary fields
    }

    # ... rest of event() unchanged ...
```

### C.3 Aggregation & Summary

**File:** `src/infrastructure/telemetry.py`, method `flush()` (lines 198–252)

**Additions to last_run.json:**
```python
# After line 242 (latency_summary built)
ast_summary = {
    "ast_parse_count": self.metrics.get("ast_parse_count", 0),
    "ast_cache_hit_rate": (
        self.metrics.get("ast_cache_hit_count", 0) /
        self.metrics.get("ast_parse_count", 1)
    ),
}

lsp_summary = {
    "lsp_spawn_count": self.metrics.get("lsp_spawn_count", 0),
    "lsp_ready_count": self.metrics.get("lsp_ready_count", 0),
    "lsp_timeout_count": self.metrics.get("lsp_timeout_count", 0),
    "lsp_timeout_rate": (
        self.metrics.get("lsp_timeout_count", 0) /
        max(self.metrics.get("lsp_spawn_count", 1), 1)
    ),
    "lsp_fallback_count": self.metrics.get("lsp_fallback_count", 0),
}

file_read_summary = {
    "skeleton_bytes": self.metrics.get("file_read_skeleton_bytes_total", 0),
    "excerpt_bytes": self.metrics.get("file_read_excerpt_bytes_total", 0),
    "raw_bytes": self.metrics.get("file_read_raw_bytes_total", 0),
    "total_bytes": (
        self.metrics.get("file_read_skeleton_bytes_total", 0) +
        self.metrics.get("file_read_excerpt_bytes_total", 0) +
        self.metrics.get("file_read_raw_bytes_total", 0)
    ),
}

run_summary = {
    "run_id": self.run_id,
    "ts": datetime.now(timezone.utc).isoformat(),
    "metrics_delta": self.metrics,
    "latencies": latency_summary,
    "tokens": tokens_summary,
    "ast": ast_summary,          # NEW
    "lsp": lsp_summary,          # NEW
    "file_read": file_read_summary,  # NEW
    "top_warnings": self.warnings[:5],
    "pack_state": {...},
}
```

---

## PHASE D: REDACTION & SECURITY

### D.1 No Sensitive Data in Telemetry

**Redaction rules (HARD):**

| Data Type | Example | Allowed in Telemetry? | How |
|-----------|---------|----------------------|-----|
| Full file path | `/Users/..../myfile.py` | ❌ NO | Use relative path (`src/domain/models.py`) or just filename |
| File content | `config = {"API_KEY": "sk_..."}` | ❌ NO | Use hash or size only |
| API keys, tokens | `sk_abc123def...` | ❌ NO | Redact in args before sending |
| User home dir | `/Users/alice/...` | ❌ NO | Use segment-relative path |
| Query text | `"find secrets in my code"` | ⚠️ TRUNCATED | Truncate to 120 chars (existing behavior) |
| Symbol names | `ContextService`, `search_by_symbol` | ✅ YES | Public names, non-sensitive |
| Line numbers | 42, 150, 200 | ✅ YES | Structural info, non-sensitive |

**Implementation in ast_lsp.py:**
```python
def _relative_path(path: Path, segment_root: Path) -> str:
    """Convert to relative path for telemetry."""
    try:
        return str(path.relative_to(segment_root))
    except ValueError:
        return str(path.name)  # Fallback to filename only

# Usage
telemetry.event(
    "ast.parse",
    {"file": _relative_path(file_path, segment_root)},  # ← NO absolute path
    {...},
    ...,
)
```

### D.2 Redaction Filter for Diagnostics

**If LSP emits diagnostics with snippets, redact before logging:**

```python
def _redact_code_snippet(snippet: str) -> str:
    """Hash code, don't log actual content."""
    import hashlib
    return f"sha256:{hashlib.sha256(snippet.encode()).hexdigest()[:12]}"

# In DiagnosticsCollector
def _on_diagnostics(self, params):
    uri = params["uri"]
    diags = params.get("diagnostics", [])

    # Redact message if contains code
    for diag in diags:
        if "source" in diag and "message" in diag:
            diag["message"] = diag["message"][:100]  # Truncate
            # Don't log the actual error snippet

    self.diagnostics[uri] = diags
```

---

## PHASE E: TESTING REQUIREMENTS

### E.1 Unit Tests (Required)

**File:** `tests/unit/test_telemetry_ast_lsp.py` (NEW)

**Test cases:**

| Test | Objective | Assertion |
|------|-----------|-----------|
| `test_ast_event_uses_monotonic_clock` | Verify perf_counter_ns used | `timing_ms > 0`, no backwards jumps |
| `test_ast_event_redacts_absolute_path` | No /Users/.../ in logs | Relative path only in event |
| `test_lsp_ready_event_fires_on_diagnostics` | READY trigger correct | `cmd == "lsp.ready"` when publishDiagnostics received |
| `test_lsp_timeout_falls_back_to_tree_sitter` | Fallback on 500ms exceed | `lsp_timeout_count` incremented, result is fallback |
| `test_bytes_read_per_command_aggregated` | Bytes tracked per mode | `file_read_skeleton_bytes_total` in metrics.json |
| `test_event_extra_fields_serialized` | Extended fields in payload | `bytes_read`, `disclosure_mode` in events.jsonl |
| `test_no_lock_skip_on_critical_events` | Critical events don't drop | LSP ready, command start/end logged even if lock busy |
| `test_summary_calculates_p50_p95_correctly` | Aggregation math | Given dataset, p50 == median, p95 == 95th percentile |

**Example test:**
```python
def test_ast_event_uses_monotonic_clock(tmp_path):
    """Verify AST events use perf_counter_ns, not time.time()."""
    import json
    telemetry = Telemetry(tmp_path, level="lite")

    # Parse with instrumentation
    start_ns = time.perf_counter_ns()
    time.sleep(0.01)  # 10ms
    elapsed_ms = int((time.perf_counter_ns() - start_ns) / 1_000_000)

    telemetry.event(
        "ast.parse",
        {"file": "test.py"},
        {"status": "ok"},
        elapsed_ms,
    )
    telemetry.flush()

    # Read back event
    events_file = tmp_path / "_ctx" / "telemetry" / "events.jsonl"
    assert events_file.exists()

    with open(events_file) as f:
        event = json.loads(f.readline())

    # Assert timing is reasonable (10-20ms for the 10ms sleep + overhead)
    assert 8 <= event["timing_ms"] <= 30, f"Timing {event['timing_ms']}ms is unrealistic"
```

### E.2 Integration Tests (Required)

**File:** `tests/integration/test_lsp_instrumentation.py` (NEW)

**Test cases:**

| Test | Objective | Assertion |
|------|-----------|-----------|
| `test_full_search_flow_logs_all_metrics` | Search emits all events | events.jsonl has ctx.search, file.read, bytes_read |
| `test_lsp_lifecycle_complete` | Full LSP flow | lsp.spawn → lsp.initialize → lsp.ready → lsp.definition |
| `test_fallback_on_lsp_timeout` | Timeout → fallback path | lsp.timeout event + lsp_fallback_count incremented |
| `test_concurrent_commands_no_corruption` | Lock mechanism works | spawn 3 commands, all events logged, no duplicates/drops |
| `test_summary_consistency` | last_run.json math correct | sum of counters == metrics.json, p50 < p95, etc. |

**Example test:**
```python
def test_full_search_flow_logs_all_metrics(tmp_path, monkeypatch):
    """Verify search command emits bytes_read + disclosure metrics."""
    # Setup segment
    segment_dir = tmp_path / "test_segment"
    segment_dir.mkdir()
    ctx_dir = segment_dir / "_ctx"
    ctx_dir.mkdir()

    # Stub file system with small context pack
    pack_file = ctx_dir / "context_pack.json"
    pack_file.write_text(json.dumps({
        "index": {"test": ["chunk:1", "chunk:2"]},
        "chunks": {"chunk:1": {"content": "x" * 1000}}
    }))

    # Run search command
    from src.infrastructure.cli import ctx_search
    # ... invoke search("--segment", str(segment_dir), ...)

    # Verify events logged
    events_file = ctx_dir / "telemetry" / "events.jsonl"
    events = [json.loads(line) for line in events_file.read_text().strip().split("\n")]

    search_event = next((e for e in events if e["cmd"] == "ctx.search"), None)
    assert search_event is not None
    assert "bytes_read" in search_event  # NEW field
    assert search_event["bytes_read"] >= 1000  # At least pack size
```

### E.3 Synthetic Dataset for Summary Validation

**File:** `tests/fixtures/synthetic_telemetry.py` (NEW)

```python
def generate_synthetic_events(n_events: int) -> list[dict]:
    """Generate synthetic events for summary calculation validation."""
    events = []
    for i in range(n_events):
        events.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "run_id": f"run_{i}",
            "cmd": "ctx.search",
            "args": {"query": f"test{i}"},
            "result": {"hits": i % 10},
            "timing_ms": 10 + i % 100,  # 10–110ms range
        })
    return events

def test_summary_p50_p95_calculation():
    """Verify percentile math with synthetic data."""
    events = generate_synthetic_events(100)
    times = [e["timing_ms"] for e in events]
    times_sorted = sorted(times)

    p50_expected = times_sorted[50]  # Median
    p95_expected = times_sorted[int(100 * 0.95)]

    # ... call Telemetry.flush() and parse last_run.json ...

    assert last_run["latencies"]["ctx.search"]["p50_ms"] == p50_expected
    assert last_run["latencies"]["ctx.search"]["p95_ms"] == p95_expected
```

---

## PHASE F: DELIVERABLES CHECKLIST

### F.1 Code Changes

- [ ] **telemetry.py**: Extend `event()` to accept `**extra_fields` (5 lines)
- [ ] **telemetry.py**: Add AST/LSP/file_read summaries to `flush()` (30 lines)
- [ ] **ast_lsp.py**: NEW module with SkeletonMapBuilder, LSPClient, Selector (300+ lines)
  - [ ] Instrumentate `parse_python()` with perf_counter_ns
  - [ ] Instrumentate `send_request()` with perf_counter_ns
  - [ ] Instrumentate `_on_ready()` with cumulative timing
  - [ ] All event() calls use relative paths (via `_relative_path()`)
- [ ] **cli.py**: Add `bytes_read`, `disclosure_mode` fields to ctx.search/get events (10 lines)
- [ ] **file_system.py**: Track `total_bytes_read` per read mode (20 lines)

### F.2 Tests

- [ ] **test_telemetry_ast_lsp.py**: 8 unit tests (monotonic, redaction, ready trigger, aggregation)
- [ ] **test_lsp_instrumentation.py**: 5 integration tests (full flow, lifecycle, fallback, concurrency, consistency)
- [ ] **synthetic_telemetry.py**: 1 fixture + 1 validation test

### F.3 Documentation

- [ ] **docs/telemetry.md** (NEW or UPDATE existing):
  - [ ] Extend to document AST/LSP events
  - [ ] Document "READY" definition
  - [ ] Example: How to query last_run.json for LSP metrics
  - [ ] Security/redaction policy

---

## PHASE G: VALIDATION CRITERIA (PASS/FAIL)

| Criterion | Pass | Status |
|-----------|------|--------|
| **No second telemetry system created** | Only events.jsonl, metrics.json, last_run.json used | ✅ DESIGN COMPLIES |
| **All timings use perf_counter_ns** | No time.time() for intervals | ⏳ IMPLEMENTATION (T-TBD) |
| **No sensitive data logged** | Relative paths only, no file content, no API keys | ⏳ IMPLEMENTATION (T-TBD) |
| **LSP READY clearly defined** | Spec: initialized + (diagnostics OR definition success) | ✅ DESIGN COMPLIES |
| **Critical events not lossy** | lsp.ready, command.end, bytes_read must NOT drop | ⏳ IMPLEMENTATION (needs fallback queue) |
| **Bytes tracked per command** | metrics.json has file_read_*_bytes_total counters | ✅ DESIGN COMPLIES |
| **Fallback rate measurable** | lsp_timeout_count, lsp_fallback_count in summary | ✅ DESIGN COMPLIES |
| **Summary math correct** | p50/p95 calculated correctly on synthetic data | ⏳ TESTING (T-TBD) |
| **All tests pass** | 8 unit + 5 integration tests >80% pass | ⏳ TESTING (T-TBD) |

---

## IMPLEMENTATION ROADMAP (4–5 Days)

### Day 1: Telemetry Module Extension
- [ ] Extend `event()` signature in telemetry.py
- [ ] Add AST/LSP/file_read summaries to `flush()`
- [ ] Update **docs/telemetry.md** (new or existing)
- [ ] 3 unit tests for aggregation logic

### Day 2–3: AST/LSP Instrumentation
- [ ] Create **src/infrastructure/ast_lsp.py** with SkeletonMapBuilder + LSPClient + Selector (all with telemetry hooks)
- [ ] Update **cli.py** to emit bytes_read, disclosure_mode
- [ ] Update **file_system.py** to track total_bytes_read
- [ ] 5 unit tests (monotonic, redaction, ready, extra fields, counters)

### Day 4: Integration Tests
- [ ] Create **test_lsp_instrumentation.py** with 5 integration tests
- [ ] Create **synthetic_telemetry.py** fixture + validation test
- [ ] Run full suite: `pytest tests/ --cov=src` >80%

### Day 5: Review & Docs
- [ ] Code review (linting, type hints, docstrings)
- [ ] Final docs update (examples, queries, troubleshooting)
- [ ] Merge to main

---

## NOTES & CAVEATS

### N.1 Lock Skipping (Acceptable Risk)

The POSIX fcntl non-blocking lock is **lossy by design** (skip write if busy). This is **acceptable for telemetry** because:
1. **Not critical data**: Telemetry is best-effort observability, not transactional.
2. **Fail-safe**: Never corrupts events.jsonl; just drops the entire event.
3. **Measurable**: Drop count recorded in `telemetry_lock_skipped` warnings.

**However:** For MVP, ensure critical events (lsp.ready, command.end) use the **existing event() mechanism** (same lock as everything else) to maintain single failure mode.

### N.2 Monotonic Clock Conversion

`time.perf_counter_ns()` returns nanoseconds. Convert to milliseconds as:
```python
elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
```

Store as **integer** in `timing_ms` field for backward compatibility.

### N.3 Relative Path Redaction

Always use `Path.relative_to()` or fallback to `.name` (filename only) for telemetry:
```python
try:
    rel = path.relative_to(segment_root)
except ValueError:
    rel = path.name
telemetry.event(..., {"file": str(rel)}, ...)
```

### N.4 LSP READY Definition (Canonical)

**DO NOT invent new LSP protocol requests.** Instead, observe standard notifications:

```python
# Option A: publishDiagnostics (most reliable)
if initialized AND received_first_publishDiagnostics:
    ready = True

# Option B: textDocument/definition success
if initialized AND received_first_definition_response:
    ready = True

# Pick the FIRST condition that fires
```

---

## SUCCESS METRICS (Post-Implementation)

Once implemented, you should be able to run:

```bash
# Query last_run.json for AST metrics
cat _ctx/telemetry/last_run.json | jq '.ast'
# Output:
# {
#   "ast_parse_count": 42,
#   "ast_cache_hit_rate": 0.86
# }

# Query for LSP metrics
cat _ctx/telemetry/last_run.json | jq '.lsp'
# Output:
# {
#   "lsp_spawn_count": 3,
#   "lsp_ready_count": 3,
#   "lsp_timeout_count": 0,
#   "lsp_timeout_rate": 0.0,
#   "lsp_fallback_count": 0
# }

# Query for bytes by mode
cat _ctx/telemetry/last_run.json | jq '.file_read'
# Output:
# {
#   "skeleton_bytes": 8192,
#   "excerpt_bytes": 45678,
#   "raw_bytes": 123456,
#   "total_bytes": 177326
# }

# Query latencies
cat _ctx/telemetry/last_run.json | jq '.latencies."lsp.definition"'
# Output:
# {
#   "count": 5,
#   "p50_ms": 145.0,
#   "p95_ms": 289.0,
#   "max_ms": 512.0
# }
```

---

**Audit Complete:** 2026-01-01  
**Next Step:** Begin Day 1 implementation  
**Owner:** Senior Engineer / Telemetry Architect
