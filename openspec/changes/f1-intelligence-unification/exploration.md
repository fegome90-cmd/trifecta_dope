## Exploration: F1 Intelligence Unification & Authority Audit

### Current State
Trifecta has powerful but siloed intelligence signals:
1. **PRIME**: Deterministic authority index (Keywords/Weights).
2. **AST (M1)**: Structural DNA extraction.
3. **LSP (Pyright)**: Compiler-grade definitions and references.
The system currently requires multiple tool calls to merge these signals, increasing agent cognitive load and latency. The CLI operates independently of the running Daemon, leading to redundant indexing.

### Authority Flow Audit (PCC vs RAG)
- **RAG Check**: No embeddings, no vector databases, no semantic similarity search implemented.
- **PCC Verification**: The "Oracle" acts as a **Macro-Tool**. It uses the query to hit the **PRIME Index** (Authority), then uses the resulting paths to trigger **AST/LSP** (Technical Fidelity).
- **Verdict**: The architecture remains pure PCC. The "Oracle" is a fusion of authority signals, not a semantic guesser.

### Affected Areas
- `src/application/oracle_use_case.py` — Orchestrates signal fusion.
- `src/infrastructure/cli.py` — Implements Hybrid Dispatcher (CLI -> Daemon).
- `src/interfaces/mcp/server.py` — Enriched health and new tool handlers.
- `src/domain/sanitizer.py` — Centralized PII policy.

### Approaches
1. **Unified Oracle (F1 Fusion)** — Merge LSP+AST+PRIME into one response.
   - Pros: Single tool call for agents, complete symbol profile, reduced latency.
   - Cons: Potential response bloat (mitigated by 1500 token budget).
   - Effort: Medium.

2. **Hybrid Dispatcher (Socket-First)** — CLI talks to active Daemon.
   - Pros: Near-zero CLI latency, shared memory cache.
   - Cons: Requires robust socket management and fallback.
   - Effort: Medium.

### Recommendation
Proceed with **Option 1 and 2**. The combination transforms Trifecta into a high-performance intelligence engine while maintaining PCC sovereignty.

### Risks
- **Signal Pollution**: LSP might return too much data. *Mitigation: Strict extraction to definitions/hovers only.*
- **Socket Collisions**: Multiple daemons or stale sockets. *Mitigation: Path-based socket hashing.*

### Ready for Proposal
Yes. The technical foundations are implemented in the worktree but require a "F1 Tuning" pass to fix collect errors and telemetry signatures.
