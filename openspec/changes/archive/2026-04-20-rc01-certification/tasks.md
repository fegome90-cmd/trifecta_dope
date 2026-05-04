# Tasks: RC-0.1 Installation Certification

## Phase 1: Certification Harness (Infrastructure)

- [ ] 1.1 Create `tests/certification/conftest.py` with the `clean_machine` fixture.
- [ ] 1.2 Implement environment isolation (PATH/HOME monkeypatching) in the fixture.
- [ ] 1.3 Add utility to build a wheel from current source and install it in the isolated `venv`.

## Phase 2: MCP Backpressure & Hardening (Core)

- [ ] 2.1 Refactor `src/interfaces/mcp/server.py` to offload `ensure_context_ready` to a background thread.
- [ ] 2.2 Implement `BUILD_TIMEOUT` (default 30s) logic with `LSP_TIMEOUT` error reporting.
- [ ] 2.3 Update `ctx_health` to return `SYNCING` state, `elapsed_ms`, and `timeout_limit`.
- [ ] 2.4 Update tool call handlers to return structured recommendations for manual `trifecta sync` on timeout.

## Phase 3: 16-Point Certification Suite (Testing)

- [ ] 3.1 Create `tests/certification/test_certification_suite.py`.
- [ ] 3.2 Implement Installation tests: `trifecta --version`, `doctor`, and `bootstrap --dry-run`.
- [ ] 3.3 Implement Agent Wiring tests: `bootstrap --agent opencode`, idempotency, and rollback.
- [ ] 3.4 Implement MCP Robustness tests: First call silent sync, read-only repo, and large repo timeout.
- [ ] 3.5 Implement Discovery & Concurrency tests: Engram present/absent, and concurrent MCP tool calls.

## Phase 4: Final Pass & Cleanup

- [ ] 4.1 Execute full certification suite against the generated distribution package.
- [ ] 4.2 Document the certification results in `docs/REPORTS.md`.
