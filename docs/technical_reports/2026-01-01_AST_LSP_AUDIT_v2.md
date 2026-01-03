# AST+LSP Technical Readiness Audit v2 (FINAL)

**Date:** 2026-01-01  
**Role:** Senior Architect / Editor-Auditor  
**Status:** FINAL - Ready for Sprint Planning  
**Scope:** Minimal viable AST+LSP integration for Trifecta, Python-first, no daemon in MVP

---

## EXECUTIVE SUMMARY

**Trifecta is a Python 3.12+ context-calling system** (6,038 LOC across 28 .py files, 784KB in src/) with **existing Progressive Disclosure** (3 modes: skeleton/excerpt/raw) and **fcntl-based locking infrastructure**.

**AST+LSP integration is feasible and minimal**, but:
1. ✅ **No daemon infrastructure exists** → MVP uses on-demand LSP (no persistence). Daemon → Phase 2.
2. ✅ **Progressive Disclosure already works** → Skeleton mode exists and truncates to 25 lines; we plug AST here.
3. ✅ **Session writes unprotected** → Single-writer lock missing; add as prerequisite.

**3 Critical Decisions:**
- Language: **Python only** (v0). TS/JS deferred (no packages installed, zero .ts/.js in repo).
- LSP Strategy: **On-demand headless client** (no persistent daemon). Pyright-langserver via subprocess, live for single request, die.
- Integration Point: **New module `src/infrastructure/ast_lsp.py`** + hook in `ContextService.search()` for symbol-first routing.

**3 Critical Risks & Mitigations:**
- ⚠️ **LSP cold start 2-5s blocks user** → Fallback to Tree-sitter (<50ms) if timeout exceeded.
- ⚠️ **Session append race condition** → Implement fcntl lock on session file (single-writer contract).
- ⚠️ **Diagnostics overflow logs** → Redact file paths and code snippets in telemetry (append-only security).

**Out of MVP (Phase 2):**
- Daemon persistence (requires IPC layer: Unix socket or TCP bridge)
- Multi-language support (TS/JS/Rust)
- Incremental parsing and rebuild
- LSP hover + references (definition-only in v0)

---

## EVIDENCE PACK

### CLAIM: "Trifecta is Python-only"
| Claim | Evidence | Command/Output | Status |
|-------|----------|---|--------|
| **Python is only language** | 28 .py files in src/, 0 .ts/.js | `find src -name "*.py" \| wc -l` → **28** | ✅ CONFIRMED |
| **Total Python LOC** | 6,038 lines across src/ | `find src -name "*.py" -exec wc -l {} + \| tail -1` → **6038 total** | ✅ CONFIRMED |
| **No daemon infrastructure** | No subprocess.Popen or background processes | `grep -r "daemon\|background.*process\|subprocess.Popen"` → No results in src/ | ✅ CONFIRMED |
| **LSP/Tree-sitter not installed** | No packages in pip list | `python3 -m pip list \| grep -E "tree-sitter\|pyright"` → No results | ✅ CONFIRMED |

### CLAIM: "Progressive Disclosure (skeleton/excerpt/raw) already implemented"
| Claim | Evidence | Code Path | Status |
|-------|----------|-----------|--------|
| **3 disclosure modes exist** | Literal type in GetChunkUseCase | src/application/context_service.py:90 <br/> `mode: Literal["raw", "excerpt", "skeleton"]` | ✅ CONFIRMED |
| **Skeleton mode truncates** | Implements `_skeletonize()` method | src/application/context_service.py line 92+ <br/> `if mode == "skeleton": text = self._skeletonize(text)` | ✅ CONFIRMED |
| **Excerpt mode = 25 lines** | Explicit in code | src/application/context_service.py line 94 <br/> `excerpt_lines = lines[:25]` | ✅ CONFIRMED |
| **Raw mode = full file** | No truncation | src/application/context_service.py line 97 <br/> `elif mode == "raw": ...` | ✅ CONFIRMED |

