# Design: WO-0043 — GraphStore como Señal Derivada del Oracle

## Technical Approach

Wire the existing `GraphService` (already instantiated in `TrifectaF1Server`) into `SearchOracleUseCase` as an optional dependency. Add a pure-function predicate detector in domain. The graph signal activates only for queries matching relational patterns, with strict latency budgets and staleness gates. No new dependencies. No schema changes to GraphStore.

## Architecture Decisions

| Decision | Choice | Alternative | Rationale |
|---|---|---|---|
| Predicate detection | Pure function in domain | Regex in application layer | Domain owns query classification. Testable without IO. |
| Graph wiring | Constructor injection `Optional[GraphService]` | Lazy import / global | Follows existing DI pattern (ast_builder, lsp_client). |
| Result shape | `graph_data` field on `OracleResult` | Separate response object | Single response contract. No breaking change (field is Optional). |
| Latency enforcement | Per-operation timeouts with `time.time()` | asyncio deadline | Oracle is sync. No async needed. |
| Staleness check | `GraphStore.probe_status()` → compare `indexed_at` | File mtime on .db | `probe_status` already exists and returns `last_indexed_at`. |

## Data Flow

```
Query → OracleUseCase.execute()
            │
            ├─ (1) PRIME Search (authority, always)     → prime_chunks
            ├─ (2) AST Resolution (from top hit)        → ast_symbols
            ├─ (3) LSP Signal (gated)                   → lsp_data
            │
            └─ (4) Graph Signal (NEW, conditional)
                 │
                 ├─ detect_relational_predicate(query)
                 │   NO → skip, graph_signal="no_predicate"
                 │   YES ↓
                 ├─ graph_service available?
                 │   NO → skip, graph_signal="unavailable"
                 │   YES ↓
                 ├─ staleness check (indexed_at < 7 days)
                 │   STALE → skip, graph_signal="stale"
                 │   FRESH ↓
                 ├─ resolve target (< 10ms budget)
                 │   TIMEOUT → skip, graph_signal="timeout"
                 │   NOT FOUND → graph_signal="target_not_found"
                 │   FOUND ↓
                 └─ callers/callees traversal (< 5ms budget)
                     TIMEOUT → skip, graph_signal="timeout"
                     SUCCESS → graph_data populated
                                graph_signal="used"
```

## File Changes

| File | Action | Description |
|---|---|---|
| `src/domain/context_models.py` | Modify | Add `graph_data: Optional[Dict]` field to `OracleResult` |
| `src/domain/query_classifier.py` | Create | Pure function `classify_query(query) → QueryClass` with `RelationalPredicate` dataclass |
| `src/application/oracle_use_case.py` | Modify | Accept `graph_service: Optional[GraphService]`. Add `_execute_graph_signal()` method with latency/staleness gates. |
| `src/interfaces/mcp/server.py` | Modify | Pass `graph_service=self.graph_service` to `SearchOracleUseCase` constructor (line 62) |

## Interfaces / Contracts

```python
# src/domain/query_classifier.py (NEW)

class RelationalPredicate:
    """Detected relational intent from a query."""
    relation: Literal["callers", "callees"]
    target: str

class QueryClass:
    predicate: Optional[RelationalPredicate]

def classify_query(query: str) -> QueryClass:
    """Pure function. No IO. Tests: 10 pattern cases."""
```

```python
# src/domain/context_models.py (MODIFIED — OracleResult)

class OracleResult(BaseModel):
    fidelity: Literal["full", "degraded", "fallback"]
    lsp_data: Optional[Dict[str, Any]] = None
    ast_symbols: List[str] = Field(default_factory=list)
    prime_chunks: List[SearchHit] = Field(default_factory=list)
    graph_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Derived relational signal from GraphStore (callers/callees)"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

```python
# src/application/oracle_use_case.py (MODIFIED — constructor)

class SearchOracleUseCase:
    def __init__(
        self,
        ast_builder: SkeletonMapBuilder,
        lsp_client: Optional[Any] = None,
        graph_service: Optional["GraphService"] = None,  # NEW
        telemetry: Optional[Any] = None,
    ):
        self.graph_service = graph_service
        # ... existing code unchanged
```

## Testing Strategy

| Layer | What | Approach |
|---|---|---|
| Unit | `classify_query()` predicate detection | 10 parametrized cases: callers/callees/no-predicate/borderline |
| Unit | `_execute_graph_signal()` timeout/staleness | Mock GraphService with time.sleep to exceed budget |
| Unit | `_execute_graph_signal()` target not found | Mock raises `GraphTargetNotFoundError` |
| Integration | Oracle with graph_service wired | Real GraphStore (in-memory :memory:) + real predicate detection |
| Integration | Oracle without graph_service | Verify graph_data=None, no regression on existing signals |
| E2E | CLI `ctx oracle` with indexed segment | Verify graph_data populated for relational queries |

## Migration / Rollout

No migration required. `graph_service` defaults to `None` — existing behavior preserved. Wiring happens at server construction time (single line change).

## Resolved Questions

- **Spanish+English predicates**: `classify_query()` supports both. Patterns: `"who calls X"`, `"quién llama a X"`, `"callers of X"`, `"quienes llaman a X"`, `"what does X call"`, `"qué llama X"`, `"callees of X"`.
- **Node representation**: Trimmed. `graph_data.nodes` returns `[{"symbol_name": str, "file_rel": str, "line": int, "kind": str}]`. Excludes `id`, `segment_id`, `qualified_name`, `metadata_json` — noisy for consumers.
