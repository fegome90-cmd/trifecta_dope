# Proposal: LSP Signal Integration for SearchOracle

## Problem

The Oracle (`SearchOracleUseCase`) fuses PRIME, AST, and Graph signals, but the LSP signal is a stub -- step 4 checks `LSPClient.state` and sets a placeholder `lsp_data` dict, never issuing actual LSP requests. This means queries like "what is `resolve_segment_ref`" get documentation and symbol names, but miss the type signature, docstring, and exact definition location that only a language server can provide. The `lsp_data` field on `OracleResult` exists but is always `None` or a status placeholder.

## Approach

Wire the existing `LSPClient` infrastructure into the Oracle's step 4 to issue real `textDocument/hover` requests for semantic queries. This phase is **hover-only** — definition and references are deferred to a future phase. Introduce a 7-state LSP signal taxonomy (`lsp_not_applicable`, `lsp_not_injected`, `lsp_not_ready`, `lsp_timeout`, `lsp_error`, `lsp_no_result`, `lsp_used`) reported in `metadata.lsp_signal`. LSP requests are gated by a predicate detector that activates only for hover-aligned queries ("what is X", "show me X"), keeping non-semantic queries untouched. A 20ms per-query budget (post-hoc over-budget check after request completes; result discarded if exceeded) ensures the 65ms total Oracle budget is preserved.

## Capabilities

### New Capabilities
- **lsp-signal-integration**: Populates `OracleResult.lsp_data` with hover data (type signatures and docstrings) from a real LSP server. Hover-only scope — `textDocument/definition` and `textDocument/references` are future enhancements. Includes predicate detection (only activates for "what is X" / "show me X" queries), a 7-state signal taxonomy in `metadata.lsp_signal`, 20ms per-query budget (post-hoc over-budget check), symbol disambiguation via AST positioning, and telemetry emission for every LSP outcome.

### Modified Capabilities
- **unified-intelligence-oracle**: The Oracle pipeline in `src/application/oracle_use_case.py` gains a real LSP signal in step 4 (replacing the stub). The change is additive -- PRIME, AST, and Graph logic are untouched. Fidelity promotion logic upgrades to `full` only when LSP returns usable data.

## Scope

### In Scope
- `lsp_data` population in `OracleResult` via `LSPClient.request()`
- `metadata.lsp_signal` taxonomy (7 states)
- LSP query predicate detection (semantic queries only)
- Per-query 20ms budget (post-hoc over-budget check; result discarded if exceeded)
- Telemetry: `ctx_oracle` event includes `lsp_signal` state
- LSP-specific tests (>=20, covering all 7 signal states)
- Benchmark: hover accuracy, latency p95, fallback correctness

### Out of Scope
- Graph signal changes or new `graph_signal` states
- `GraphStore` / `graph_service.py` modifications
- New top-level `OracleResult` fields
- `LSPClient` infrastructure changes (already complete)
- `textDocument/definition` — future phase
- `textDocument/references` — future phase
- Embeddings, vector search, multi-hop traversal, import chain analysis

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LSP adds >20ms to non-LSP queries | Low | High | Predicate gate skips LSP entirely for non-semantic queries; state check is ~1ms |
| LSP subprocess crashes mid-query | Medium | Medium | `LSPState.FAILED` + `_emit_fallback()` already exist in `LSPClient` |
| Graph taxonomy accidentally modified | Low | Critical | Kill criteria: any graph_signal test break stops the phase |
| LSP returns stale/wrong hover data | Medium | Low | PRIME is SSOT -- LSP supplements, never overrides |
| Memory growth from LSP thread state | Low | Medium | Kill criteria: >10MB growth over 100-iteration soak |

## Success Criteria
- `lsp_data` populated with hover data for semantic queries when LSP is READY
- `metadata.lsp_signal` set for every query (even `lsp_not_applicable` or `lsp_not_injected`)
- All 60 existing tests pass unchanged (16 graph signal + 44 adversarial)
- >=20 new LSP-specific tests covering all 7 signal states
- Latency p95 < 65ms with LSP active over 100 mixed queries
- Zero regression in PRIME chunks, AST symbols, graph_signal states
- Telemetry `ctx_oracle` event includes `lsp_signal` on every call

## Kill Criteria
- Any existing graph_signal test breaks
- Latency regression >20ms on non-LSP queries
- LSPClient changes break daemon lifecycle
- Memory growth >10MB over 100-iteration soak
- LSP causes Oracle crashes on any query or state
- Graph taxonomy modified to accommodate LSP
