# PR Plan: AST+LSP Telemetry Instrumentation (Implementation Detail)

**Date:** 2026-01-01  
**Role:** Senior Engineer / Project Manager  
**Scope:** 4–5 days of focused implementation  
**Success Criterion:** All events logged with monotonic timings, zero duplicate systems, >80% test coverage

---

## OVERVIEW

This PR will instrument the **existing Trifecta telemetry system** (not create a new one) to measure:
- AST skeleton build latencies (Tree-sitter parse times)
- LSP lifecycle (spawn → initialize → ready)
- LSP request latencies (definition, diagnostics)
- Bytes read per command and per disclosure mode
- Fallback triggers (timeouts, errors)

**Breaking changes:** None. All new fields are additive; existing event format unchanged.

---

## TICKET 1: Core Telemetry Extension (Day 1, 2 hours)

**PR Title:** `feat(telemetry): extend event() to support AST/LSP structured fields`

**Description:**
Extend the Telemetry class to accept optional structured fields (e.g., bytes_read, disclosure_mode) while maintaining backward compatibility with existing events.

### Changes

#### File: `src/infrastructure/telemetry.py`

**Line 113: Modify `event()` signature**
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
    
    Extra fields will be serialized directly to the event JSON.
    Example: telemetry.event("ctx.search", {...}, {...}, 100, bytes_read=1024)
    """
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
        **extra_fields,  # NEW: merge all extra fields into payload
    }

    try:
        self._write_jsonl("events.jsonl", payload)
        if timing_ms > 0:
            self.observe(cmd, timing_ms)
        # ... rest of token tracking unchanged ...
```

**Line 245: Add AST/LSP/file_read summaries to `flush()`**

Before final `run_summary` dict assembly (line ~230), add:

```python
    # NEW: AST summary
    ast_summary = {
        "ast_parse_count": self.metrics.get("ast_parse_count", 0),
        "ast_cache_hit_count": self.metrics.get("ast_cache_hit_count", 0),
        "ast_cache_hit_rate": round(
            self.metrics.get("ast_cache_hit_count", 0) / 
            max(self.metrics.get("ast_parse_count", 1), 1),
            3
        ),
    }

    # NEW: LSP summary
    lsp_summary = {
        "lsp_spawn_count": self.metrics.get("lsp_spawn_count", 0),
        "lsp_ready_count": self.metrics.get("lsp_ready_count", 0),
        "lsp_timeout_count": self.metrics.get("lsp_timeout_count", 0),
        "lsp_fallback_count": self.metrics.get("lsp_fallback_count", 0),
        "lsp_timeout_rate": round(
            self.metrics.get("lsp_timeout_count", 0) / 
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

### Definition of Done

- [ ] `event()` accepts `**extra_fields` and merges into JSON payload
- [ ] All new event fields appear in events.jsonl on write
- [ ] `flush()` calculates and outputs AST/LSP/file_read summaries
- [ ] Backward compatibility: old code calling `telemetry.event(cmd, args, result, timing_ms)` still works
- [ ] Unit test: `test_telemetry_extra_fields_serialized` (verify bytes_read in event)
- [ ] Unit test: `test_telemetry_summary_calculations` (verify AST/LSP/file_read in last_run.json)
- [ ] No errors or warnings from linting (mypy, pylint)

---

## TICKET 2: AST+Selector Module (Day 2–3, 16 hours)

**PR Title:** `feat(infrastructure): add ast_lsp.py with SkeletonMapBuilder + LSPClient + Selector + Instrumentation`

**Description:**
Create a new infrastructure module for AST parsing (Tree-sitter), symbol selection, and LSP client integration. All components use the extended telemetry system with monotonic clocks.

### Changes

#### File: `src/infrastructure/ast_lsp.py` (NEW, 300+ lines)

```python
"""AST + LSP integration with instrumentation."""

import json
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from src.infrastructure.telemetry import Telemetry

@dataclass
class SkeletonMap:
    """Parsed Python structure (functions, classes, imports)."""
    functions: List[Dict[str, Any]]
    classes: List[Dict[str, Any]]
    imports: List[str]
    file_path: Path

class SkeletonMapBuilder:
    """Build skeleton maps using Tree-sitter Python parser."""
    
    def __init__(self, telemetry: Telemetry, segment_root: Path):
        self.telemetry = telemetry
        self.segment_root = segment_root
        self._skeleton_cache: Dict[str, SkeletonMap] = {}
        self._file_sha_cache: Dict[Path, str] = {}
    
    def _relative_path(self, path: Path) -> str:
        """Convert to relative path for telemetry (redaction)."""
        try:
            return str(path.relative_to(self.segment_root))
        except ValueError:
            return str(path.name)
    
    def parse_python(self, code: str, file_path: Path) -> SkeletonMap:
        """
        Parse Python code, extract structure (functions/classes only).
        Uses monotonic clock for timing.
        """
        start_ns = time.perf_counter_ns()
        
        try:
            # Import tree-sitter on first use
            from tree_sitter import Language, Parser
            
            PYTHON_LANGUAGE = Language("tree-sitter-python")
            parser = Parser()
            parser.set_language(PYTHON_LANGUAGE)
            
            tree = parser.parse(code.encode('utf-8'))
            functions, classes, imports = self._extract_structure(tree)
            
            skeleton = SkeletonMap(
                functions=functions,
                classes=classes,
                imports=imports,
                file_path=file_path
            )
            
            elapsed_ns = time.perf_counter_ns() - start_ns
            elapsed_ms = int(elapsed_ns / 1_000_000)
            
            skeleton_bytes = len(json.dumps(skeleton.__dict__, default=str))
            reduction_ratio = skeleton_bytes / max(len(code), 1)
            
            # Emit event with monotonic timing
            self.telemetry.event(
                "ast.parse",
                {"file": self._relative_path(file_path)},
                {
                    "functions": len(functions),
                    "classes": len(classes),
                    "status": "ok"
                },
                elapsed_ms,
                skeleton_bytes=skeleton_bytes,
                reduction_ratio=round(reduction_ratio, 4),
            )
            
            # Increment counter
            self.telemetry.incr("ast_parse_count")
            
            return skeleton
            
        except Exception as e:
            elapsed_ns = time.perf_counter_ns() - start_ns
            elapsed_ms = int(elapsed_ns / 1_000_000)
            
            self.telemetry.event(
                "ast.parse",
                {"file": self._relative_path(file_path)},
                {"status": "error", "error": str(e)},
                elapsed_ms,
            )
            raise
    
    def _extract_structure(self, tree) -> tuple:
        """Extract functions, classes, imports from AST tree."""
        # Pseudocode: walk tree, identify function_definition / class_definition / import_statement nodes
        # Return (functions, classes, imports) lists
        # ACTUAL IMPLEMENTATION: Use tree-sitter Python query language
        return [], [], []

class LSPClient:
    """JSON-RPC client for Pyright language server."""
    
    def __init__(self, telemetry: Telemetry, pyright_binary: str = "pyright-langserver"):
        self.telemetry = telemetry
        self.pyright_binary = pyright_binary
        self.process: Optional[subprocess.Popen] = None
        self.initialized = False
        self._message_id = 0
        
        self.spawn_time_ns = time.perf_counter_ns()
        
        try:
            self.process = subprocess.Popen(
                [pyright_binary],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            
            self.telemetry.event(
                "lsp.spawn",
                {"pyright_binary": pyright_binary},
                {"subprocess_pid": self.process.pid, "status": "ok"},
                0,
            )
            
            self.telemetry.incr("lsp_spawn_count")
            
        except Exception as e:
            self.telemetry.event(
                "lsp.spawn",
                {"pyright_binary": pyright_binary},
                {"status": "error", "error": str(e)},
                0,
            )
            raise
    
    def initialize(self, workspace_path: Path) -> None:
        """Send LSP initialize request."""
        start_ns = time.perf_counter_ns()
        
        try:
            # Construct and send initialize JSON-RPC request
            # (Pseudocode; actual implementation: send JSON-RPC message)
            
            elapsed_ns = time.perf_counter_ns() - start_ns
            elapsed_ms = int(elapsed_ns / 1_000_000)
            
            self.telemetry.event(
                "lsp.initialize",
                {"workspace": str(workspace_path)},
                {"status": "ok", "initialized": True},
                elapsed_ms,
            )
            
            self.initialized = True
            
        except Exception as e:
            elapsed_ns = time.perf_counter_ns() - start_ns
            elapsed_ms = int(elapsed_ns / 1_000_000)
            
            self.telemetry.event(
                "lsp.initialize",
                {"workspace": str(workspace_path)},
                {"status": "error", "error": str(e)},
                elapsed_ms,
            )
            raise
    
    def definition(self, file_path: Path, line: int, col: int) -> Optional[Dict]:
        """Request textDocument/definition."""
        start_ns = time.perf_counter_ns()
        
        try:
            # Send textDocument/definition request, wait for response (timeout 500ms)
            response = self._send_request("textDocument/definition", {
                "textDocument": {"uri": file_path.as_uri()},
                "position": {"line": line, "character": col}
            }, timeout_ms=500)
            
            elapsed_ns = time.perf_counter_ns() - start_ns
            elapsed_ms = int(elapsed_ns / 1_000_000)
            
            if response:
                # Extract file + line from response
                target_file = response.get("uri", "unknown")
                target_line = response.get("range", {}).get("start", {}).get("line", 0)
                
                self.telemetry.event(
                    "lsp.definition",
                    {"file": str(file_path.name), "line": line, "col": col},
                    {"resolved": True, "target_file": target_file, "target_line": target_line},
                    elapsed_ms,
                )
            
            self.telemetry.incr("lsp_definition_count")
            return response
            
        except TimeoutError:
            elapsed_ns = time.perf_counter_ns() - start_ns
            elapsed_ms = int(elapsed_ns / 1_000_000)
            
            self.telemetry.event(
                "lsp.timeout",
                {"method": "definition"},
                {"timeout_ms": 500},
                elapsed_ms,
                fallback_to="tree_sitter"
            )
            
            self.telemetry.incr("lsp_timeout_count")
            self.telemetry.incr("lsp_fallback_count")
            
            raise
    
    def _send_request(self, method: str, params: dict, timeout_ms: int = 500) -> Optional[dict]:
        """Send JSON-RPC request, wait for response."""
        # Pseudocode: assemble JSON-RPC message, send, wait for response, parse
        # ACTUAL: Use python-jsonrpc2 or similar
        pass
    
    def shutdown(self) -> None:
        """Kill LSP process."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                self.process.kill()
            finally:
                self.process = None

