# Review Inventory: daemon-runtime mergefix bundle

## Source surface
- Worktree: `<repo>/.worktrees/skill-hub-authority-anchor-mergefix`
- Branch: `codex/skill-hub-authority-anchor-mergefix`

## Files rescued into this review

### `src/application/use_cases.py`
- Adds fallback logic for generic builds when canonical tracked state is missing.
- Uses `trifecta_config.json` or `get_segment_slug()` before failing.
- This is not related to skill-hub cards behavior.

### `src/infrastructure/daemon/lsp_handler.py`
- Adds `textDocument/didOpen` handling.
- Adds explicit FAILED-state degraded response handling.
- Skips `.md` didOpen with a note.

### `src/platform/daemon_manager.py`
- Replaces socket-bind singleton locking with lock-file creation semantics.
- Adds stale lock cleanup path and explicit file descriptor release.

### `tests/integration/daemon/test_daemon_manager.py`
- Deleted from the mergefix worktree.
- Appears to be paired with the new integration test file below.

### `tests/integration/daemon/test_daemon_manager_integration.py`
- Untracked replacement/addition carrying the deleted daemon manager lifecycle/security tests.
- Indicates the daemon test suite was being reshaped, not merely deleted.

## Review recommendation
- Treat this as a separate daemon/runtime review campaign.
- Do not discard it together with skill-hub cleanup.
- Do not apply it blindly either; it needs its own owner, test plan, and scope decision.

## Preserved evidence
- `bundle-tracked.patch` captures the tracked diff for the rescued daemon/runtime files.
- `bundle-untracked.patch` captures the untracked replacement test file from the mergefix worktree.

## Review findings to verify before any future apply
- Narrow the `resolve_segment_state()` fallback so only the true “not materialized” path falls back to config/slug derivation.
- Ensure daemon singleton stale-lock recovery does not unlink a live owner's lock during startup.
- Ensure `didOpen` send paths degrade cleanly instead of leaking transport exceptions.
