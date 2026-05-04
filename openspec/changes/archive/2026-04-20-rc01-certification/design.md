# Design: RC-0.1 Installation Certification

## Technical Approach
This phase focuses on certifying Trifecta v2.0 for public release by building a rigorous, isolated test harness and hardening the MCP server's lifecycle management. We will implement a "Clean Machine" simulation using `pytest` to verify installation and environment wiring. Simultaneously, the MCP server will be upgraded with a threaded execution model for background builds, ensuring that agents receive timely feedback (timeouts/SYNCING state) instead of hanging.

## Architecture Decisions

### Decision: Threaded Background Sync
**Choice**: Use `threading.Thread` to execute the `ensure_context_ready` build logic.
**Alternatives considered**: `asyncio`, `multiprocessing`.
**Rationale**: Trifecta UseCases are currently synchronous. Threading allows us to offload the build without blocking the main RPC loop while sharing the same memory space for state tracking (`self.state`).

### Decision: Environment Isolation via Monkeypatch
**Choice**: Use `pytest`'s `monkeypatch` to isolate `HOME`, `PATH`, and `PYTHONPATH`.
**Alternatives considered**: Docker containers, virtual machines.
**Rationale**: Environment isolation is sufficient for certifying path wiring and bootstrap logic. It provides faster feedback loops and requires no external dependencies like Docker during the certification run.

## Data Flow
The MCP server manages state transitions during tool calls.

    [Agent Call] ──→ [MCP Server] ──→ [Check State]
                          │               │
                          │        ┌──────┴──────┐
                          │        ▼             ▼
                          │    [READY]       [UNINITIALIZED/STALE]
                          │    (Execute)     (Trigger Threaded Sync)
                          │                      │
                          │               ┌──────┴──────┐
                          │               ▼             ▼
                          │          [Success]      [Timeout/Fail]
                          │          (READY)        (FAILED + Error)
                          │
    [Health Tool] ←───────┴──────────────────────┘

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `tests/certification/conftest.py` | Create | Pytest fixtures for environment isolation (`clean_machine`). |
| `tests/certification/test_certification_suite.py` | Create | Implementation of the 16-point certification checklist. |
| `src/interfaces/mcp/server.py` | Modify | Implement threaded `ensure_context_ready` and timeout handling. |
| `src/interfaces/mcp/handlers.py` | Modify | Update error responses with manual sync recommendations. |

## Interfaces / Contracts

### Enhanced `ctx_health` Payload
```json
{
  "state": "SYNCING",
  "sync_info": {
    "elapsed_ms": 1200,
    "timeout_limit_ms": 30000,
    "lock_owner": "pid_1234"
  },
  "recommendation": "If syncing takes too long, run 'trifecta sync' manually."
}
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Certification | Installation | Verify `pip install .` and `bootstrap` on a clean `HOME`. |
| Integration | Timeout Logic | Simulate a slow build and verify `LSP_TIMEOUT` error. |
| Integration | Concurrency | Send two tool calls simultaneously and verify only one build triggers. |

## Migration / Rollout
No migration required. This is a certification and hardening phase.

## Open Questions
- [ ] Should `BUILD_TIMEOUT` be a CLI flag or an environment variable? (Decision: CLI flag with env var fallback).