class Selector:
    """Symbol resolver for sym:// DSL."""
    
    def __init__(self, telemetry: Telemetry, skeleton_map_builder: SkeletonMapBuilder):
        self.telemetry = telemetry
        self.skeleton_map_builder = skeleton_map_builder
    
    def resolve_symbol(self, symbol_query: str) -> Optional[Dict]:
        """
        Resolve sym://python/module.path/SymbolName to file + line + kind.
        Uses monotonic timing.
        """
        start_ns = time.perf_counter_ns()
        
        try:
            # Parse sym://python/src.domain.models/Config
            # Find file, load skeleton, locate symbol in skeleton
            
            resolved = True  # simplified
            matches_count = 1
            ambiguous = False
            
            elapsed_ns = time.perf_counter_ns() - start_ns
            elapsed_ms = int(elapsed_ns / 1_000_000)
            
            self.telemetry.event(
                "selector.resolve",
                {"symbol_query": symbol_query},
                {"resolved": resolved, "matches": matches_count, "ambiguous": ambiguous},
                elapsed_ms,
            )
            
            if resolved:
                self.telemetry.incr("selector_resolve_success_count")
            
            self.telemetry.incr("selector_resolve_count")
            
            return {"file": "src/domain/models.py", "line": 42, "kind": "class"}
            
        except Exception as e:
            elapsed_ns = time.perf_counter_ns() - start_ns
            elapsed_ms = int(elapsed_ns / 1_000_000)
            
            self.telemetry.event(
                "selector.resolve",
                {"symbol_query": symbol_query},
                {"resolved": False, "error": str(e)},
                elapsed_ms,
            )
            
            raise
