# Proposal: RC-0.1 Installation Certification

## Intent
Transform Trifecta from an internally verified set of scripts into a certified installable product. This change establishes the "Clean Machine" certification harness and hardens the MCP server to handle build latency gracefully (backpressure management), ensuring the system is ready for public release.

## Scope

### In Scope
- **Clean Machine Harness**: `pytest` fixture to simulate a fresh macOS environment (isolated PATH/HOME).
- **16-Point Certification Checklist**: Automated execution of the release readiness matrix.
- **MCP Backpressure Management**: Configurable timeouts for `ensure_context_ready` with structured error reporting.
- **Improved Health Reporting**: Transition states (SYNCING) and concrete manual sync recommendations in error payloads.

### Out of Scope
- Production distribution to PyPI (this phase covers certification only).
- Non-macOS environment certification (Windows/Linux).

## Capabilities

### New Capabilities
- `certification-harness`: Automated infrastructure to verify installation from a built package in an isolated environment.
- `mcp-backpressure-mgmt`: Robust timeout handling and async-aware state management for background build operations.

### Modified Capabilities
- `mcp-core-engine`: Enhanced `ctx_health` and error contracts to support the `SYNCING` state and timeout-based failures.

## Approach
Leverage `pytest` with environment monkeypatching to create a "sandbox" for installation testing. The MCP server will be updated to use a threaded execution model for the `ensure_context_ready` phase, allowing the server to respond with a `LSP_TIMEOUT` error if a build exceeds the configured threshold, rather than blocking the agent indefinitely.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `tests/certification/` | New | New test suite for release candidate validation. |
| `src/interfaces/mcp/server.py` | Modified | Implementation of timeout logic and transition states. |
| `src/interfaces/mcp/handlers.py` | Modified | Updated error payloads with manual sync instructions. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Harness false positives | Medium | Use explicit bin path verification and checksums of installed files. |
| Timeout race conditions | Low | Use thread-safe status flags and standard filesystem locking. |

## Rollback Plan
Delete `tests/certification/` and revert `server.py` to the previous synchronous pre-flight check.

## Success Criteria
- [ ] Passing 16-point certification suite in an isolated environment.
- [ ] `uvx trifecta-mcp` returns a structured error within 30s if a massive build is triggered.
- [ ] No manual installation steps required to reach `READY` state on a clean machine.