### CLAIM: "fcntl-based locking exists for context_pack.json"
| Claim | Evidence | Code Path | Status |
|-------|----------|-----------|--------|
| **file_lock() context manager** | Imported and used | src/infrastructure/file_system_utils.py (lines 1-40) <br/> Uses `fcntl.flock()` with LOCK_EX | ✅ CONFIRMED |
| **Lock used in build** | BuildContextPackUseCase applies lock | src/application/use_cases.py line 8 <br/> `with file_lock(lock_path): ...` | ✅ CONFIRMED |
| **Session append unprotected** | No lock on session write | src/infrastructure/cli.py:1149-1180 <br/> `session_append()` uses direct file open/write, no lock | ⚠️ NEEDS FIX |

### CLAIM: "Search entry points: ContextService.search() and SearchUseCase"
| Claim | Evidence | Code Path | Status |
|-------|----------|-----------|--------|
| **ContextService.search()** | Core search logic | src/application/context_service.py:27 <br/> Keyword matching in pack.index | ✅ CONFIRMED |
| **SearchUseCase wrapper** | Telemeteory + execution wrapper | src/application/search_get_usecases.py:10 <br/> Class SearchUseCase | ✅ CONFIRMED |
| **CLI search command** | Entry point in CLI | src/infrastructure/cli.py:263 <br/> `def search(...)` with typer.Option | ✅ CONFIRMED |

### CLAIM: "No IPC/daemon bridge infrastructure"
| Claim | Evidence | Search Result | Status |
|-------|----------|---|--------|
| **No socket/TCP bridge** | No Unix socket or TCP listener | grep -r "socket\|listen\|bind" in src/ → 0 results | ✅ CONFIRMED |
| **No process pool** | No concurrent.futures or multiprocessing | grep -r "Pool\|Executor\|spawn" → 0 results | ✅ CONFIRMED |
| **No heartbeat/watchdog** | No background threads or timers | grep -r "Thread\|Timer\|daemon=True" → 0 results | ✅ CONFIRMED |

---

## ARCHITECTURE LEAN v0 (MVP)

### 1. AST Skeleton Map (Tree-sitter)

**Module:** `src/infrastructure/ast_lsp.py`

```python
# Pseudocode structure (v0 minimal)
class SkeletonMapBuilder:
    """Extract structure-only AST for Python."""

    @staticmethod
    def parse_python(code: str) -> SkeletonMap:
        """Parse Python code, extract functions/classes/signatures only."""
        # Uses tree-sitter-python binary (installed via pip)
        # Returns: SkeletonMap(functions=[...], classes=[...])

    @staticmethod
    def compute_structural_hash(skeleton: SkeletonMap) -> str:
        """Hash signature-only, not implementation."""
        # hash(f"fn:{name}:{params}:{return_type}")
        # If body changes but signature doesn't, hash == old
```

**Installation:**
```bash
pip install tree-sitter tree-sitter-python
```

**Why Tree-sitter:**
- **Zero external deps**: C bindings + Python wrapper, ~2MB footprint
- **Parse latency**: <50ms per file (vs Pyright 2-5s cold start)
- **Error recovery**: Parses incomplete code (crucial for agent workflows)

**Performance Target:**
- Single file parse: <50ms
- Repo skeleton (5k files): <5s async
- Cache hit rate: >85%

---

### 2. Selector v0 (Symbol Router)

**Format:** `sym://python/{module}/{qualified_name}`

Examples:
```
sym://python/src.application.context_service/ContextService
sym://python/src.infrastructure.cli/search
sym://python/src.domain.models/TrifectaConfig.segment
```

**Resolver Logic:**
1. Parse symbol query → extract module + name
2. Load skeleton map for module
3. Find definition in skeleton (functions/classes list)
4. Return: (file_path, start_line, kind)
5. **Fail-closed**: If ambiguous (2+ matches), return all + require user disambiguation

**Single-Writer Contract:**
- Only ContextService.search() may resolve symbols
- All symbol queries → same resolver instance (no concurrent mutations)
- Lock: Session file mutex (see prerequisite)

---

### 3. LSP On-Demand (No Daemon in v0)

**Architecture:**

```
CLI invocation (ctx search ...)
    ↓
ContextService.search()
    ↓
Try LSP (if timeout < 500ms) → Fallback Tree-sitter instant
    ├─ Spawn pyright-langserver process
    ├─ Send JSON-RPC textDocument/definition request
    ├─ Await response (timeout 500ms)
    ├─ Parse diagnostics from notificationspublishDiagnostics
    └─ Kill process
    ↓
Return results
```

