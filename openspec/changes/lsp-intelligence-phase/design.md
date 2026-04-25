# Design: LSP Intelligence Phase

## Technical Approach

LSP becomes the 4th signal in the Oracle pipeline, following the established Graph signal pattern exactly. The signal order remains frozen: PRIME -> AST -> Graph -> LSP. This phase is **hover-only** — the system issues a single `textDocument/hover` per query. LSP activates only when three gates pass: (1) the query contains a semantic predicate ("what is X", "show me X"), (2) `LSPClient` is injected, and (3) `LSPClient.state == READY`. A per-query 20ms budget prevents LSP from blowing the 65ms total Oracle ceiling.

The existing step 4 in `SearchOracleUseCase.execute()` is a stub that checks state and sets a placeholder dict. This design replaces that stub with `_execute_lsp_signal()`, a method mirroring the proven `_execute_graph_signal()` pattern: predicate detection -> state gate -> budget gate -> request -> result assembly.

## Architecture Decisions

### Decision: Extend `query_classifier.py` with `SemanticPredicate`
**Choice**: Add a new `SemanticPredicate` dataclass and a `semantic` field to `QueryClass` in the existing `query_classifier.py` module.
**Alternatives considered**: Separate `src/domain/lsp_predicate.py` module.
**Rationale**: The classifier is already the single point of predicate detection. A separate module would scatter the "what does this query want?" logic across two files. `QueryClass` gains `semantic: Optional[SemanticPredicate]` alongside `predicate: Optional[RelationalPredicate]`. Both are optional and independent — a query can have neither, one, or both (e.g., "what is foo and who calls it"). The `method` field starts as `Literal["hover"]` only, extensible to `"definition"` and `"references"` in future phases.

### Decision: `_execute_lsp_signal()` as method on `SearchOracleUseCase`
**Choice**: New private method on the existing use case, following the `_execute_graph_signal()` pattern.
**Alternatives considered**: Separate `LspSignalUseCase` class with its own `execute()`.
**Rationale**: The graph signal proved that a private method works cleanly. The method is stateless (reads from injected `self.lsp_client`), returns a discriminated union (signal string or data dict), and keeps all signal orchestration in one class. A separate use case would add indirection without benefit since the Oracle is the sole consumer.

### Decision: AST-first symbol resolution for LSP positioning
**Choice**: Use AST `SymbolInfo` (which has `start_line` from `SkeletonMapBuilder.build()`) to resolve the symbol to a file URI + line position before issuing LSP requests.
**Alternatives considered**: Let LSP resolve the symbol via `textDocument/documentSymbol` on its own.
**Rationale**: LSP requires a `Position{line, character}` to request hover/definition. We already have AST with exact line numbers from the top PRIME hit's file. Using AST to bootstrap LSP avoids a round-trip and keeps the pipeline compositional. If AST has no symbol match, we skip LSP for that query -- no speculative requests.

### Decision: Hover-only initial scope for LSP methods
**Choice**: Issue only `textDocument/hover` in the initial implementation. Definition and references are deferred.
**Alternatives considered**: All three methods (hover + definition + references) from day one.
**Rationale**: Hover gives the highest value (type signature + docstring) with a single request. Definition and references add latency and complexity (multiple requests, merging). The 20ms budget allows at most one request. Hover-first validates the pipeline, then definition/references follow as enhancements.

## Data Flow

```
execute(repo_path, query, k)
  |
  +-- 1. PRIME search (ContextService) -> hits[]
  |
  +-- 2. AST resolution (SkeletonMapBuilder) -> ast_symbols[]
  |       Also: extract SymbolInfo with start_line for LSP positioning
  |
  +-- 3. Graph signal (_execute_graph_signal) -> graph_signal state/data
  |
  +-- 4. LSP signal (_execute_lsp_signal) -> lsp_signal state/data
  |     |
  |     +-- Gate A: classify_query(query).semantic != None?
  |     |     No  -> return "lsp_not_applicable"
  |     +-- Gate B: self.lsp_client is not None?
  |     |     No  -> return "lsp_not_injected"
  |     +-- Gate C: lsp_client.state == READY?
  |     |     No  -> return "lsp_not_ready"
  |     +-- Gate D: Resolve symbol file+line from AST results
  |     |     No match -> return "lsp_no_result"
  |     +-- Gate E: Budget check (elapsed < 20ms)?
  |     |     Over -> return "lsp_timeout"
  |     +-- Execute: lsp_client.request("textDocument/hover", {...})
  |     |     Error -> return "lsp_error"
  |     |     Empty -> return "lsp_no_result"
  |     +-- Success -> return {"method": "hover", "target": X, ...}
  |
  +-- 5. Assemble OracleResult with lsp_data, metadata.lsp_signal
  +-- 6. Emit telemetry (ctx_oracle with lsp_signal)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/domain/query_classifier.py` | MODIFY | Add `SemanticPredicate` dataclass, `semantic` field to `QueryClass`, EN/ES pattern lists for "what is X", "definition of X", "show me X" |
