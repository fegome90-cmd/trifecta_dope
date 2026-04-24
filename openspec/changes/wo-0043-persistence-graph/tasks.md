# Tasks: WO-0043 — GraphStore como Señal Derivada del Oracle

## Phase 0: Validation Benchmark (Kill Gate)

- [x] 0.1 Run benchmark with 20 queries (5 caller, 5 callee, 5 no-relacional, 5 ambigua) against existing GraphStore
- [x] 0.2 Measure routing accuracy, caller recall, latency p95
- [x] 0.3 Produce report. **Kill gate**: routing 100%, p95 3.7ms → PASS

## Phase 1: Domain Types (RED → GREEN)

- [x] 1.1 Write failing tests for `classify_query()` in `tests/unit/test_query_classifier.py` — 12 cases: callers EN ("who calls X"), callers ES ("quién llama a X", "quién llama al X"), callees EN/ES, no-predicate, empty target, borderline
- [x] 1.2 Create `src/domain/query_classifier.py` with `RelationalPredicate(relation, target)`, `QueryClass(predicate)`, `classify_query()` — EN+ES patterns including "al"/"a la" contractions — make tests pass
- [x] 1.3 Write failing test: `OracleResult` accepts `graph_data: Optional[Dict]` field, defaults None
- [x] 1.4 Add `graph_data` field to `OracleResult` in `src/domain/context_models.py` — make test pass

## Phase 2: Oracle Graph Signal (RED → GREEN)

- [x] 2.1 Write failing tests for `_execute_graph_signal()` in `tests/unit/test_oracle_graph_signal.py` — 8 scenarios: graph unavailable, stale graph (>7 days via mock), target not found, timeout (mock time.sleep), callers success, callees success, empty target, GraphStoreAccessError handling
- [x] 2.2 Add `graph_service: Optional[GraphService]` keyword param to `SearchOracleUseCase.__init__`
- [x] 2.3 Implement `_is_graph_fresh(status)` helper — parse ISO `last_indexed_at`, compare with `datetime.now(timezone.utc)`, return bool
- [x] 2.4 Implement `_execute_graph_signal()` — staleness gate via `_is_graph_fresh`, single DB connection (use `GraphStore.open_readonly` for both check + query), latency budgets (total <15ms), fuzzy target resolution (use `search_nodes` LIKE match, not exact `find_target_candidates`), trimmed node output: `{symbol_name, qualified_name, file_rel, line, kind}` — include `qualified_name` for disambiguation
- [x] 2.5 Wire `_execute_graph_signal()` into `execute()` — call BETWEEN AST and LSP signals (PRIME→AST→Graph→LSP), populate `graph_data` and `metadata.graph_signal`
- [x] 2.6 Add `graph_signal` state tracking to telemetry event in `execute()` — states: "used", "unavailable", "timeout", "stale", "no_predicate", "target_not_found"
- [x] 2.7 Make all Phase 2 tests pass

## Phase 3: Server Wiring + Integration

- [x] 3.2 Integration test: Oracle with real GraphService + in-memory SQLite (3 nodes, 2 edges) → caller query returns `graph_data` populated with correct callers
- [x] 3.3 Integration test: Oracle without `graph_service` → `graph_data=None`, zero regression on existing PRIME+AST+LSP signals
- [x] 3.4 Kill criteria test: mock GraphService returning <3/5 useful callers → verify Oracle still functions with `fidelity="degraded"`

## Phase 4: Verification

- [x] 4.1 Run full test suite — zero regressions, verify existing test files pass
- [x] 4.2 Automated benchmark: 100 iterations of 5 caller queries, assert p95 <65ms
- [x] 4.3 Verify no-predicate queries never touch graph — use mock `assert_not_called()` on GraphService methods for 10 non-relational queries
