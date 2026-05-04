# Design: F1 Intelligence Unification & Authority Audit (PCC-First)

## Technical Approach
We unify intelligence signals by creating a **Signal Fusion Layer** (`SearchOracleUseCase`) that orchestrates multiple authority sources. The CLI is decoupled from expensive local indexing by the **Hybrid Dispatcher**, which routes calls through a warm, long-running **F1 Daemon** process via Unix Sockets. All PII safety is consolidated into a pure **Domain Sanitizer**.

> **⚠️ Baseline Status Update (Post-Audit)**:
> - The F1 Oracle currently operates exclusively in **Fallback Mode** (Structural AST + PRIME).
> - The LSP client is intentionally omitted from the `SearchOracleUseCase` constructor in `server.py`.
> - "Signal Fusion" remains a verified architectural capability, but semantic fidelity (LSP) is currently disabled to ensure maximum daemon stability.
> - The `ContextService` utilizes a strict, `mtime`-invalidated RAM cache (`_pack_cache`) to avoid synchronus disk I/O, consistently achieving sub-50ms latency.
> - **WO-0043 Redefined**: The transition to SQLite (`search.db`) is no longer intended as a replacement for the `context_pack.json` in-memory SSOT. Instead, WO-0043 is redefined to focus on providing a Persistence Graph / Vector Store for complex querying, while JSON + RAM remains the authority path for the daemon.

## Architecture Decisions

### Decision: Signal Fusion Orchestration
**Choice**: Sequential Authority-First (PRIME -> AST -> LSP).
**Rationale**: PCC requires documentation context (PRIME) as the primary anchor. Technical signals (AST/LSP) are enrichments.

### Decision: CLI-Daemon Communication
**Choice**: Unix Sockets with line-delimited JSON.
**Rationale**: Unix Sockets are the fastest IPC for local developer environments, allowing the CLI to achieve ~50ms latencies.

## Data Flow

    [CLI/Agent] --- (Query) --- [F1 Daemon]
                                   |
           (1) PRIME Index Search (Authority)
           (2) AST Symbol Extraction (Structure)
           (3) LSP Definition Lookup (Fidelity)
                                   |
    [CLI/Agent] <--- (Fused Authority Result) ---

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/domain/sanitizer.py` | Create | Centralized redaction policy service. |
| `src/application/oracle_use_case.py` | Create | Signal fusion orchestrator. |
| `src/infrastructure/cli_hybrid.py` | Create | Unix socket client for hybrid dispatch. |
| `src/interfaces/mcp/server.py` | Modify | Enriched health metrics and oracle tool. |
| `src/infrastructure/cli.py` | Modify | Hybrid routing and `ctx oracle` command. |

## Interfaces / Contracts

```python
@dataclass
class OracleResult:
    fidelity: Literal["full", "degraded", "fallback"]
    lsp_data: Optional[Dict]
    ast_symbols: List[str]
    prime_chunks: List[SearchHit]
    metadata: Dict[str, Any]
```

## Testing Strategy
- **Unit**: `Sanitizer` against Law IV path patterns.
- **Integration**: `OracleUseCase` with mocked LSP states.
- **E2E**: CLI command verification with and without active daemon.

## Open Questions
- **Multi-tenant impact**: Memory footprint of holding multiple `context_pack.json` caches simultaneously across different segments.
