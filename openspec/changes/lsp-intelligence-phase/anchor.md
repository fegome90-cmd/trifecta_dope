# LSP Intelligence Phase — Anchor Document

**Phase**: lsp-intelligence-phase
**Opened**: 2026-04-24
**Status**: OPEN — Planning only, no implementation
**Predecessor**: WO-0043 (Oracle Reliability Gate, commit `0150e15f`)

---

## 1. Inherited Baseline

The Oracle enters this phase with a **frozen contract**:

### Signal Pipeline (immutable order)
```
PRIME (SSOT) → AST (structural) → Graph (relational) → LSP (deep semantic)
```

### OracleResult Shape (frozen)
```python
class OracleResult(BaseModel):
    fidelity: Literal["full", "degraded", "fallback"]
    lsp_data: Optional[Dict[str, Any]]     # ← LSP phase target
    ast_symbols: List[str]
    prime_chunks: List[SearchHit]
    graph_data: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]
```

### Graph Signal Taxonomy (frozen — 7 states)
`no_predicate` · `unavailable` · `stale` · `timeout` · `target_not_found` · `ambiguous_target` · `used`

### Mandatory Metadata (frozen)
- `metadata.graph_signal`: one of 7 states
- `metadata.latency_ms`: total oracle latency
- `metadata.timings`: per-signal breakdown
- `metadata.query`: original query string
- `metadata.hit_count`: PRIME results count

### Test Baseline
- 16 graph signal tests in `test_oracle_graph_signal.py`
- 44 adversarial tests in `test_oracle_adversarial.py`
- 0 crashes, 0 wrong states under adversarial conditions

---

## 2. Non-Negotiable Invariants

These constraints MUST hold throughout the LSP phase. Violation = stop and escalate.

1. **PRIME is SSOT**: LSP data supplements but never overrides PRIME results
2. **Graph taxonomy untouched**: No new graph_signal states, no renames
3. **Graph code untouched**: No changes to `graph_store.py`, `graph_service.py`, or graph signal logic
4. **Fidelity model preserved**: `full` / `degraded` / `fallback` semantics unchanged
5. **Latency budget**: Total Oracle latency MUST stay under 65ms with LSP active
6. **Backward compatible**: `lsp_data=None` must remain valid — Oracle works without LSP
7. **No new signals outside LSP**: Only `lsp_data` field changes; no new top-level fields
8. **Telemetry discipline**: Every LSP outcome emits `ctx_oracle` telemetry with `lsp_signal` state

---

## 3. LSP Problem Statement

### What LSP Adds (that PRIME+AST+Graph cannot)

| Capability | PRIME | AST | Graph | LSP (this phase) | LSP (future) |
|-----------|-------|-----|-------|-------------------|--------------|
| Documentation text | YES | no | no | no | no |
| Symbol names in file | no | YES | YES | YES | YES |
| Callers/callees | no | no | YES | no | no |
| **Hover (type + docstring)** | no | no | no | **YES** | YES |
| **Symbol resolution** | fuzzy | exact | fuzzy | **exact** | exact |
| Go-to-definition | no | no | no | no | **FUTURE** |
| Find-all-references | no | no | no | no | **FUTURE** |

**This phase is HOVER-ONLY.** The LSP signal issues a single `textDocument/hover` request per query. Definition and references are documented as future enhancements, not current deliverables.

The gap: when a user asks "what is `resolve_segment_ref`", PRIME returns documentation chunks, AST returns the symbol name, but nobody returns the **type signature or docstring** at query time. Hover fills this gap.

### Why Now

The Oracle has a stable fallback pipeline (PRIME+AST+Graph). Adding LSP is safe because:
- `lsp_data` field already exists in `OracleResult`
- `LSPClient` already exists with state management, fallback emission, invariant checks
- Fidelity model already accounts for LSP readiness (`full` = LSP ready, `degraded` = AST only, `fallback` = PRIME only)

---

## 4. LSP Signal States

LSP introduces its own signal taxonomy, parallel to graph_signal:

| LSP Signal | Trigger | lsp_data |
|-----------|---------|----------|
| `lsp_not_applicable` | Query has no semantic predicate | null |
| `lsp_not_injected` | No LSPClient provided to Oracle | null |
| `lsp_not_ready` | LSPClient.state in {COLD, WARMING, FAILED, CLOSED} | null |
| `lsp_timeout` | LSP request completes but exceeds 20ms budget (post-hoc over-budget detection; result discarded) | null |
| `lsp_error` | LSP returns error response | null |
| `lsp_no_result` | LSP returns null/empty, OR AST cannot resolve symbol position | null |
| `lsp_used` | LSP returns valid hover data | populated |

These are reported in `metadata.lsp_signal` (new metadata key, NOT a new top-level field).

---

## 5. Latency Budget

```
Total Oracle budget:     65ms
├── PRIME search:       ~15ms (existing)
├── AST resolution:     ~5ms  (existing)
├── Graph signal:       ~15ms (existing, conditional)
└── LSP signal:         ~20ms (NEW, conditional)
    ├── State check:    ~1ms
    ├── Request:        ~15ms
    └── Parse:          ~4ms
```

