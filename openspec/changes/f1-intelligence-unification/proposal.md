# Proposal: F1 Intelligence Unification & Authority Audit (PCC-First)

## Intent
Consolidate the disparate high-performance signals (LSP, AST, PRIME) into a unified "Context Oracle" macro-tool. This move targets near-zero latency for context retrieval while strictly maintaining the **PCC (Programming Context Calling)** philosophy—fusing authoritative signals without resorting to semantic guessing or RAG architectures.

## Scope

### In Scope
- **Signal Fusion Oracle**: A high-level UseCase that merges results from PRIME (Authority), AST (Structure), and LSP (Fidelity).
- **Hybrid Dispatcher**: Intelligent CLI routing via Unix Sockets to the active F1 Daemon.
- **Enriched Health Reporting**: Real-time hit rate, uptime, and staleness metrics in `ctx_health`.
- **Centralized Sanitizer**: Unified PII and path redaction policy in the domain layer (Law IV).

### Out of Scope
- Semantic Search (Embeddings/Vector DBs).
- Multi-repo orchestration.

## Capabilities

### New Capabilities
- `unified-intelligence-oracle`: Single step retrieval of definition + structure + documentation.
- `hybrid-cli-dispatch`: Zero-latency CLI commands leveraging shared daemon memory.
- `autonomous-pii-sanitization`: Domain-enforced Zero Trust Path policy.

### Modified Capabilities
- `mcp-core-engine`: Updated to support multi-signal tool handlers and enriched telemetry.

## Approach
Implement the `SearchOracleUseCase` as a signal fusion layer. Use Unix Sockets for the `HybridDispatcher` to bypass Python's startup overhead during CLI calls. Centralize all sanitization in `src/domain/sanitizer.py`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/domain/sanitizer.py` | New | Centralized PII/Path redaction service. |
| `src/application/oracle_use_case.py` | New | Intelligence orchestrator. |
| `src/infrastructure/cli_hybrid.py` | New | Unix Socket client for CLI routing. |
| `src/infrastructure/cli.py` | Modified | Integration of Hybrid Dispatch and `ctx oracle` command. |
| `src/interfaces/mcp/server.py` | Modified | Enriched health and oracle tool handlers. |

## Risks
- **Socket Stale state**: Handled via path-based hashing and connectivity timeouts.
- **Signal Bloat**: Managed via a strict 1500 token budget per oracle call.

## Rollback Plan
Restore original `cli.py` and `server.py` from git.

## Success Criteria
- [ ] `ctx oracle` returns merged signals in <100ms (via daemon).
- [ ] Law IV compliance: No absolute paths in telemetry logs.
- [ ] CLI latency reduced by >80% when daemon is active.