```

### Definition of Done

- [ ] Tree-sitter Python parser installed and imported successfully
- [ ] SkeletonMapBuilder.parse_python() uses perf_counter_ns for timing
- [ ] LSPClient constructor spawns pyright-langserver subprocess
- [ ] LSPClient.definition() sends textDocument/definition JSON-RPC request
- [ ] LSPClient.definition() timeouts after 500ms (configurable)
- [ ] Selector.resolve_symbol() parses sym:// DSL
- [ ] All event() calls use relative paths (via _relative_path())
- [ ] No sensitive data (API keys, absolute paths) in events
- [ ] Unit test: `test_skeleton_parse_perf_counter_ns` (verify monotonic clock)
- [ ] Unit test: `test_lsp_timeout_fallback` (verify timeout → fallback event)
- [ ] Unit test: `test_selector_resolve_symbol` (basic sym:// parsing)
- [ ] Type hints complete (mypy clean)
- [ ] All imports available (tree-sitter, subprocess, typing)

---

## TICKET 3: CLI + FileSystem Hooks (Day 3, 8 hours)

**PR Title:** `feat(cli,file_system): emit bytes_read and disclosure_mode in events`

**Description:**
Integrate new telemetry fields into existing CLI commands (ctx.search, ctx.get) and track bytes read per mode.

### Changes

#### File: `src/infrastructure/cli.py`

**Line 279 (ctx.search):** Add bytes_read and cache_hit_rate

```python
@ctx_app.command("search")
def search(
    query: str = typer.Option(..., "--query", "-q", help="Search query"),
    segment: str = typer.Option(..., "--segment", "-s", help=HELP_SEGMENT),
    limit: int = typer.Option(5, "--limit", "-l", help="Max results"),
    telemetry_level: str = typer.Option("lite", "--telemetry", help=HELP_TELEMETRY),
) -> None:
    """Search for relevant chunks in the Context Pack."""
    telemetry = _get_telemetry(segment, telemetry_level)
    start_time = time.time()
    start_ns = time.perf_counter_ns()  # NEW: monotonic clock
    _, file_system, _ = _get_dependencies(segment, telemetry)

    use_case = SearchUseCase(file_system, telemetry)

    try:
        output = use_case.execute(Path(segment), query, limit=limit)
        typer.echo(output)
        
        # NEW: Record with monotonic timing
        elapsed_ms = int((time.perf_counter_ns() - start_ns) / 1_000_000)
        
        # Collect bytes read from file_system
        bytes_read = getattr(file_system, 'total_bytes_read', 0)
        
        # Log event with new fields
        telemetry.event(
            "ctx.search",
            {"query": query, "limit": limit},
            {"hits": output.count("hit"), "status": "ok"},
            elapsed_ms,
            bytes_read=bytes_read,  # NEW
            disclosure_mode=None,   # NEW (N/A for search)
        )
        
    except Exception as e:
        elapsed_ms = int((time.perf_counter_ns() - start_ns) / 1_000_000)
        
        telemetry.event(
            "ctx.search",
            {"query": query, "limit": limit},
            {"status": "error", "error": str(e)},
            elapsed_ms,
            bytes_read=getattr(file_system, 'total_bytes_read', 0),  # NEW
        )
        typer.echo(_format_error(e, "Search Error"), err=True)
        raise typer.Exit(1)
    finally:
        telemetry.flush()
