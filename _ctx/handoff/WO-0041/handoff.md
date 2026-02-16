# WO-0041 Handoff

## Summary
Implemented READY invariants contract for LSP client to ensure READY state truly means "operational and capable of serving requests".

## Changes
- Added invariant checking before READY transition (process_alive, workspace_root, health)
- Track failed invariants in `_failed_invariants` list
- Added `health_check()` method with configurable timeout
- Added `failed_invariants` to `lsp.state_change` telemetry event
- Added tests for invariant checking
- Added `LSP_READY_INVARIANTS.md` contract documentation

## Files Changed
- src/infrastructure/lsp_client.py
- tests/integration/test_ready_semantics_documented_and_enforced.py  
- docs/contracts/LSP_READY_INVARIANTS.md

## Tests
- All LSP-related tests pass (17 tests)
- 3 new tests for invariant checking added
