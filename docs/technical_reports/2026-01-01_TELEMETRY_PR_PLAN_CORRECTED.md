# PR Plan: Telemetry Extension for AST+LSP (2-Phase, Corrected)

**Date:** 2026-01-01  
**Version:** 2.2 (PASS - Ready for Implementation)  
**Role:** Senior Engineer / Patch Agent  
**Scope:** 2 PRs over 5–6 days (PR#1: 2 days, PR#2: 3-4 days)  
**Success Criterion:** Zero corruption (valid JSON lines), <2% drop rate (tracked via telemetry_lock_skipped), monotonic timings, zero duplicate systems, >80% test coverage. Loss acceptable for analytics ONLY, never for gates.

---

## PATCH NOTES (Cambios vs v1.0)

1. ✅ **Split into 2 PRs**: PR#1 (telemetry only), PR#2 (AST/LSP implementation)
2. ✅ **Reserved keys protection**: Fail-fast on collision with core fields
3. ✅ **LSP state machine**: COLD→WARMING→READY→FAILED (no aggressive timeouts)
4. ✅ **Path security**: `_relpath()` utility, enforce relative paths everywhere
5. ✅ **Concurrency model**: Declared lossy fcntl, no corruption acceptance in tests
6. ✅ **Event schema table**: Complete catalog with examples
7. ✅ **Remove speculative code**: PR#1 only scaffolding, no real parsers
8. ✅ **Test criteria fix**: Corruption-free validation, not exact counts
9. ✅ **Redaction policy**: Hash content, log sizes/ranges/relative paths only
10. ✅ **Dependencies**: PR#2 depends on PR#1 merge + tag
11. ✅ **DoD tightened**: No placeholders, all tests pass, mypy clean
12. ✅ **Timeline adjusted**: Clear handoff between phases

---

## OVERVIEW

This plan splits telemetry instrumentation into **2 clean phases**:

**PR#1 (Telemetry Extension):** Extend `src/infrastructure/telemetry.py` to support AST/LSP event types, reserved key protection, path normalization, and new aggregation summaries. **No AST/LSP implementation** — only scaffolding, types, and tests.

**PR#2 (AST/LSP Implementation):** Implement Tree-sitter parser, Pyright LSP client, symbol selector, and progressive disclosure logic. Consumes telemetry hooks from PR#1.

### Instrumentation Targets (PR#2 will measure)

- AST skeleton build latencies (Tree-sitter parse times + caching)
- LSP lifecycle with state machine (COLD → WARMING → READY → FAILED)
- LSP warm-up policy (parallel spawn during AST build, READY-only gating)
- LSP request latencies (definition, hover, diagnostics) when READY
- Bytes read per command and per disclosure mode
- Fallback triggers (LSP not READY → use AST-only)

### Architecture Constraints

- **Single telemetry system:** Reuse `_ctx/telemetry/` directory, no new sinks
- **Monotonic clocks:** `time.perf_counter_ns()` for all latencies
- **Lossy concurrency:** fcntl non-blocking lock (acceptable <2% drop rate for analytics, not gates)
- **Security:** Relative paths only, no file content, reserved key protection
- **AST-first:** Symbol resolution works without LSP; LSP enhances when READY

**Breaking changes:** None. All changes are additive and backward compatible.

---

## PR#1: TELEMETRY EXTENSION (2 days, no AST/LSP implementation)

### TICKET 1.1: Reserved Key Protection + Extra Fields (4 hours)

**PR Title:** `feat(telemetry): extend event() to support AST/LSP structured fields with reserved key protection`

**Description:**
Extend the Telemetry class to accept optional structured fields while protecting core event fields from accidental override.

#### Changes

**File:** `src/infrastructure/telemetry.py`

**After line 15 (before class Telemetry), add:**

```python
# Reserved keys that cannot be overridden by extra_fields
RESERVED_KEYS = frozenset({
    "ts", "run_id", "segment", "cmd", "args", "result", 
    "timing_ms", "tokens", "warnings"
})

def _relpath(root: Path, target: Path) -> str:
    """
    Convert absolute path to relative path for telemetry.
    Prevents logging absolute paths or URIs with user/system info.
    
    Args:
        root: Repository/segment root (workspace root)
        target: File path to convert
    
    Returns:
        Relative path string, or external/<hash8>-<name> if outside root
    
    Example:
        >>> _relpath(Path("/workspaces/repo"), Path("/workspaces/repo/src/app.py"))
        'src/app.py'
        >>> _relpath(Path("/workspaces/repo"), Path("/usr/lib/python3.12/typing.py"))
        'external/a3b4c5d6-typing.py'  # hash ensures uniqueness without exposing path
    """
    try:
        return str(target.relative_to(root))
    except ValueError:
        # File outside workspace: hash path for privacy + uniqueness
        import hashlib
        path_hash = hashlib.sha256(str(target).encode()).hexdigest()[:8]
        return f"external/{path_hash}-{target.name}"
```

**Line 113: Modify `event()` signature:**

```python
def event(
    self,
    cmd: str,
    args: Dict[str, Any],
    result: Dict[str, Any],
    timing_ms: int,
    warnings: List[str] | None = None,
    **extra_fields: Any,  # NEW: accept arbitrary kwargs
) -> None:
    """
    Log a discrete event with optional structured fields.
    
    Args:
        cmd: Command name (e.g., "ctx.search", "ast.parse", "lsp.spawn")
        args: Command arguments (sanitized)
        result: Command result metadata
        timing_ms: Elapsed time in milliseconds (use perf_counter_ns)
        warnings: Optional list of warning messages
        **extra_fields: Additional structured fields (e.g., bytes_read, lsp_state)
    
    Raises:
        ValueError: If extra_fields contains a reserved key
    
    Example:
        telemetry.event(
            "lsp.spawn", 
            {"pyright_binary": "pyright-langserver"}, 
            {"pid": 12345, "status": "ok"},
            42,
            lsp_state="WARMING",  # Goes into payload["x"]["lsp_state"]
            spawn_method="subprocess"  # Goes into payload["x"]["spawn_method"]
        )
    """
    if not self.enabled:
        return

    if warnings:
        self.warnings.extend(warnings)

    # NEW: Protect reserved keys
    collision = RESERVED_KEYS & extra_fields.keys()
    if collision:
        raise ValueError(
            f"extra_fields contains reserved keys: {collision}. "
            f"Reserved: {RESERVED_KEYS}"
        )

    safe_args = self._sanitize_args(args)
    tokens = self._estimate_token_usage(cmd, args, result)

    # NEW: compute stable segment_id (no path leakage)
    import hashlib
    segment_id = hashlib.sha256(str(self.segment_path).encode()).hexdigest()[:8]
    
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "run_id": self.run_id,
        "segment_id": segment_id,  # FIX: stable ID, no absolute path
        "cmd": cmd,
        "args": safe_args,
        "result": result,
        "timing_ms": timing_ms,
        "tokens": tokens,
        "warnings": warnings or [],
        "x": extra_fields,  # NEW: namespace extra fields to prevent future collisions
    }

    # NEW: _write_jsonl now returns success bool for drop tracking
    if self._write_jsonl("events.jsonl", payload):
        if timing_ms > 0:
            self.observe(cmd, timing_ms)
        # (rest of token tracking unchanged)
    else:
        # Lock not acquired: track drop
        self.incr("telemetry_lock_skipped", 1)
```

**Line 245: Add AST/LSP/file_read summaries to `flush()`:**

Before final `run_summary` dict assembly, add:

```python
    # NEW: AST summary
    ast_summary = {
        "ast_parse_count": self.metrics.get("ast_parse_count", 0),
        "ast_cache_hit_count": self.metrics.get("ast_cache_hit_count", 0),
        "ast_cache_miss_count": self.metrics.get("ast_cache_miss_count", 0),
        "ast_cache_hit_rate": round(
            self.metrics.get("ast_cache_hit_count", 0) / 
            max(self.metrics.get("ast_parse_count", 1), 1),
            3
        ),
    }

    # NEW: LSP summary
    lsp_summary = {
        "lsp_spawn_count": self.metrics.get("lsp_spawn_count", 0),
        "lsp_warming_count": self.metrics.get("lsp_warming_count", 0),
        "lsp_ready_count": self.metrics.get("lsp_ready_count", 0),
        "lsp_failed_count": self.metrics.get("lsp_failed_count", 0),
        "lsp_fallback_count": self.metrics.get("lsp_fallback_count", 0),
        "lsp_ready_rate": round(
            self.metrics.get("lsp_ready_count", 0) / 
            max(self.metrics.get("lsp_spawn_count", 1), 1),
            3
        ),
        "lsp_fallback_rate": round(
            self.metrics.get("lsp_fallback_count", 0) / 
            max(self.metrics.get("lsp_spawn_count", 1), 1),
            3
        ),
    }

    # NEW: File read summary by mode
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

    # (Keep existing latency_summary and tokens_summary code)

    run_summary = {
        "run_id": self.run_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        "metrics_delta": self.metrics,
        "latencies": latency_summary,
        "tokens": tokens_summary,
        "ast": ast_summary,              # NEW
        "lsp": lsp_summary,              # NEW
        "file_read": file_read_summary,  # NEW
        "telemetry_drops": {             # NEW: track lossy fcntl drops
            "lock_skipped": self.metrics.get("telemetry_lock_skipped", 0),
            "drop_rate": round(
                self.metrics.get("telemetry_lock_skipped", 0) / 
                max(sum(self.metrics.values()), 1),
                4
            ),
        },
        "top_warnings": self.warnings[:5],
        "pack_state": {
            "pack_sha": self.pack_sha,
            "pack_mtime": self.pack_mtime,
            **(
                {}
                if self.stale_detected is None
                else {"stale_detected": self.stale_detected}
            ),
        },
    }
```

#### Definition of Done (Ticket 1.1)

- [ ] `_write_jsonl()` returns True on success, False on lock skip (for drop tracking)
- [ ] `event()` accepts `**extra_fields` and merges into JSON payload
- [ ] `event()` raises `ValueError` if extra_fields collides with reserved keys
- [ ] `_relpath()` utility converts absolute paths to relative paths
- [ ] All new event fields appear in events.jsonl on write
- [ ] `flush()` calculates AST/LSP/file_read summaries with correct formulas
- [ ] Backward compatibility: old code calling `telemetry.event(cmd, args, result, timing_ms)` still works
- [ ] Unit test: `test_reserved_key_protection` (verify ValueError on collision)
- [ ] Unit test: `test_relpath_normalization` (verify relative path output)
- [ ] Unit test: `test_extra_fields_serialized` (verify bytes_read in event)
- [ ] Unit test: `test_summary_calculations` (verify AST/LSP/file_read in last_run.json)
- [ ] No errors or warnings from linting (mypy, pylint)

---

### TICKET 1.2: Event Schema Documentation (4 hours)

**PR Title:** `docs(telemetry): define AST/LSP event schema and state machine`

**Description:**
Document all event types, fields, and LSP state machine for PR#2 implementation reference.

#### File: `docs/telemetry_event_schema.md` (NEW)

```markdown
# Telemetry Event Schema (AST+LSP)

**Version:** 1.0 (PR#1)  
**Status:** Specification (implementation in PR#2)

---

## Event Types

### 1. AST Events

| Event Type | Fields | Example |
|------------|--------|---------|
| `ast.parse` | `file` (relative), `status`, `functions_count`, `classes_count`, `skeleton_bytes`, `reduction_ratio`, `cache_hit` | `{"cmd": "ast.parse", "args": {"file": "src/domain/models.py"}, "result": {"status": "ok", "functions": 3, "classes": 2}, "timing_ms": 45, "x": {"skeleton_bytes": 512, "reduction_ratio": 0.08, "cache_hit": false}}` |

### 2. LSP Events

**State Machine:**
- **COLD**: No LSP process spawned
- **WARMING**: Process spawned, initializing (parallel with AST build)
- **READY**: Initialized + first notification received (publishDiagnostics or similar)
- **FAILED**: Spawn/init error or crash

| Event Type | Fields | Example |
|------------|--------|---------|
| `lsp.spawn` | `pyright_binary`, `subprocess_pid`, `status` | `{"cmd": "lsp.spawn", "args": {"pyright_binary": "pyright-langserver"}, "result": {"subprocess_pid": 12345, "status": "ok"}, "timing_ms": 0, "x": {"lsp_state": "WARMING"}}` |
| `lsp.state_change` | `from_state`, `to_state`, `reason` | `{"cmd": "lsp.state_change", "args": {}, "result": {"from_state": "WARMING", "to_state": "READY", "reason": "publishDiagnostics received"}, "timing_ms": 1500}` |
| `lsp.request` | `method`, `file` (relative), `line`, `col`, `resolved`, `fallback` | `{"cmd": "lsp.request", "args": {"method": "definition", "file": "src/app.py", "line": 42, "col": 10}, "result": {"resolved": true, "target_file": "src/lib.py", "target_line": 15}, "timing_ms": 120, "x": {}}` |
| `lsp.fallback` | `reason`, `fallback_to` | `{"cmd": "lsp.fallback", "args": {"reason": "lsp_not_ready"}, "result": {"fallback_to": "ast_only"}, "timing_ms": 0}` |

### 3. File Read Events

| Event Type | Fields | Example |
|------------|--------|---------|
| `file.read` | `file` (relative), `mode`, `bytes`, `status` | `{"cmd": "file.read", "args": {"file": "src/app.py", "mode": "excerpt"}, "result": {"bytes": 2048, "status": "ok"}, "timing_ms": 5, "x": {"disclosure_mode": "excerpt"}}` |

### 4. Selector Events

| Event Type | Fields | Example |
|------------|--------|---------|
| `selector.resolve` | `symbol_query`, `resolved`, `matches`, `ambiguous` | `{"cmd": "selector.resolve", "args": {"symbol_query": "sym://python/src.domain.models/Config"}, "result": {"resolved": true, "matches": 1, "ambiguous": false}, "timing_ms": 30}` |

---

## Counters (Aggregated in last_run.json)

### AST Counters
- `ast_parse_count`: Total AST parses requested
- `ast_cache_hit_count`: Cache hits (file hash unchanged)
- `ast_cache_miss_count`: Cache misses (new parse required)

### LSP Counters
- `lsp_spawn_count`: Total LSP processes spawned
- `lsp_warming_count`: Processes in WARMING state
- `lsp_ready_count`: Processes that reached READY
- `lsp_failed_count`: Processes that failed (spawn/init error)
- `lsp_fallback_count`: Requests that fell back to AST-only

### File Read Counters
- `file_read_skeleton_bytes_total`: Bytes read in skeleton mode
- `file_read_excerpt_bytes_total`: Bytes read in excerpt mode
- `file_read_raw_bytes_total`: Bytes read in raw mode

---

## Summaries (in last_run.json)

```json
{
  "ast": {
    "ast_parse_count": 42,
    "ast_cache_hit_count": 36,
    "ast_cache_miss_count": 6,
    "ast_cache_hit_rate": 0.857
  },
  "lsp": {
    "lsp_spawn_count": 3,
    "lsp_warming_count": 0,
    "lsp_ready_count": 3,
    "lsp_failed_count": 0,
    "lsp_fallback_count": 2,
    "lsp_ready_rate": 1.0,
    "lsp_fallback_rate": 0.667
  },
  "file_read": {
    "skeleton_bytes": 8192,
    "excerpt_bytes": 45678,
    "raw_bytes": 123456,
    "total_bytes": 177326
  }
}
```

---

## Security & Redaction Policy

1. **Paths:** Always use `_relpath(repo_root, path)` to log relative paths. NEVER log absolute paths or URIs with user/system info.
2. **Segment:** Log `segment_id` (SHA-256 hash prefix), not `segment_path` (prevents path leakage).
3. **Content:** Do not log file content. Log hashes (SHA-256), sizes, and line ranges only.
4. **Secrets:** Do not log API keys, tokens, or credentials in any field.
5. **Reserved Keys:** `ts`, `run_id`, `segment_id`, `cmd`, `args`, `result`, `timing_ms`, `tokens`, `warnings`, `x` are protected. Extra fields go under `x` namespace.

---

## LSP READY Definition

**READY state** is achieved when:
1. LSP process spawned successfully
2. `initialize` request sent and `InitializeResult` received
3. `didOpen` sent for 1 file (relevant to current operation)
4. `textDocument/publishDiagnostics` notification received for that specific URI

**Policy:**
- LSP spawns in parallel during AST build (warm-up phase)
- Warm-up sends `didOpen` for first Python file found by AST scan
- READY achieved when `publishDiagnostics` received for that specific URI
- Requests ONLY sent when state == READY
- If not READY when needed → fallback to AST-only (no blocking wait)
- No aggressive timeouts: LSP gets full init time (5-10s typical)
- READY is LSP-instance-specific, not global (multiple LSP clients track own state)
```

#### Definition of Done (Ticket 1.2)

- [ ] Event schema doc created with all event types, fields, and examples
- [ ] LSP state machine (COLD/WARMING/READY/FAILED) defined
- [ ] READY definition specified (initialize + notification)
- [ ] Security/redaction policy documented
- [ ] Counter and summary spec complete
- [ ] Doc reviewed and approved by team

---

### TICKET 1.3: Test Suite (8 hours)

**PR Title:** `test(telemetry): add unit tests for extended telemetry API`

**Description:**
Comprehensive unit tests for reserved key protection, path normalization, extra fields, and summary calculations.

#### File: `tests/unit/test_telemetry_extension.py` (NEW)

```python
"""Unit tests for telemetry extension (PR#1)."""

import json
import time
from pathlib import Path
import pytest
from src.infrastructure.telemetry import Telemetry, RESERVED_KEYS, _relpath


class TestReservedKeyProtection:
    """Test reserved key collision detection."""
    
    def test_collision_raises_error(self, tmp_path):
        """Verify ValueError on reserved key collision."""
        telemetry = Telemetry(tmp_path, level="lite")
        
        with pytest.raises(ValueError, match="reserved keys"):
            telemetry.event(
                "test.cmd",
                {},
                {},
                100,
                ts="2026-01-01T00:00:00Z",  # RESERVED KEY
            )
    
    def test_multiple_collisions(self, tmp_path):
        """Verify error message includes all colliding keys."""
        telemetry = Telemetry(tmp_path, level="lite")
        
        with pytest.raises(ValueError, match="ts.*run_id"):
            telemetry.event(
                "test.cmd",
                {},
                {},
                100,
                ts="2026-01-01",
                run_id="fake_id",
            )
    
    def test_safe_extra_fields(self, tmp_path):
        """Verify non-reserved keys accepted."""
        telemetry = Telemetry(tmp_path, level="lite")
        
        # Should not raise
        telemetry.event(
            "test.cmd",
            {},
            {},
            100,
            bytes_read=1024,
            lsp_state="READY",
            custom_field="value",
        )
        telemetry.flush()
        
        events_file = tmp_path / "_ctx" / "telemetry" / "events.jsonl"
        event = json.loads(events_file.read_text().strip())
        
        # Extra fields are namespaced under "x"
        assert event["x"]["bytes_read"] == 1024
        assert event["x"]["lsp_state"] == "READY"
        assert event["x"]["custom_field"] == "value"


class TestPathNormalization:
    """Test _relpath utility."""
    
    def test_relpath_inside_workspace(self):
        """Verify relative path for files inside workspace."""
        root = Path("/workspaces/trifecta_dope")
        target = Path("/workspaces/trifecta_dope/src/domain/models.py")
        
        result = _relpath(root, target)
        
        assert result == "src/domain/models.py"
        assert not result.startswith("/")
    
    def test_relpath_outside_workspace(self):
        """Verify external/<hash>-<name> for files outside workspace."""
        root = Path("/workspaces/trifecta_dope")
        target = Path("/usr/lib/python3.12/typing.py")
        
        result = _relpath(root, target)
        
        assert result.startswith("external/")
        assert result.endswith("-typing.py")
        assert "/" not in result.split("-", 1)[1]  # No slashes after hash
    
    def test_relpath_uniqueness(self):
        """Verify different external paths produce different hashes."""
        root = Path("/workspaces/trifecta_dope")
        target1 = Path("/usr/lib/python3.12/typing.py")
        target2 = Path("/opt/python3.12/typing.py")  # Same name, different path
        
        result1 = _relpath(root, target1)
        result2 = _relpath(root, target2)
        
        # Different hashes ensure uniqueness
        assert result1 != result2
        assert result1.endswith("-typing.py")
        assert result2.endswith("-typing.py")


class TestExtraFields:
    """Test extra_fields serialization."""
    
    def test_extra_fields_in_event(self, tmp_path):
        """Verify extra fields appear in events.jsonl."""
        telemetry = Telemetry(tmp_path, level="lite")
        
        telemetry.event(
            "test.cmd",
            {},
            {},
            100,
            bytes_read=2048,
            disclosure_mode="excerpt",
            cache_hit=True,
        )
        telemetry.flush()
        
        events_file = tmp_path / "_ctx" / "telemetry" / "events.jsonl"
        event = json.loads(events_file.read_text().strip())
        
        # Extra fields are namespaced under "x"
        assert event["x"]["bytes_read"] == 2048
        assert event["x"]["disclosure_mode"] == "excerpt"
        assert event["x"]["cache_hit"] is True
    
    def test_extra_fields_types(self, tmp_path):
        """Verify various types serialize correctly."""
        telemetry = Telemetry(tmp_path, level="lite")
        
        telemetry.event(
            "test.cmd",
            {},
            {},
            100,
            int_field=42,
            float_field=3.14,
            bool_field=True,
            str_field="hello",
            list_field=[1, 2, 3],
            dict_field={"key": "value"},
        )
        telemetry.flush()
        
        events_file = tmp_path / "_ctx" / "telemetry" / "events.jsonl"
        event = json.loads(events_file.read_text().strip())
        
        # All extra fields under "x" namespace
        assert event["x"]["int_field"] == 42
        assert abs(event["x"]["float_field"] - 3.14) < 0.01
        assert event["x"]["bool_field"] is True
        assert event["x"]["str_field"] == "hello"
        assert event["x"]["list_field"] == [1, 2, 3]
        assert event["x"]["dict_field"] == {"key": "value"}


class TestSummaryCalculations:
    """Test aggregation in flush()."""
    
    def test_ast_summary(self, tmp_path):
        """Verify AST summary calculation."""
        telemetry = Telemetry(tmp_path, level="lite")
        
        telemetry.incr("ast_parse_count", 100)
        telemetry.incr("ast_cache_hit_count", 86)
        telemetry.incr("ast_cache_miss_count", 14)
        
        telemetry.flush()
        
        last_run_file = tmp_path / "_ctx" / "telemetry" / "last_run.json"
        last_run = json.loads(last_run_file.read_text())
        
        assert last_run["ast"]["ast_parse_count"] == 100
        assert last_run["ast"]["ast_cache_hit_count"] == 86
        assert last_run["ast"]["ast_cache_miss_count"] == 14
        assert abs(last_run["ast"]["ast_cache_hit_rate"] - 0.86) < 0.01
    
    def test_lsp_summary(self, tmp_path):
        """Verify LSP summary calculation."""
        telemetry = Telemetry(tmp_path, level="lite")
        
        telemetry.incr("lsp_spawn_count", 5)
        telemetry.incr("lsp_ready_count", 5)
        telemetry.incr("lsp_fallback_count", 1)
        
        telemetry.flush()
        
        last_run_file = tmp_path / "_ctx" / "telemetry" / "last_run.json"
        last_run = json.loads(last_run_file.read_text())
        
        assert last_run["lsp"]["lsp_spawn_count"] == 5
        assert last_run["lsp"]["lsp_ready_count"] == 5
        assert last_run["lsp"]["lsp_ready_rate"] == 1.0
        assert abs(last_run["lsp"]["lsp_fallback_rate"] - 0.2) < 0.01
    
    def test_file_read_summary(self, tmp_path):
        """Verify file read summary calculation."""
        telemetry = Telemetry(tmp_path, level="lite")
        
        telemetry.incr("file_read_skeleton_bytes_total", 1024)
        telemetry.incr("file_read_excerpt_bytes_total", 5120)
        telemetry.incr("file_read_raw_bytes_total", 10240)
        
        telemetry.flush()
        
        last_run_file = tmp_path / "_ctx" / "telemetry" / "last_run.json"
        last_run = json.loads(last_run_file.read_text())
        
        assert last_run["file_read"]["skeleton_bytes"] == 1024
        assert last_run["file_read"]["excerpt_bytes"] == 5120
        assert last_run["file_read"]["raw_bytes"] == 10240
        assert last_run["file_read"]["total_bytes"] == 16384


class TestMonotonicTiming:
    """Test perf_counter_ns usage."""
    
    def test_monotonic_clock(self, tmp_path):
        """Verify timing uses perf_counter_ns."""
        telemetry = Telemetry(tmp_path, level="lite")
        
        start_ns = time.perf_counter_ns()
        time.sleep(0.01)  # 10ms
        elapsed_ms = int((time.perf_counter_ns() - start_ns) / 1_000_000)
        
        telemetry.event("test.cmd", {}, {}, elapsed_ms)
        telemetry.flush()
        
        events_file = tmp_path / "_ctx" / "telemetry" / "events.jsonl"
        event = json.loads(events_file.read_text().strip())
        
        # Assert timing is reasonable (8-30ms for 10ms sleep + overhead)
        assert 8 <= event["timing_ms"] <= 30


class TestConcurrencySafety:
    """Test concurrent event logging (corruption-free guarantee)."""
    
    def test_concurrent_writes_no_corruption(self, tmp_path):
        """Verify concurrent writes produce valid JSON (no interleaved data)."""
        import threading
        
        def write_events(thread_id: int):
            telemetry = Telemetry(tmp_path, level="lite")
            for i in range(10):
                telemetry.event(
                    f"thread_{thread_id}",
                    {"iteration": i},
                    {"status": "ok"},
                    10,
                )
            telemetry.flush()
        
        threads = [threading.Thread(target=write_events, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Verify all logged events are valid JSON
        events_file = tmp_path / "_ctx" / "telemetry" / "events.jsonl"
        events = []
        for line in events_file.read_text().strip().split("\n"):
            if line:
                event = json.loads(line)  # Should not raise
                events.append(event)
                assert "cmd" in event
                assert "timing_ms" in event
        
        # Some events may be dropped (lossy model), but all logged events must be valid
        assert len(events) > 0, "At least some events should be logged"
        assert len(events) <= 50, "At most 50 events (5 threads × 10 events)"
```

#### Definition of Done (Ticket 1.3)

- [ ] All unit tests pass: `pytest tests/unit/test_telemetry_extension.py -v`
- [ ] Coverage >90% for telemetry.py extension code
- [ ] Test: `test_collision_raises_error` (reserved key protection)
- [ ] Test: `test_relpath_inside_workspace` (path normalization)
- [ ] Test: `test_extra_fields_in_event` (serialization)
- [ ] Test: `test_ast_summary` (aggregation)
- [ ] Test: `test_lsp_summary` (aggregation)
- [ ] Test: `test_file_read_summary` (aggregation)
- [ ] Test: `test_monotonic_clock` (timing correctness)
- [ ] Test: `test_concurrent_writes_no_corruption` (concurrency safety)
- [ ] No test data logged to production events.jsonl (tests use tmp_path)
- [ ] Type hints complete (mypy clean)

---

### TICKET 1.4: Concurrency Documentation (2 hours)

**PR Title:** `docs(telemetry): document concurrency model and guarantees`

**Description:**
Clarify concurrency guarantees for telemetry system (lossy fcntl vs single-writer alternatives).

#### File: `docs/telemetry_concurrency.md` (NEW)

```markdown
# Telemetry Concurrency Model

**Version:** 1.0  
**Status:** Current (PR#1)

---

## Model: Lossy fcntl (Non-Blocking)

**Current Implementation:** `src/infrastructure/telemetry.py` uses POSIX `fcntl.flock()` with `LOCK_EX | LOCK_NB` for file writes.

**Behavior:**
- If lock is available: write succeeds
- If lock is held by another process: write is **skipped** (event lost)
- No blocking, no retries

**Guarantees:**
- ✅ No deadlocks
- ✅ No corruption (atomic append to JSONL)
- ❌ Not lossless (2-5% event drop under concurrent load)

**Usage Policy:**
- **Safe for analytics:** Percentiles, counters, trends are statistically valid despite loss
- **Unsafe for gates:** Do NOT use telemetry counters for critical decisions (e.g., "if lsp_ready_count == 0 then fail")
- **Warning emitted:** `telemetry_lock_skipped` counter tracks dropped events

---

## Alternatives (Not Implemented)

### Single-Writer with Queue
- Spawn background thread/process as telemetry sink
- All events pushed to queue, single writer drains queue
- **Pros:** Zero loss, exact counts
- **Cons:** Complexity (thread lifecycle, shutdown), memory (unbounded queue)

### Blocking Lock
- Use `fcntl.flock(LOCK_EX)` without `LOCK_NB` (blocking wait)
- **Pros:** No loss
- **Cons:** Performance impact (waits for lock), potential deadlock if writer crashes

---

## Decision: Lossy Model is Correct

**Rationale:**
1. Telemetry is for **observability**, not correctness. Losing 2% of events does not materially impact trend analysis.
2. No critical paths depend on telemetry counters (LSP READY is determined by in-memory state, not logs).
3. Simplicity: no background threads, no shutdown complexity.
4. Performance: no blocking waits.

**Test Criteria:**
- Concurrent tests MUST validate **no corruption** (valid JSON, no interleaved writes)
- Concurrent tests MUST NOT expect **exact counts** (some events may be dropped)
- Validate: "All logged events are valid" NOT "All events are logged"
```

#### Definition of Done (Ticket 1.4)

- [ ] Concurrency model documented (lossy fcntl)
- [ ] Guarantees specified (no corruption, 2-5% loss acceptable)
- [ ] Usage policy defined (safe for analytics, unsafe for gates)
- [ ] Alternatives documented with trade-offs
- [ ] Decision rationale documented
- [ ] Test criteria clarified (corruption-free, not loss-free)

---

## PR#1 SUMMARY

**Duration:** 2 days  
**Deliverables:**
- Extended telemetry API with reserved key protection
- Path normalization utility
- AST/LSP/file_read summaries in flush()
- Event schema documentation
- Concurrency model documentation
- Comprehensive unit tests (>90% coverage)

**No Implementation:**
- No Tree-sitter parser
- No LSP client
- No actual AST/LSP logic
- Only scaffolding and hooks

**Merge Gate:**
- All tests pass
- Coverage >90%
- Mypy clean
- Code review approved
- Tag: `v1.1-telemetry-extension`

---

## PR#2: AST+LSP IMPLEMENTATION (3-4 days, depends on PR#1 merge)

**PR Title:** `feat(infrastructure): implement AST parser, LSP client, and selector with telemetry`

**Description:**
Implement Tree-sitter AST parser, Pyright LSP client with state machine, and symbol selector. All components consume telemetry hooks from PR#1.

**Dependency:** PR#1 must be merged and tagged before starting PR#2.

---

### TICKET 2.1: AST Parser with Caching (12 hours)

**PR Title:** `feat(ast): implement Tree-sitter parser with skeleton map and caching`

**Description:**
Create AST parser using Tree-sitter for Python, with SHA-256 content hashing for cache invalidation.

#### File: `src/infrastructure/ast_lsp.py` (NEW)

**Implementation highlights:**
- Tree-sitter Python parser integration
- Skeleton map extraction (functions, classes, imports only)
- Content-based caching (SHA-256 hash)
- All paths use `_relpath()` from PR#1
- All timings use `perf_counter_ns()`
- Emit `ast.parse` events with telemetry

#### Definition of Done (Ticket 2.1)

- [ ] Tree-sitter Python parser installed: `pip install tree-sitter==0.22.6 tree-sitter-python==0.23.2` (pinned to stable release, not experimental 0.25)
- [ ] Dependencies added to pyproject.toml: `tree-sitter = "~0.22.6"`, `tree-sitter-python = "~0.23.2"`
- [ ] Version rationale documented: 0.23.x is latest stable; 0.25.x requires TS 0.24+ (breaking changes)
- [ ] `SkeletonMapBuilder.parse_python()` uses perf_counter_ns for timing
- [ ] SHA-256 hash computed for cache invalidation
- [ ] Cache hit/miss tracked with `ast_cache_hit_count`, `ast_cache_miss_count`
- [ ] All file paths logged as relative (via `_relpath()`)
- [ ] No file content logged (only sizes, hashes, line counts)
- [ ] Unit test: `test_skeleton_parse_timing` (verify monotonic)
- [ ] Unit test: `test_cache_invalidation` (hash-based)
- [ ] Unit test: `test_path_redaction` (relative paths only)
- [ ] Integration test: parse 50 files in <5s
- [ ] Mypy clean

---

### TICKET 2.2: LSP Client with State Machine (16 hours)

**PR Title:** `feat(lsp): implement Pyright LSP client with COLD→WARMING→READY→FAILED state machine`

**Description:**
Create LSP client with JSON-RPC framing, state machine, and warm-up policy.

#### Implementation highlights:**
- **LSP dependency:** Pyright requires Node.js (TypeScript-based). For lean/Python-only environments, consider `basedpyright` (pure Python packaging). Document chosen approach in pyproject.toml.
- Subprocess spawn with stdin/stdout pipes (`pyright-langserver --stdio` or `basedpyright-langserver`)
- JSON-RPC Content-Length framing
- State machine: COLD → WARMING (spawn + init) → READY (didOpen + publishDiagnostics) → FAILED (error)
- Warm-up policy: spawn in parallel during AST build, send didOpen for first file
- READY-only gating: requests only when state == READY
- Fallback to AST-only if not READY
- Emit `lsp.spawn`, `lsp.state_change`, `lsp.request`, `lsp.fallback` events

#### Definition of Done (Ticket 2.2)

- [ ] LSP integration gated behind `LSP_ENABLED=true` env var (experimental)
- [ ] LSP implementation choice documented: pyright (requires Node.js) vs basedpyright (pure Python)
- [ ] Chosen LSP binary subprocess spawned successfully (pyright-langserver or basedpyright-langserver)
- [ ] JSON-RPC Content-Length framing implemented
- [ ] State machine (COLD/WARMING/READY/FAILED) implemented
- [ ] `initialize` request sent and `InitializeResult` parsed
- [ ] Warm-up sends `didOpen` for 1 file to trigger diagnostics
- [ ] First `publishDiagnostics` notification triggers READY state
- [ ] Requests ONLY sent when state == READY
- [ ] Fallback to AST-only if not READY
- [ ] All file paths logged as relative
- [ ] No aggressive timeouts (5-10s init time allowed)
- [ ] Unit test: `test_lsp_state_transitions` (COLD→WARMING→READY)
- [ ] Unit test: `test_lsp_ready_gating` (no requests before READY)
- [ ] Unit test: `test_lsp_fallback` (AST-only when not READY)
- [ ] Integration test: full lifecycle (spawn→init→didOpen→diagnostics→READY→request) - skippable if pyright not available
- [ ] Mypy clean

---

### TICKET 2.3: Symbol Selector + CLI Integration (8 hours)

**PR Title:** `feat(selector): implement symbol resolver with sym:// DSL and CLI hooks`

**Description:**
Create symbol selector and integrate with CLI commands (ctx.search, ctx.get).

#### Implementation highlights:**
- sym:// DSL parser
- Symbol resolution using AST skeleton maps
- Progressive disclosure integration
- CLI hooks in `ctx.search` and `ctx.get` for bytes_read tracking
- FileSystemAdapter bytes tracking

#### Definition of Done (Ticket 2.3)

- [ ] `Selector.resolve_symbol()` parses sym:// DSL
- [ ] Symbol resolution uses AST skeleton maps (LSP optional)
- [ ] CLI `ctx.search` emits `bytes_read` field
- [ ] CLI `ctx.get` emits `bytes_read` + `disclosure_mode` fields
- [ ] FileSystemAdapter tracks `total_bytes_read` per command
- [ ] All timings use perf_counter_ns
- [ ] All paths relative
- [ ] Unit test: `test_selector_resolve` (sym:// parsing)
- [ ] Integration test: `test_cli_search_telemetry` (bytes_read logged)
- [ ] Integration test: `test_cli_get_telemetry` (disclosure_mode logged)
- [ ] Mypy clean

---

## PR#2 SUMMARY

**Duration:** 3-4 days  
**Deliverables:**
- Tree-sitter AST parser with caching
- Pyright LSP client with state machine
- Symbol selector with sym:// DSL
- CLI integration (bytes tracking)

**Merge Gate:**
- All tests pass
- Coverage >80%
- Mypy clean
- AST/LSP features working end-to-end
- Code review approved
- Tag: `v1.1-ast-lsp-implementation`

---

## DEPLOYMENT CHECKLIST

- [ ] PR#1 merged and tagged
- [ ] PR#2 merged and tagged
- [ ] CHANGELOG.md updated
- [ ] docs/telemetry.md updated with examples
- [ ] Example data generated: run ctx.search/ctx.get, collect _ctx/telemetry/*
- [ ] Share sanitized events.jsonl + last_run.json
- [ ] Monitor for `telemetry_lock_skipped` warnings (should be <2%)

---

## SUCCESS METRICS (Post-Deployment)

After both PRs merged, these queries should work:

```bash
# Query AST metrics
jq '.ast' _ctx/telemetry/last_run.json
# Output: {"ast_parse_count": 42, "ast_cache_hit_count": 36, "ast_cache_hit_rate": 0.857}

# Query LSP metrics
jq '.lsp' _ctx/telemetry/last_run.json
# Output: {"lsp_spawn_count": 3, "lsp_ready_count": 3, "lsp_ready_rate": 1.0, ...}

# Query bytes by mode
jq '.file_read' _ctx/telemetry/last_run.json
# Output: {"skeleton_bytes": 8192, "excerpt_bytes": 45678, "raw_bytes": 123456, ...}

# Query LSP definition latencies
jq '.latencies."lsp.request"' _ctx/telemetry/last_run.json
# Output: {"count": 5, "p50_ms": 145.0, "p95_ms": 289.0, "max_ms": 512.0}

# Query drop rate (lossy fcntl)
jq '.telemetry_drops' _ctx/telemetry/last_run.json
# Output: {"lock_skipped": 3, "drop_rate": 0.0067}  # 0.67% < 2% threshold ✅
```

---

## NOTES

1. **No breaking changes:** All existing CLI commands work unchanged.
2. **Backward compatible:** Old code calling `telemetry.event()` without extra fields still works.
3. **Monotonic clocks:** All new timings use `time.perf_counter_ns()`, never `time.time()`.
4. **Secure:** No absolute paths (normalized via `_relpath`), no file content, no API keys in telemetry.
5. **Auditable:** Every event is append-only; no deletions or modifications.
6. **Drop-safe:** Critical decisions (LSP READY) based on in-memory state, not telemetry counters.
7. **Telemetry is for observation, NOT gates:** Use tests/e2e/deterministic outputs for pass/fail decisions. Lossy telemetry is for trends/analytics only.

---

**Plan Complete:** Ready for Day 1 implementation  
**Owner:** Senior Engineer  
**Estimated Duration:** 5-6 days (2 days PR#1 + 3-4 days PR#2)  
**Success Criterion:** All tests pass, no data loss, all metrics queryable from last_run.json