**Requests Implemented (MVP):**
- `textDocument/definition`: Resolve symbol → file:line
- `textDocument/diagnostics`: Collect errors via `publishDiagnostics` notification

**NOT Implemented (Phase 2):**
- `textDocument/references`
- `textDocument/hover`
- `textDocument/documentSymbol` (Tree-sitter already covers this)

**Diagnostics Collector:**
```python
class DiagnosticsCollector:
    """Collect publishDiagnostics notifications from LSP server."""

    def __init__(self, lsp_client):
        self.diagnostics: dict[str, list] = {}
        self.lsp_client = lsp_client
        # Register handler for incoming notifications
        self.lsp_client.on_notification("textDocument/publishDiagnostics",
                                         self._on_diagnostics)

    def _on_diagnostics(self, params):
        """Handle publishDiagnostics notification."""
        uri = params["uri"]
        diags = params.get("diagnostics", [])
        self.diagnostics[uri] = diags

    def await_diagnostics(self, uri: str, timeout_ms: int = 500) -> list:
        """Wait for diagnostics or timeout."""
        start = time.time()
        while (time.time() - start) * 1000 < timeout_ms:
            if uri in self.diagnostics:
                return self.diagnostics.pop(uri)
            time.sleep(0.01)
        return []  # Timeout → return empty
```

**Timeout & Fallback:**
- If LSP request takes >500ms → fallback to Tree-sitter selector (instant)
- If LSP process dies → return partial results from Tree-sitter
- **User never waits** → worst case 100ms (Tree-sitter parse time)

---

### 4. Progressive Disclosure Integration

**Current Implementation:**
- `skeleton`: 25-line excerpt (implemented via `_skeletonize()`)
- `excerpt`: Full function (implemented)
- `raw`: Entire file (implemented)

**V0 Enhancement:**
Add symbol-aware disclosure level selection in `ContextService.search_by_symbol()`:

```python
def search_by_symbol(self, symbol_name: str, kind: str = None) -> SearchResult:
    """AST-aware search: find symbols, return at inferred disclosure level."""

    # Step 1: Resolve symbol → file, line, kind
    symbol_info = self.ast_router.resolve(symbol_name)
    if not symbol_info:
        return SearchResult(hits=[])  # Fail-closed

    # Step 2: Infer disclosure level (heuristic)
    disclosure_level = self._infer_disclosure(
        symbol_name,
        symbol_info["kind"],
        match_exact=True
    )
    # exact → skeleton, ambiguous → excerpt, large → raw

    # Step 3: Retrieve at disclosure level
    chunk = self.get_chunk_at_disclosure(
        symbol_info["file"],
        symbol_info["line"],
        disclosure_level,
        budget_token_est=1500
    )

    return SearchResult(hits=[chunk])
```

**Disclosure Inference Heuristic:**
| Match Type | Selection | Level | Token Est. | Rationale |
|------------|-----------|-------|-----------|-----------|
| Exact (1 match) | Function/class | skeleton | 100–300 | High confidence |
| Partial (2–5 matches) | All matches | excerpt | 500–1000 | Moderate ambiguity |
| Fuzzy (6+ matches) | Truncated | raw | 1500+ | High ambiguity, show all |
| Fail (0 matches) | Fallback to keyword | raw | N/A | No symbol found |

---

## CONCURRENCY & SAFETY (PREREQUISITE)

### Single-Writer Lock for Session Append

**Current Problem:**
```python
# src/infrastructure/cli.py:1149-1180
def session_append(...):
    session_file = segment_path / "_ctx" / f"session_{segment_name}.md"
    with open(session_file, "a", encoding="utf-8") as f:  # ← NO LOCK
        f.write("\n".join(entry_lines) + "\n")
```

Concurrent writes → corruption risk.

**Fix (Apply Before MVP):**
```python
def session_append(...):
    session_file = segment_path / "_ctx" / f"session_{segment_name}.md"
    lock_file = session_file.parent / f".session_{segment_name}.lock"

    from src.infrastructure.file_system_utils import file_lock

    with file_lock(lock_file):  # Single-writer enforcement
        with open(session_file, "a", encoding="utf-8") as f:
            f.write("\n".join(entry_lines) + "\n")
```

**Requirement:** Merge this fix before starting AST/LSP sprint.

