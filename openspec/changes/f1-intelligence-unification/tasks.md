# Tasks: F1 Intelligence Unification & Authority Audit (PCC-First)

## Phase 1: Foundation & Shared Services

- [x] 1.1 Create `src/domain/sanitizer.py` with centralized PII and path redaction logic.
- [x] 1.2 Refactor `src/infrastructure/telemetry.py` to use `src/domain/sanitizer.py`.
- [x] 1.3 Add `OracleResult` dataclass to `src/domain/context_models.py`.
- [x] 1.4 Implement hit/miss counters in `src/interfaces/mcp/server.py` state.

## Phase 2: Core Intelligence (Oracle)

- [x] 2.1 Create `src/application/oracle_use_case.py` implementing signal fusion (LSP + AST + PRIME).
- [x] 2.2 Implement LSP state-gating logic: fallback to AST if not `READY`.
- [x] 2.3 Add `ctx_oracle` tool handler to `src/interfaces/mcp/server.py`.
- [x] 2.4 Implement `AutonomousWeightCalibrationUseCase` to adjust weights based on PCC metrics.

## Phase 3: Integration (CLI Hybrid Dispatch)

- [x] 3.1 Create `src/infrastructure/cli_hybrid.py` with Unix Socket client logic.
- [x] 3.2 Update `src/infrastructure/cli.py` to use `HybridDispatcher` for `ctx search` and `ctx get`.
- [x] 3.3 Implement socket-liveness check in CLI to ensure graceful fallback to local UseCases.

## Phase 4: Governance & Documentation

- [x] 4.1 Update `.gemini/skills/trifecta_dope/SKILL.md` with "MCP Power Tools" prioritization.
- [x] 4.2 Add usage examples for `ctx_oracle` and `ctx_calibrate` to `docs/CLI_WORKFLOW.md`.
- [x] 4.3 Update `README.md` to reflect unified intelligence capabilities.

## Phase 5: Verification & Certification

- [x] 5.1 Unit: Verify `sanitizer.py` against complex absolute path patterns.
- [x] 5.2 Integration: Verify `OracleUseCase` fallback behavior with mocked LSP states.
- [x] 5.3 E2E: Run daemon, execute `trifecta ctx oracle`, and confirm Socket routing.
- [x] 5.4 Performance: Measure latency difference (~50ms hybrid vs ~800ms local).