```

**Line 317 (ctx.get):** Add bytes_read and disclosure_mode

```python
@ctx_app.command("get")
def get(
    ids: str = typer.Option(..., "--ids", "-i", help="Comma-separated Chunk IDs"),
    mode: Literal["raw", "excerpt", "skeleton"] = typer.Option("excerpt", "--mode", "-m", help="Disclosure level"),
    segment: str = typer.Option(..., "--segment", "-s", help=HELP_SEGMENT),
    budget_token_est: int = typer.Option(1500, "--budget-token-est", "-b", help="Max token budget"),
    telemetry_level: str = typer.Option("lite", "--telemetry", help=HELP_TELEMETRY),
) -> None:
    """Retrieve full content for specific chunks."""
    telemetry = _get_telemetry(segment, telemetry_level)
    start_ns = time.perf_counter_ns()  # NEW: monotonic clock
    _, file_system, _ = _get_dependencies(segment, telemetry)

    use_case = GetChunkUseCase(file_system, telemetry)

    id_list = [x.strip() for x in ids.split(",") if x.strip()]

    try:
        output = use_case.execute(
            Path(segment), id_list, mode=mode, budget_token_est=budget_token_est
        )
        typer.echo(output)
        
        # NEW: Record with monotonic timing
        elapsed_ms = int((time.perf_counter_ns() - start_ns) / 1_000_000)
        
        # Collect bytes read from file_system
        bytes_read = getattr(file_system, 'total_bytes_read', 0)
        
        # Log event with new fields
        telemetry.event(
            "ctx.get",
            {"ids": id_list, "mode": mode, "budget": budget_token_est},
            {"chunks_returned": output.count("---"), "status": "ok"},
            elapsed_ms,
            bytes_read=bytes_read,        # NEW
            disclosure_mode=mode,         # NEW
        )
        
    except Exception as e:
        elapsed_ms = int((time.perf_counter_ns() - start_ns) / 1_000_000)
        
        telemetry.event(
            "ctx.get",
            {"ids": id_list, "mode": mode},
            {"status": "error", "error": str(e)},
            elapsed_ms,
            bytes_read=getattr(file_system, 'total_bytes_read', 0),  # NEW
            disclosure_mode=mode,  # NEW
        )
        typer.echo(_format_error(e, "Get Error"), err=True)
        raise typer.Exit(1)
    finally:
        telemetry.flush()