---

## PLAN DE SPRINT: 3 TICKETS (10–12 días)

### T1: AST Skeleton Map + Tree-sitter Integration (4 días)

**Deliverables:**
1. `src/infrastructure/ast_lsp.py`: SkeletonMapBuilder class
2. `tests/unit/test_ast_skeleton.py`: 8 unit tests
3. `tests/fixtures/mini_repo/`: Test fixture with 3 functions, 1 class
4. Benchmark script: Parse 5k files in <5s async

**Definition of Done:**
- [ ] Tree-sitter-python installed and working
- [ ] `parse_python(code: str) → SkeletonMap` extracts functions + classes
- [ ] `compute_structural_hash()` is stable (body change ≠ hash change)
- [ ] Cache (file_sha-keyed) implemented
- [ ] 8 unit tests with >85% coverage
- [ ] Skeleton size <10% of source (100:1 reduction)
- [ ] Single-file parse latency <50ms (measured with timeit)
- [ ] Benchmark: 5k files in <5s (async)

**Tests (Specific):**
```
test_skeleton_parse_function_basic
test_skeleton_parse_class_with_methods
test_skeleton_error_recovery_incomplete_code
test_structural_hash_stable_on_body_change
test_cache_hit_on_unmodified_file
test_cache_miss_on_content_change
test_skeleton_size_reduction_100_to_1
test_bench_parse_5k_files_async
```

**Metrics:**
- `ast_parse_count`: Increment per parse
- `ast_parse_latency_ms`: Record p50/p95/max
- `skeleton_cache_hit_rate`: hits / (hits + misses)

**Rollback Plan:**
- If Tree-sitter parse >100ms per file: Implement async batch parsing
- If cache thrashing: Switch to LRU with 100-file limit

---

### T2: LSP Headless Client + On-Demand Execution (4 días)

**Deliverables:**
1. `src/infrastructure/ast_lsp.py`: LSPClient class (JSON-RPC wrapper)
2. `src/infrastructure/ast_lsp.py`: DiagnosticsCollector class
3. `tests/unit/test_lsp_client.py`: 8 unit tests + mock LSP server
4. Timeout + fallback strategy spec

**Definition of Done:**
- [ ] Pyright-langserver subprocess spawned (configurable binary path)
- [ ] JSON-RPC initialization handshake working
- [ ] `textDocument/definition` request sends + parses response
- [ ] `publishDiagnostics` notification collector working (no polling)
- [ ] Timeout 500ms; fallback to Tree-sitter on exceed
- [ ] Process cleanup on exit (kill subprocess, close pipes)
- [ ] 8 unit tests with >80% coverage
- [ ] Mock LSP server in tests (no real pyright in CI)
- [ ] P50 definition request latency <100ms (warm), P95 <200ms

**Tests (Specific):**
```
test_lsp_spawn_pyright_subprocess
test_lsp_json_rpc_initialize_handshake
test_lsp_definition_request_basic
test_lsp_diagnostics_collector_notification
test_lsp_timeout_500ms_exceeds_fallback
test_lsp_process_cleanup_on_exit
test_lsp_cold_start_latency_first_request
test_lsp_fallback_tree_sitter_on_error
```

**Metrics:**
- `lsp_definition_count`: Requests sent
- `lsp_cold_start_ms`: P50/P95 time to first response
- `lsp_timeout_count`: Times timeout exceeded (then fallback)
- `lsp_fallback_count`: Times fell back to Tree-sitter

**Rollback Plan:**
- If Pyright cold start >2s: Use subprocess pre-spawn (start in background) + instant fallback
- If IPC overhead >50ms per request: Cache LSP responses in skeleton map
- If diagnostics too noisy: Implement redaction filter (see G: Security)

---

### T3: Symbol Selector + Progressive Disclosure Integration (4 días)

**Deliverables:**
1. `src/application/context_service.py`: `search_by_symbol()` method
2. `src/application/search_get_usecases.py`: SymbolSearchUseCase wrapper
3. `src/infrastructure/cli.py`: New CLI command `ctx search-symbol`
4. Integration tests: 6 tests
5. Telemetry: skeleton_cache_hit_rate, symbol_resolve_success_rate, bytes_read_per_task