| `src/application/oracle_use_case.py` | MODIFY | Replace LSP stub (lines 97-113) with `_execute_lsp_signal()` method call; update metadata and telemetry to include `lsp_signal` |
| `src/application/ast_parser.py` | MODIFY (minor) | Add `find_symbol(name: str) -> Optional[SymbolInfo]` method to `ParseResult` for LSP position lookup |
| `tests/unit/test_lsp_signal.py` | CREATE | >=20 tests covering all 6 LSP signal states |

## Interfaces / Contracts

### New Types in `src/domain/query_classifier.py`

```python
@dataclass(frozen=True)
class SemanticPredicate:
    """A detected semantic-resolution intent from a query."""
    method: Literal["hover"]   # Extensible: "definition", "references" later
    target: str                # The symbol name extracted from the query

@dataclass(frozen=True)
class QueryClass:
    predicate: Optional[RelationalPredicate]
    semantic: Optional[SemanticPredicate]   # NEW
```

### New Method on `SearchOracleUseCase`

```python
def _execute_lsp_signal(
    self,
    repo_path: Path,
    query: str,
    timings: Dict[str, Any],
    ast_result: Optional[ParseResult] = None,  # For symbol position lookup
) -> str | Dict[str, Any]:
    """Execute LSP signal if query has semantic predicate.
    Returns either a signal state string or an lsp_data dict."""
```

### `lsp_data` Shape

```python
# When lsp_signal == "lsp_used"
{
    "method": "hover",
    "target": "resolve_segment_ref",
    "contents": [       # LSP Hover result contents
        {"language": "python", "value": "def resolve_segment_ref(...)"},
        {"kind": "plaintext", "value": "Resolves segment..."}
    ],
    "latency_ms": 12.4,
    "source_file": "src/domain/segment_resolver.py",
    "source_line": 42,
}
```

### `metadata.lsp_signal` Values

`lsp_not_applicable` | `lsp_not_injected` | `lsp_not_ready` | `lsp_timeout` | `lsp_error` | `lsp_no_result` | `lsp_used`

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| **Unit: Predicate detection** | `classify_query()` detects semantic predicates for EN/ES patterns, extracts target symbol, returns None for non-semantic queries | Pure function tests, no IO, no mocks |
| **Unit: LSP signal states** | All 7 states: not applicable, not injected, not ready (each COLD/WARMING/FAILED/CLOSED), timeout, error, no result, used | Mock `LSPClient` with controlled `state` and `request()` return; verify `metadata.lsp_signal` and `lsp_data` |
| **Unit: Budget enforcement** | LSP request exceeding 20ms returns `"lsp_timeout"`, Oracle total under 65ms | Mock `request()` with `time.sleep`; assert signal state and latency |
| **Unit: Graph independence** | LSP activation does not affect graph signal states or data | Run queries triggering both signals; verify graph_data and lsp_data are independent |
| **Unit: AST fallback for position** | When AST has no matching symbol, LSP returns `"lsp_no_result"` without issuing request | Mock `SkeletonMapBuilder` returning empty symbols; verify no `request()` call |
| **Integration: Fidelity promotion** | LSP used -> "full", LSP unavailable with AST -> "degraded", PRIME only -> "fallback" | End-to-end Oracle calls with mock LSP client in various states |
| **Integration: Telemetry** | Every Oracle call emits `ctx_oracle` with `lsp_signal` in result payload | Spy on telemetry mock; verify event structure |

### LSP Signal State Tests (minimum — 7 states + edge cases)

1. `test_lsp_signal_not_applicable` -- non-semantic query -> `"lsp_not_applicable"`, no request issued
2. `test_lsp_signal_not_injected` -- no LSP client -> `"lsp_not_injected"`
3. `test_lsp_signal_not_ready_cold` -- COLD state -> `"lsp_not_ready"`
4. `test_lsp_signal_not_ready_warming` -- WARMING state -> `"lsp_not_ready"`
5. `test_lsp_signal_not_ready_failed` -- FAILED state -> `"lsp_not_ready"`
6. `test_lsp_signal_not_ready_closed` -- CLOSED state -> `"lsp_not_ready"`
7. `test_lsp_signal_timeout` -- request exceeds 20ms -> `"lsp_timeout"`
8. `test_lsp_signal_error` -- request returns error -> `"lsp_error"`
9. `test_lsp_signal_no_result` -- request returns None/empty -> `"lsp_no_result"`
10. `test_lsp_signal_used_hover` -- successful hover -> `"lsp_used"` with populated `lsp_data`
11. `test_lsp_signal_es_query` -- "que es resolve_segment_ref" -> `"lsp_used"`
12. `test_lsp_signal_ast_no_match` -- AST returns no matching symbol -> `"lsp_no_result"`, no request issued

## Migration / Rollout

No migration required. The change is purely additive:
- `lsp_data` already exists on `OracleResult` (always `None` today)
- `LSPClient` is already injected via constructor (optional)
- Non-semantic queries skip LSP entirely (zero behavior change)
- Deploying with `lsp_client=None` preserves exact current behavior
- Fidelity model semantics are unchanged: `full`/`degraded`/`fallback` gain a new trigger (LSP data) but the downgrade path is identical