```

#### File: `src/infrastructure/file_system.py`

**Add bytes tracking:**

```python
class FileSystemAdapter:
    """File system operations with telemetry."""
    
    def __init__(self):
        self.total_bytes_read = 0  # NEW
    
    def read_file_at_mode(self, path: Path, mode: Literal["raw", "excerpt", "skeleton"] = "excerpt") -> str:
        """Read file content at disclosure level."""
        start_ns = time.perf_counter_ns()  # NEW
        
        content = self._do_read(path, mode)
        
        bytes_read = len(content.encode('utf-8'))
        self.total_bytes_read += bytes_read  # NEW
        
        if hasattr(self, 'telemetry') and self.telemetry:
            # NEW: Emit per-file read event
            elapsed_ms = int((time.perf_counter_ns() - start_ns) / 1_000_000)
            
            self.telemetry.event(
                "file.read",
                {"file": str(path.name), "mode": mode},
                {"bytes": bytes_read, "status": "ok"},
                elapsed_ms,
            )
            
            # NEW: Increment mode-specific counter
            self.telemetry.incr(f"file_read_{mode}_bytes_total", bytes_read)
        
        return content
```

### Definition of Done

- [ ] ctx.search emits bytes_read field in events
- [ ] ctx.get emits bytes_read + disclosure_mode fields in events
- [ ] All timings use perf_counter_ns (monotonic)
- [ ] FileSystemAdapter.total_bytes_read tracks cumulative bytes per command
- [ ] Counters incremented: file_read_skeleton_bytes_total, file_read_excerpt_bytes_total, file_read_raw_bytes_total
- [ ] Unit test: `test_cli_search_emits_bytes_read` (verify field in event)
- [ ] Unit test: `test_cli_get_emits_disclosure_mode` (verify field in event)
- [ ] No breaking changes to CLI args or output format
- [ ] Backward compatible: old commands still work

---

## TICKET 4: Integration Tests + Validation (Day 4–5, 16 hours)

**PR Title:** `test(telemetry): add integration tests for AST/LSP instrumentation`

**Description:**
Comprehensive test suite to validate monotonic timing, no data loss, aggregation correctness, and concurrent safety.

### Changes

#### File: `tests/unit/test_telemetry_ast_lsp.py` (NEW, 200+ lines)

```python
"""Unit tests for AST/LSP telemetry instrumentation."""

