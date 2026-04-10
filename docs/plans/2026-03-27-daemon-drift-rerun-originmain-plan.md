# Daemon Drift Rerun on origin/main Plan

## Goal
Port the still-valid daemon/LSP drift decisions from the isolated batch onto current `origin/main` shape so `reviewctl` can run against a clean, current baseline.

## Scope
- `src/infrastructure/lsp_client.py`
- `src/platform/daemon_manager.py`
- `tests/unit/test_lsp_client_strict.py`
- `tests/integration/daemon/test_daemon_manager.py`

## Decisions In Scope
1. Drain LSP stderr to avoid pipe backpressure.
2. Gate debug logging behind `TRIFECTA_LSP_DEBUG`.
3. Make `LSPClient.request(timeout=None)` read `TRIFECTA_LSP_REQUEST_TIMEOUT` with safe fallback.
4. Return authoritative boolean from `_send_rpc()`.
5. Export validated `TRIFECTA_LSP_REQUEST_TIMEOUT` from `DaemonManager.start()`.

## Explicit Non-Goals
- Reintroduce deleted `src/infrastructure/daemon/lsp_handler.py` on current `origin/main` shape.
- Recreate old unit-test paths that no longer exist on current base.
- Broaden the review beyond daemon/LSP transport and timeout contract.

## Verification
```bash
uv run pytest tests/unit/test_lsp_client_strict.py tests/unit/test_lsp_ready_contract.py tests/integration/test_ready_semantics_documented_and_enforced.py tests/integration/daemon/test_daemon_manager.py -q
uv run ruff check src/infrastructure/lsp_client.py src/platform/daemon_manager.py tests/unit/test_lsp_client_strict.py tests/integration/daemon/test_daemon_manager.py
uv run mypy src/infrastructure/lsp_client.py src/platform/daemon_manager.py --no-error-summary
```

## Expected Review Outcome
A clean `reviewctl` rerun anchored to current `origin/main`, with scope limited to the ported daemon/LSP transport batch and no stale plan-source mismatch.