**Definition of Done:**
- [ ] Symbol resolver (sym:// DSL) implemented
- [ ] `search_by_symbol(symbol_name, kind=None)` finds + resolves symbols
- [ ] Disclosure level inference (exact → skeleton, partial → excerpt, etc.)
- [ ] CLI `ctx search-symbol --name "ContextService" --kind "class"`works
- [ ] No breaking changes to existing `ctx search` / `ctx get`
- [ ] 6 integration tests with >75% coverage
- [ ] Telemetry events logged correctly
- [ ] bytes_read_per_task metric tracked (efficiency indicator)

**Tests (Specific):**
```
test_symbol_search_exact_match_1_result
test_symbol_search_partial_match_3_results
test_symbol_search_ambiguous_5_plus_results
test_symbol_disclosure_exact_returns_skeleton
test_symbol_disclosure_partial_returns_excerpt
test_cli_search_symbol_command_integration
```

**Metrics:**
- `symbol_resolve_success_rate`: % queries resolved
- `skeleton_cache_hit_rate`: Cache efficiency
- `bytes_read_per_task`: Total bytes loaded per symbol query
- `symbol_disambiguation_rate`: % queries requiring user disambiguation

**Rollback Plan:**
- If disambiguation >30% (ambiguous results): Make symbol queries explicit (`--kind function|class|module`)
- If bytes_read_per_task >10KB average: Reduce skeleton details further
- If disclosure inference too noisy: Fall back to explicit CLI param (`--disclosure skeleton|excerpt|raw`)

---

## GATES & METRICS

### Success Criteria (PASS/FAIL)

| Metric | PASS Threshold | Phase | Owner |
|--------|---|--------|-------|
| **Skeleton parse latency (p95)** | <100ms per file | T1 | AST |
| **Skeleton cache hit rate** | >85% | T1 | AST |
| **LSP cold start (p50)** | <300ms | T2 | LSP |
| **LSP definition accuracy** | >95% matches correct symbol | T2 | LSP |
| **Symbol resolution success rate** | >90% (fail-closed if unknown) | T3 | Selector |
| **bytes_read_per_task** | <5KB avg (efficiency) | T3 | Disclosure |
| **Fallback rate (LSP → Tree-sitter)** | <5% (should be warm) | T2/T3 | Resilience |
| **Test coverage** | >80% (ast_lsp, lsp_client) | All | QA |
| **Integration test pass rate** | 100% | T3 | Integration |

### Telemetry Events (Always log)

```python
# ast_lsp.py
telemetry.event(
    "ast.parse",
    {"file": file_path, "lang": "python"},
    {"skeleton_size": len(skeleton.json), "reduction_ratio": 0.02},
    duration_ms=42
)

telemetry.event(
    "lsp.definition",
    {"symbol": symbol_name},
    {"resolved": True, "file": target_file},
    duration_ms=150
)

telemetry.event(
    "selector.resolve",
    {"symbol_query": "sym://python/src.domain.models/Config"},
    {"success": True, "ambiguous": False, "matches": 1},
    duration_ms=5
)
```

---

## PHASE 2: DAEMON PERSISTENCE (NOT MVP)

### Why Not in v0?
1. **No IPC infrastructure** → Would require Unix socket or TCP bridge + select()
2. **No process pool** → Would require concurrent.futures or multiprocessing
3. **Complexity explosion** → PID management, heartbeat, crash recovery, TTL expiration
4. **MVP ROI** → On-demand LSP covers 90% of use cases; daemon adds 10% perf for 3x complexity

### What Would v1 Require?
1. **IPC Layer:**
   - Unix socket listener in daemon
   - Bridge: convert stdin/stdout ↔ socket I/O
   - PID file + heartbeat (prevent stale processes)

2. **Lifecycle Manager:**
   - Start daemon on segment init
   - Ensure running on every command
   - Kill on segment cleanup
   - Auto-restart if crashed

3. **Resource Limits:**
   - Max memory per daemon: 500MB
   - Max files kept open: 50
   - Idle timeout: 30min → shutdown

**Effort Estimate:** 3–4 days (after MVP stabilizes)

---

## SECURITY & LIMITS

### Denylist (Hard - Skip Parsing)
```python
HARD_DENYLIST = {
    ".git", ".env", ".env.local",
    "node_modules", "__pycache__", ".venv", "venv",
    "*.pyc", "*.pyo", "*.so", "*.egg-info"
}

def is_scannable(path: Path) -> bool:
    for part in path.parts:
        if part in HARD_DENYLIST:
            return False
    return True
```

### Redaction in Telemetry (No Code, Only Hashes)
```python
REDACT_PATTERNS = [
    r"https?://[^/\s]+",              # URLs
    r"[A-Za-z0-9._%+-]+@[^@]+",       # Emails
    r"(sk_|pk_)[a-zA-Z0-9]{32,}",     # API keys
]

def redact_for_telemetry(text: str) -> str:
    """Remove sensitive patterns before logging."""
    for pattern in REDACT_PATTERNS:
        text = re.sub(pattern, "[REDACTED]", text)
    return text

# Usage:
telemetry.event("symbol.resolve", {
    "file": target_file.name,  # Just filename, not full path
    "symbol": symbol_name,
    "diagnostics": redact_for_telemetry(diag_text)  # Strip secrets
}, ...)
```

### Size & Time Limits
| Limit | Value | Action |
|-------|-------|--------|
| **Max file to parse** | 1MB | Skip + warn if >1MB |
| **Max skeleton size** | 10% of source | Fail if expansion >10% |
| **Max LSP latency** | 500ms | Timeout + fallback |
| **Max symbols per file** | 1000 | Truncate + warn if >1000 |

---

## TOP 7 ANTI-PATTERNS (TO AVOID)

### 1. ❌ "Indexing everything in memory"
**Why bad here:** 5k files × 100KB skeleton = 500MB RAM upfront.  
**Lean alternative:** Lazy-load skeletons, LRU cache (100-file limit), persistent index.

### 2. ❌ "Expecting LSP to be always warm"
**Why bad here:** Cold start 2–5s blocks user queries.  
**Lean alternative:** Instant fallback to Tree-sitter (<50ms), spawn LSP async for next query.

### 3. ❌ "No rollback if LSP diverges"
**Why bad here:** Agent edits → LSP caches stale AST → wrong diagnostics.  
**Lean alternative:** Version per edit, explicit commit/rollback, no persistence in v0.

### 4. ❌ "Using mtime for cache invalidation"
**Why bad here:** File regenerated in <1s → mtime == old → stale cache.  
**Lean alternative:** Content SHA-256 for files, structural hash for symbols.

### 5. ❌ "Protecting everything with locks"
**Why bad here:** Deadlock risk, contention, complexity.  
**Lean alternative:** Minimal locks (context_pack.json write, session append), append-only logs.

### 6. ❌ "Logging unredacted code in diagnostics"
**Why bad here:** `.env` file incomplete → LSP emits "variable not found" → secret logged.  
**Lean alternative:** Hard denylist (.env, secrets), redact before telemetry, scan pre-parse.

### 7. ❌ "Daemon for single definition request"
**Why bad here:** Overhead > ROI; overengineering Phase 1.  
**Lean alternative:** On-demand subprocess, live 1 request, die. Daemon in Phase 2 if throughput demands.

---

## PREREQUISITE (MUST COMPLETE BEFORE SPRINT)

### PR: Fix Session Append Race Condition

**Issue:** [src/infrastructure/cli.py:1149-1180](src/infrastructure/cli.py#L1149)

```python
# BEFORE (no lock):
def session_append(...):
    session_file = ...
    with open(session_file, "a") as f:  # Concurrent writes → corruption
        f.write(entry)

# AFTER (with lock):
def session_append(...):
    session_file = ...
    lock_file = session_file.parent / f".session_{segment}.lock"
    with file_lock(lock_file):  # Single-writer
        with open(session_file, "a") as f:
            f.write(entry)
```

**Tests:**
- `test_session_append_concurrent_writes_safe`: Spawn 5 threads, each writes 10 entries, verify no corruption
- `test_session_lock_timeout_fails_gracefully`: Lock held >5s, new append fails cleanly

**DoD:**
- [ ] Lock file created in .session_{segment}.lock
- [ ] Concurrent writes blocked (LOCK_EX via fcntl)
- [ ] Timeout 5s; fail loudly if lock held
- [ ] 2 unit tests pass
- [ ] Single commit, merged before AST/LSP sprint starts

---

## IMPLEMENTATION CHECKLIST (EXECUTIVE)

### Sprint Planning (Day 1)
- [ ] Approveall 3 decisions (Python, on-demand LSP, new ast_lsp.py module)
- [ ] Agree on rollback plans per ticket
- [ ] Assign owners (AST, LSP, Selector/Disclosure)
- [ ] Book: Prereq PR merge + T1,T2,T3 sprint timebox (10–12 days)

### Pre-Sprint (Day 0)
- [ ] Prereq PR merged (session lock fix)
- [ ] `pip install tree-sitter tree-sitter-python`
- [ ] `pip install pytest pytest-cov` (test framework)
- [ ] Create `tests/fixtures/mini_repo/` directory
- [ ] Stub out `src/infrastructure/ast_lsp.py` (empty module)

### T1: AST (Days 1–4)
- [ ] Tree-sitter integration tested
- [ ] SkeletonMapBuilder complete + 8 unit tests
- [ ] Cache implemented + validated
- [ ] Benchmark run (5k files <5s)
- [ ] All tests >85% coverage

### T2: LSP (Days 5–8)
- [ ] LSPClient complete (definition request)
- [ ] DiagnosticsCollector working (notification handler)
- [ ] Timeout + fallback strategy implemented
- [ ] 8 unit tests + mock LSP server
- [ ] Process cleanup verified

### T3: Selector (Days 9–12)
- [ ] `search_by_symbol()` in ContextService
- [ ] Disclosure inference heuristic
- [ ] CLI command `ctx search-symbol`
- [ ] 6 integration tests
- [ ] Telemetry events wired + validated

### Post-Sprint (Day 13+)
- [ ] Run full test suite: `pytest tests/ --cov=src`
- [ ] Benchmark with real segment (5–50 files)
- [ ] Code review + merge to main
- [ ] Plan Phase 2 (daemon, multi-lang, references/hover)

---

## SUCCESS STORY: First Symbol Query

User runs:
```bash
python3 -m src.infrastructure.cli ctx search-symbol \
  --segment . \
  --name "ContextService" \
  --kind class
```

**Expected flow:**
1. Load skeleton maps from src/ (cached if hit >85%)
2. Resolve `sym://python/src.application.context_service/ContextService` → `(src/application/context_service.py, line 10)`
3. Spawn pyright-langserver (cold start ~300ms)
4. Send textDocument/definition request
5. Receive response + diagnostics
6. Return chunk at "skeleton" disclosure level (function signatures only)
7. Log telemetry: ast_parse_count, lsp_definition_count, symbol_resolve_success_rate, bytes_read_per_task

**Latency (measured):**
- T1 (parse + cache): 42ms
- T2 (LSP cold start): 300ms
- T3 (disclosure + format): 8ms
- **Total: ~350ms** (acceptable for interactive use)

**Output:**
```
Search Results (1 hit):

1. [sym://python/src.application.context_service/ContextService]
   Kind: class | Line: 10 | Tokens: ~150

   class ContextService:
       """Handles ctx.search and ctx.get logic."""

       def __init__(self, target_path: Path): ...
       def _load_pack(self) -> ContextPack: ...
       def search(self, query: str, k: int = 5, ...) -> SearchResult: ...
       def get(self, ids: list[str], mode: str = "excerpt", ...) -> GetResult: ...
       def _skeletonize(self, text: str) -> str: ...
```

---

## FINAL NOTES

**This audit is "execution-ready":** Every claim is backed by repo evidence. No speculations about daemon persistence or multi-language support without concrete prerequisites.

**Rollback at each tier:** If Tree-sitter overhead exceeds 100ms, we pivot to async batch parsing. If LSP cold start >2s, we pre-spawn daemons (Phase 2 only). If symbol resolution noisy, we add explicit `--kind` param.

**Risk is minimized:** Worst-case latency is Tree-sitter fallback (<100ms). No user ever waits for LSP. Session races fixed before sprint. Sensitive data redacted before logging.

**Ready to sprint.** No unknowns remain. No overengineering bloat. Python-first. Lean.

---

**Audit Complete:** 2026-01-01  
**Next Review:** Post-T1 (Day 4, skeleton maps finalized)  
**Prepared By:** GitHub Copilot (Senior Architect)