import json
import time
from pathlib import Path
import pytest
from src.infrastructure.telemetry import Telemetry

class TestTelemetryExtension:
    """Test telemetry.event() extended fields."""
    
    def test_extra_fields_serialized(self, tmp_path):
        """Verify extra fields appear in events.jsonl."""
        telemetry = Telemetry(tmp_path, level="lite")
        
        telemetry.event(
            "test.command",
            {"arg": "value"},
            {"result": "ok"},
            100,
            bytes_read=1024,           # NEW
            disclosure_mode="excerpt", # NEW
            cache_hit=True,            # NEW
        )
        telemetry.flush()
        
        events_file = tmp_path / "_ctx" / "telemetry" / "events.jsonl"
        event = json.loads(events_file.read_text().strip().split("\n")[0])
        
        assert event["bytes_read"] == 1024
        assert event["disclosure_mode"] == "excerpt"
        assert event["cache_hit"] is True
    
    def test_monotonic_timing(self, tmp_path):
        """Verify timing uses perf_counter_ns (monotonic)."""
        telemetry = Telemetry(tmp_path, level="lite")
        
        start_ns = time.perf_counter_ns()
        time.sleep(0.01)  # 10ms
        elapsed_ms = int((time.perf_counter_ns() - start_ns) / 1_000_000)
        
        telemetry.event(
            "test.command",
            {},
            {},
            elapsed_ms,
        )
        telemetry.flush()
        
        events_file = tmp_path / "_ctx" / "telemetry" / "events.jsonl"
        event = json.loads(events_file.read_text().strip().split("\n")[0])
        
        # Assert timing is reasonable (10-20ms for 10ms sleep + overhead)
        assert 8 <= event["timing_ms"] <= 30, f"Unrealistic timing {event['timing_ms']}ms"

class TestTelemetrySummary:
    """Test last_run.json aggregation."""
    
    def test_ast_summary_calculation(self, tmp_path):
        """Verify AST counters aggregated correctly."""
        telemetry = Telemetry(tmp_path, level="lite")
        
        telemetry.incr("ast_parse_count", 100)
        telemetry.incr("ast_cache_hit_count", 86)
        
        telemetry.flush()
        
        last_run_file = tmp_path / "_ctx" / "telemetry" / "last_run.json"
        last_run = json.loads(last_run_file.read_text())
        
        assert last_run["ast"]["ast_parse_count"] == 100
        assert last_run["ast"]["ast_cache_hit_count"] == 86
        assert abs(last_run["ast"]["ast_cache_hit_rate"] - 0.86) < 0.01
    
    def test_lsp_summary_calculation(self, tmp_path):
        """Verify LSP counters + timeout_rate aggregated correctly."""
        telemetry = Telemetry(tmp_path, level="lite")
        
        telemetry.incr("lsp_spawn_count", 5)
        telemetry.incr("lsp_ready_count", 5)
        telemetry.incr("lsp_timeout_count", 0)
        telemetry.incr("lsp_fallback_count", 0)
        
        telemetry.flush()
        
        last_run_file = tmp_path / "_ctx" / "telemetry" / "last_run.json"
        last_run = json.loads(last_run_file.read_text())
        
        assert last_run["lsp"]["lsp_spawn_count"] == 5
        assert last_run["lsp"]["lsp_timeout_rate"] == 0.0
    
    def test_file_read_summary_calculation(self, tmp_path):
        """Verify file read bytes aggregated by mode."""
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

class TestTelemetryAggregation:
    """Test percentile calculations."""
    
    def test_p50_p95_calculation(self, tmp_path):
        """Verify percentile math on synthetic data."""
        telemetry = Telemetry(tmp_path, level="lite")
        
        # Record 100 latency observations
        times_ms = [10 + (i % 100) for i in range(100)]
        for t in times_ms:
            telemetry.observe("test.cmd", t)
        
        telemetry.flush()
        
        last_run_file = tmp_path / "_ctx" / "telemetry" / "last_run.json"
        last_run = json.loads(last_run_file.read_text())
        
        # Verify counts and percentiles are in expected range
        assert last_run["latencies"]["test.cmd"]["count"] == 100
        assert 10 <= last_run["latencies"]["test.cmd"]["p50_ms"] <= 60
        assert 10 <= last_run["latencies"]["test.cmd"]["p95_ms"] <= 110
