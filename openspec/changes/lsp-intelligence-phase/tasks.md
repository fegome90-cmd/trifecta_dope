# Tasks: LSP Intelligence Phase

## Phase 1: Domain — Semantic Predicate Detection

- [x] 1.1 Add `SemanticPredicate` frozen dataclass to `src/domain/query_classifier.py`: fields `method: Literal["hover"]` and `target: str`
- [x] 1.2 Add `semantic: Optional[SemanticPredicate]` field to `QueryClass` dataclass in `src/domain/query_classifier.py`
- [x] 1.3 Add EN semantic patterns to `query_classifier.py`: `"what is X"`, `"show me X"` (hover-aligned only)
- [x] 1.4 Add ES semantic patterns to `query_classifier.py`: `"que es X"`, `"mostrame X"` (hover-aligned only)
- [x] 1.5 Update `classify_query()` to populate `semantic` field alongside existing `predicate` field; return both when present
- [x] 1.6 Write unit tests in `tests/unit/test_query_classifier_semantic.py`: EN patterns, ES patterns, non-semantic returns `None`, mixed relational+semantic returns both

## Phase 2: Core Signal — `_execute_lsp_signal()` Method

- [x] 2.1 Add `_execute_lsp_signal()` method to `SearchOracleUseCase` in `src/application/oracle_use_case.py`: signature `(repo_path, query, timings, ast_result) -> str | Dict`, following `_execute_graph_signal()` pattern
- [x] 2.2 Implement Gate A (predicate): call `classify_query(query).semantic`; if `None`, return `"lsp_not_applicable"`
- [x] 2.3 Implement Gate B (injection): check `self.lsp_client is not None`; if not, return `"lsp_not_injected"`
- [x] 2.4 Implement Gate C (state): check `self.lsp_client.state == READY`; if not, return `"lsp_not_ready"`
- [x] 2.5 Implement Gate D (position): look up symbol in `ast_result.symbols` by `semantic.target` to get `source_file` + `start_line`; if no match, return `"lsp_no_result"` (no LSP request issued)
- [x] 2.6 Implement Gate E (budget): check elapsed < 20ms; if over, return `"lsp_timeout"`
- [x] 2.7 Implement hover request: call `self.lsp_client.request("textDocument/hover", {uri, position})`; handle error -> `"lsp_error"`, empty -> `"lsp_no_result"`, success -> return `lsp_data` dict
- [x] 2.8 Replace LSP stub (lines 97-113) in `execute()` with call to `_execute_lsp_signal()`; wire return value into `lsp_data` and `metadata["lsp_signal"]`
- [x] 2.9 Update fidelity logic: `full` when `lsp_signal == "lsp_used"`, `degraded` when AST available without LSP, `fallback` otherwise

## Phase 3: Telemetry — Observability

- [x] 3.1 Add `lsp_signal` to `ctx_oracle` telemetry event result dict in `src/application/oracle_use_case.py`
- [x] 3.2 Add `lsp_signal_ms` from `timings` to telemetry event result dict
- [x] 3.3 Verify `lsp_signal` is emitted for every Oracle call (including `"lsp_not_injected"` when no client)

## Phase 4: Tests — Validation

- [x] 4.1 Create `tests/unit/test_lsp_signal.py` with helper `_make_oracle_with_lsp(lsp_client)` and mock LSP client factory
- [x] 4.2 Test `test_lsp_signal_not_applicable` — non-semantic query -> `"lsp_not_applicable"`, no request issued
- [x] 4.3 Test `test_lsp_signal_not_injected` — no LSP client -> `"lsp_not_injected"`
- [x] 4.4 Test `test_lsp_signal_not_ready_cold` and `test_lsp_signal_not_ready_warming` — non-READY states -> `"lsp_not_ready"`
- [x] 4.5 Test `test_lsp_signal_not_ready_failed` and `test_lsp_signal_not_ready_closed` — FAILED and CLOSED states -> `"lsp_not_ready"`
- [x] 4.6 Test `test_lsp_signal_timeout` — patch `_LSP_BUDGET_MS=0.0` -> `"lsp_timeout"` (deterministic; Gate E checks budget AFTER request)
- [x] 4.7 Test `test_lsp_signal_error` — mock request returns error dict -> `"lsp_error"`
- [x] 4.8 Test `test_lsp_signal_no_result` — mock request returns `None`/empty -> `"lsp_no_result"`
- [x] 4.9 Test `test_lsp_signal_used_hover` — mock hover returns contents -> `"lsp_used"`, `lsp_data` populated with method/target/contents/latency
- [x] 4.10 Test `test_lsp_signal_es_query` — `"que es resolve_segment_ref"` -> predicate detected, hover issued
- [x] 4.11 Test `test_lsp_signal_ast_no_symbol_match` — AST returns no matching symbol -> `"lsp_no_result"`, no LSP request
- [x] 4.12 Test `test_lsp_signal_ast_multiple_match` — AST finds symbol at multiple positions -> first match used for hover
- [x] 4.13 Test `test_lsp_signal_telemetry_recorded` — spy on telemetry mock, verify `lsp_signal` in event result
- [x] 4.14 Test `test_lsp_signal_fidelity_promotion` — LSP used -> `"full"`, LSP unavailable + AST -> `"degraded"`, PRIME only -> `"fallback"`
- [x] 4.15 Run full suite: 103 tests pass — 16 graph + 44 adversarial + 26 semantic + 17 LSP signal, zero regression

## Phase 5: Benchmark — Quality Verification

- [x] 5.1 Create benchmark script `scripts/benchmark_lsp_signal.py`: 25 queries (15 semantic + 5 non-semantic + 3 negative + 2 ambiguous), 5 dimensions + memory soak, verify p95 < 65ms
- [x] 5.2 Run benchmark with LSP active (READY) and LSP disabled (`None`); verify zero regression in PRIME chunks, AST symbols, graph_signal states — 8/8 PASS
- [x] 5.3 Run memory soak: 100 iterations, verify < 10MB growth — 1.19MB growth, PASS

## Closure

**Status**: CLOSED (2026-04-25). Hover-only LSP signal integrated into Oracle.
**Does NOT close**: future definition/references phases, unrelated Oracle slices.
**Repos green**: no-regression confirmed on Oracle slice (PRIME/AST/Graph/LSP). Full suite has pre-existing failures in unrelated validators.