LSP signal is **conditional** — only activated for queries with semantic-resolution predicates:
- "what is X" / "qué es X"
- "show me X" / "mostrame X"

Patterns for definition/references ("definition of X", "where is X defined") are deferred to a future phase. This phase triggers hover only.

Queries like "how to configure daemon" or "who calls foo" do NOT trigger LSP.

---

## 6. Degradation Contract

### When LSP Fails
- `lsp_data` remains `null`
- `metadata.lsp_signal` reports the failure reason
- Fidelity downgrades: `full` → `degraded` (if AST available) → `fallback` (PRIME only)
- PRIME, AST, and Graph results are **untouched** — no regression

### When LSP is Slow
- Per-query budget: 20ms (post-hoc check after request completes; no hard cancellation)
- If exceeded: `metadata.lsp_signal = "lsp_timeout"`, LSP result discarded, proceed without LSP data

---

## 7. Quality Benchmark Requirements

The LSP phase MUST define a benchmark that measures:

### 7.1 Hover Accuracy
- Given a symbol name in a query, does LSP return correct hover data (type signature, docstring)?
- Target: 90%+ for symbols that exist in the workspace

### 7.2 Ambiguous Symbol Handling
- Given a symbol that exists in multiple files, does the disambiguation contract resolve correctly?
- Target: explicit disambiguation or correct fallback (see §12)

### 7.3 Latency Under Load
- Run Oracle 100 times with mixed queries (LSP + non-LSP)
- p95 latency MUST stay under 65ms
- No memory leaks over 100 iterations

### 7.4 Fallback Correctness
- With LSP disabled: Oracle returns identical results to pre-LSP baseline
- Zero regression in graph_signal, PRIME chunks, AST symbols

---

## 8. Acceptance Criteria

LSP phase is complete when:

1. `lsp_data` is populated for semantic queries when LSP is READY
2. `metadata.lsp_signal` is set for every query (even if `"lsp_not_applicable"` or `"lsp_not_injected"`)
3. Fidelity correctly reflects LSP readiness
4. All 60 existing tests pass unchanged (16 in `test_oracle_graph_signal.py` + 44 in `test_oracle_adversarial.py`)
5. New LSP-specific tests: ≥20 covering all 7 signal states
6. Benchmark shows no regression in PRIME/AST/Graph dimensions
7. Latency p95 < 65ms with LSP active
8. Telemetry `ctx_oracle` event includes `lsp_signal` state

---

## 9. Kill Criteria

STOP the LSP phase and escalate if:

- Any existing graph_signal test breaks
- Latency regression >20ms on non-LSP queries
- LSPClient changes break daemon lifecycle
- Memory growth >10MB over 100-iteration soak
- LSP causes Oracle crashes (any query, any state)
- Graph taxonomy is modified to accommodate LSP

---

## 10. Inherited Risks

| Risk | Mitigation | Status |
|------|-----------|--------|
| LSP subprocess crash during query | `LSPState.FAILED` + `_emit_fallback()` | Already in `LSPClient` |
| LSP warming timeout | Fidelity = `degraded`, proceed without LSP | Already in Oracle |
| Thread safety in LSPClient | `self.lock` on state transitions | Already in `LSPClient` |
| Stale LSP diagnostics | `did_open()` for fresh files | Already in `LSPClient` |
| LSP binary not found | `LSPState.FAILED`, graceful fallback | Already in `LSPClient` |
| Graph+LSP conflicting results | PRIME is SSOT, both are derived | Architecture constraint |

---

## 11. Scope Boundaries

### IN Scope
- `lsp_data` population in OracleResult
- `metadata.lsp_signal` taxonomy
- LSP query predicate detection
- LSP signal latency budget
- Telemetry integration
- Tests and benchmark

### OUT of Scope
- Graph signal changes
- New graph_signal states
- SQLite/GraphStore modifications
- New top-level OracleResult fields
- `textDocument/definition` — future phase
- `textDocument/references` — future phase
- `lsp_partial` semantics — not applicable in hover-only phase
- Embeddings / vector search
- Multi-hop traversal
- Import chain analysis

---

## 12. Symbol Disambiguation Contract

LSP requires a file URI + line position. AST resolves symbols from the top PRIME hit's file. Disambiguation rules:

1. **AST finds exactly one match** → Use it. Issue hover request with that file + line.
2. **AST finds multiple matches in the same file** → Use first match (Python re-definitions are rare; first is canonical).
3. **Symbol not found in AST** → Do NOT issue LSP request. Return `"lsp_no_result"`.
4. **No confidence** (e.g., AST found symbol but from wrong file, or PRIME returned no hits) → Do NOT issue LSP request. Return `"lsp_no_result"`.

**Key invariant**: Never issue a speculative LSP request. If AST cannot provide a file+line, LSP is skipped. This prevents wasted latency on uncertain positioning.