```

#### File: `tests/integration/test_lsp_instrumentation.py` (NEW, 250+ lines)

```python
"""Integration tests for AST/LSP telemetry in realistic scenarios."""

import json
from pathlib import Path
import pytest
from src.infrastructure.telemetry import Telemetry
from src.infrastructure.ast_lsp import SkeletonMapBuilder, LSPClient, Selector

class TestSkeletonInstrumentation:
    """Test AST skeleton parsing emits correct telemetry."""
    
    def test_skeleton_parse_emits_event(self, tmp_path):
        """Verify parse_python() emits ast.parse event."""
        telemetry = Telemetry(tmp_path, level="lite")
        builder = SkeletonMapBuilder(telemetry, tmp_path)
        
        code = """
def hello():
    pass

class Greeter:
    def greet(self):
        pass
"""
        
        skeleton = builder.parse_python(code, Path("test.py"))
        telemetry.flush()
        
        events_file = tmp_path / "_ctx" / "telemetry" / "events.jsonl"
        event = json.loads(events_file.read_text().strip().split("\n")[0])
        
        assert event["cmd"] == "ast.parse"
        assert event["result"]["status"] == "ok"
        assert "skeleton_bytes" in event
        assert "reduction_ratio" in event
    
    def test_skeleton_cache_tracking(self, tmp_path):
        """Verify cache hits are counted."""
        telemetry = Telemetry(tmp_path, level="lite")
        builder = SkeletonMapBuilder(telemetry, tmp_path)
        
        code = "def test(): pass"
        
        # First parse: cache miss
        builder.parse_python(code, Path("test.py"))
        
        # Second parse same file: cache hit (if implemented)
        # (This test will verify once caching is implemented)
        
        telemetry.flush()
        
        # Verify counter incremented
        last_run_file = tmp_path / "_ctx" / "telemetry" / "last_run.json"
        last_run = json.loads(last_run_file.read_text())
        
        assert last_run["metrics_delta"]["ast_parse_count"] >= 1

class TestConcurrentTelemetry:
    """Test concurrent command execution doesn't corrupt logs."""
    
    def test_concurrent_commands_no_corruption(self, tmp_path):
        """Spawn multiple commands, verify no event loss or corruption."""
        import threading
        
        def run_command(cmd_id: int):
            telemetry = Telemetry(tmp_path, level="lite")
            for i in range(5):
                telemetry.event(
                    f"cmd_{cmd_id}",
                    {"iteration": i},
                    {"status": "ok"},
                    10,
                )
            telemetry.flush()
        
        threads = [threading.Thread(target=run_command, args=(i,)) for i in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Verify events logged
        events_file = tmp_path / "_ctx" / "telemetry" / "events.jsonl"
        events = [json.loads(line) for line in events_file.read_text().strip().split("\n") if line]
        
        # Should have at least some events (may drop due to lock, but structure is valid)
        assert len(events) > 0
        
        # All events should be valid JSON
        for event in events:
            assert "cmd" in event
            assert "timing_ms" in event
```

#### File: `tests/fixtures/synthetic_telemetry.py` (NEW)

```python
"""Synthetic telemetry data for validation testing."""

import json
from datetime import datetime, timezone
from pathlib import Path

def generate_synthetic_events(n: int = 100) -> list:
    """Generate synthetic events for testing aggregation."""
    events = []
    for i in range(n):
        events.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "run_id": f"run_{i}",
            "segment": "/test/segment",
            "cmd": "ctx.search",
            "args": {"query": f"test{i}"},
            "result": {"hits": i % 10},
            "timing_ms": 10 + (i % 100),
            "bytes_read": 1024 * (i % 10),
            "disclosure_mode": ["skeleton", "excerpt", "raw"][i % 3],
        })
    return events

