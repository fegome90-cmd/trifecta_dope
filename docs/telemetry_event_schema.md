# Telemetry Event Schema (AST+LSP)

**Version:** 1.0 (PR#1 - Infrastructure)  
**Status:** Specification (implementation in PR#2)

---

## Core Event Structure

All events follow this base schema:

```json
{
  "ts": "2026-01-01T12:00:00.000Z",
  "run_id": "run_1735689600",
  "segment_id": "a3b4c5d6",
  "cmd": "event.type",
  "args": {},
  "result": {},
  "timing_ms": 0,
  "tokens": {},
  "warnings": [],
  "x": {}
}
```

### Reserved Keys

The following keys are **reserved** and cannot be overridden by `extra_fields`:

- `ts`: Timestamp (ISO 8601 UTC)
- `run_id`: Unique run identifier
- `segment_id`: SHA-256 hash (8 chars) of segment path (privacy)
- `cmd`: Command/event type
- `args`: Command arguments (sanitized)
- `result`: Command result metadata
- `timing_ms`: Elapsed time in milliseconds
- `tokens`: Token usage estimation
- `warnings`: Warning messages
- `x`: Namespace for extra fields

### Extra Fields Namespace

All additional fields MUST be placed under the `x` namespace to prevent future collisions:

```json
{
  "cmd": "lsp.spawn",
  "x": {
    "lsp_state": "WARMING",
    "spawn_method": "subprocess"
  }
}
```

---

## Event Types (PR#2 Implementation)

### 1. AST Events

| Event Type | Fields | Example |
|------------|--------|---------|
| `ast.parse` | `file` (relative), `status`, `functions_count`, `classes_count` | `{"cmd": "ast.parse", "args": {"file": "src/domain/models.py"}, "result": {"status": "ok", "functions": 3, "classes": 2}, "timing_ms": 45, "x": {"skeleton_bytes": 512, "reduction_ratio": 0.08, "cache_hit": false}}` |

### 2. LSP Events

**State Machine:**
- **COLD**: No LSP process spawned
- **WARMING**: Process spawned, initializing (parallel with AST build)
- **READY**: Initialized + `didOpen` + `publishDiagnostics` received
- **FAILED**: Spawn/init error or crash

| Event Type | Fields | Example |
|------------|--------|---------|
| `lsp.spawn` | `pyright_binary`, `subprocess_pid`, `status` | `{"cmd": "lsp.spawn", "args": {"pyright_binary": "pyright-langserver"}, "result": {"subprocess_pid": 12345, "status": "ok"}, "timing_ms": 0, "x": {"lsp_state": "WARMING"}}` |
| `lsp.state_change` | `from_state`, `to_state`, `reason` | `{"cmd": "lsp.state_change", "args": {}, "result": {"from_state": "WARMING", "to_state": "READY", "reason": "publishDiagnostics received"}, "timing_ms": 1500, "x": {}}` |
| `lsp.request` | `method`, `file` (relative), `line`, `col`, `resolved` | `{"cmd": "lsp.request", "args": {"method": "definition", "file": "src/app.py", "line": 42, "col": 10}, "result": {"resolved": true, "target_file": "src/lib.py", "target_line": 15}, "timing_ms": 120, "x": {}}` |
| `lsp.fallback` | `reason`, `fallback_to` | `{"cmd": "lsp.fallback", "args": {"reason": "lsp_not_ready"}, "result": {"fallback_to": "ast_only"}, "timing_ms": 0, "x": {}}` |

### 3. File Read Events

| Event Type | Fields | Example |
|------------|--------|---------|
| `file.read` | `file` (relative), `mode`, `bytes`, `status` | `{"cmd": "file.read", "args": {"file": "src/app.py", "mode": "excerpt"}, "result": {"bytes": 2048, "status": "ok"}, "timing_ms": 5, "x": {"disclosure_mode": "excerpt"}}` |

### 4. Selector Events

| Event Type | Fields | Example |
|------------|--------|---------|
| `selector.resolve` | `symbol_query`, `resolved`, `matches`, `ambiguous` | `{"cmd": "selector.resolve", "args": {"symbol_query": "sym://python/src.domain.models/Config"}, "result": {"resolved": true, "matches": 1, "ambiguous": false}, "timing_ms": 30, "x": {}}` |

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

### Telemetry Counters (PR#1)
- `telemetry_events_attempted`: Total events attempted
- `telemetry_events_written`: Successfully written events
- `telemetry_lock_skipped`: Events dropped due to lock contention

---

## Summaries (in last_run.json)

```json
{
  "run_id": "run_1735689600",
  "ts": "2026-01-01T12:00:00.000Z",
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
  },
  "telemetry_drops": {
    "lock_skipped": 3,
    "attempted": 100,
    "written": 97,
    "drop_rate": 0.03
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
6. **External Files:** Files outside workspace are logged as `external/<hash8>-<name>` for privacy + uniqueness.

---

## LSP READY Definition (PR#2)

**READY state** is achieved when:
1. LSP process spawned successfully
2. `initialize` request sent and `InitializeResult` received
3. `didOpen` sent for first Python file found by AST scan
4. `textDocument/publishDiagnostics` notification received for that specific URI

**Policy:**
- LSP spawns in parallel during AST build (warm-up phase)
- Warm-up sends `didOpen` for first Python file found by AST scan
- READY achieved when `publishDiagnostics` received for that specific URI
- Requests ONLY sent when state == READY
- If not READY when needed → fallback to AST-only (no blocking wait)
- No aggressive timeouts: LSP gets full init time (5-10s typical)
- READY is LSP-instance-specific, not global (multiple LSP clients track own state)