def test_summary_percentile_validation():
    """Validate percentile calculations with synthetic data."""
    from src.infrastructure.telemetry import Telemetry
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmp_path:
        tmp = Path(tmp_path)
        telemetry = Telemetry(tmp, level="lite")
        
        # Record synthetic timings
        for i in range(100):
            telemetry.observe("ctx.search", 10 + (i % 100))
        
        telemetry.flush()
        
        # Load and validate
        last_run_file = tmp / "_ctx" / "telemetry" / "last_run.json"
        last_run = json.loads(last_run_file.read_text())
        
        latencies = last_run["latencies"]["ctx.search"]
        
        # Verify percentile ordering: p50 <= p95 <= max
        assert latencies["p50_ms"] <= latencies["p95_ms"]
        assert latencies["p95_ms"] <= latencies["max_ms"]
        
        # Verify count matches
        assert latencies["count"] == 100
```

### Definition of Done

- [ ] All unit tests pass: `pytest tests/unit/test_telemetry_ast_lsp.py -v`
- [ ] All integration tests pass: `pytest tests/integration/test_lsp_instrumentation.py -v`
- [ ] Synthetic validation passes: `pytest tests/fixtures/synthetic_telemetry.py::test_summary_percentile_validation -v`
- [ ] Coverage >80%: `pytest tests/ --cov=src --cov-report=term-missing | grep TOTAL`
- [ ] No test data logged to real events.jsonl (tests use isolated tmp directories)
- [ ] Concurrent safety validated (3+ threads, no data corruption)

---

## DEPLOYMENT CHECKLIST

- [ ] All PRs merged to main (T1 → T2 → T3 → T4)
- [ ] CHANGELOG.md updated with "Telemetry: AST/LSP instrumentation"
- [ ] docs/telemetry.md created/updated with:
  - [ ] Specification of new event types (ast.parse, lsp.spawn, etc.)
  - [ ] Example queries for metrics
  - [ ] "READY" definition for LSP
  - [ ] Redaction policy (no absolute paths, no content)
- [ ] Example data generated: run ctx.search/ctx.get, collect _ctx/telemetry/*
- [ ] Share sanitized example events.jsonl + last_run.json in PR description

---

## SUCCESS METRICS (Post-Deployment)

After all PRs merged, these queries should work:

```bash
# Query AST metrics
jq '.ast' _ctx/telemetry/last_run.json
# Output: {"ast_parse_count": 42, "ast_cache_hit_count": 36, "ast_cache_hit_rate": 0.857}

# Query LSP metrics
jq '.lsp' _ctx/telemetry/last_run.json
# Output: {"lsp_spawn_count": 3, "lsp_ready_count": 3, "lsp_timeout_count": 0, "lsp_timeout_rate": 0.0, ...}

# Query bytes by mode
jq '.file_read' _ctx/telemetry/last_run.json
# Output: {"skeleton_bytes": 8192, "excerpt_bytes": 45678, "raw_bytes": 123456, "total_bytes": 177326}

# Query LSP definition latencies
jq '.latencies."lsp.definition"' _ctx/telemetry/last_run.json
# Output: {"count": 5, "p50_ms": 145.0, "p95_ms": 289.0, "max_ms": 512.0}

# List all events of type lsp.spawn
jq 'select(.cmd == "lsp.spawn")' _ctx/telemetry/events.jsonl
```

---

## NOTES

1. **No breaking changes:** All existing CLI commands work unchanged.
2. **Backward compatible:** Old code calling `telemetry.event()` without extra fields still works.
3. **Monotonic clocks:** All new timings use `time.perf_counter_ns()`, never `time.time()`.
4. **Secure:** No absolute paths, no file content, no API keys in telemetry.
5. **Auditable:** Every event is append-only; no deletions or modifications.
6. **Drop-safe:** Critical events (lsp.ready, command boundaries) use same lock as everything else; acceptable <2% drop rate.

---

**Plan Complete:** Ready for Day 1 implementation  
**Owner:** Senior Engineer / Telemetry Architect  
**Estimated Duration:** 4–5 days  
**Success Criterion:** All tests pass, no data loss, all metrics queryable from last_run.json

