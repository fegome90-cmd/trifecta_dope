# Design: daemon-runtime mergefix review

## Technical approach
Treat the old mergefix worktree as a temporary evidence source and extract only the review metadata into this change.

1. Record the exact files that belong to the daemon/runtime review bundle.
2. Record the current diff intent visible in those files.
3. Leave implementation and acceptance to a separate future owner or follow-up change.

## Bundle under review
- `src/application/use_cases.py`
- `src/infrastructure/daemon/lsp_handler.py`
- `src/platform/daemon_manager.py`
- `tests/integration/daemon/test_daemon_manager.py`
- `tests/integration/daemon/test_daemon_manager_integration.py`

## Why this shape
This avoids polluting the skill-hub rebuild with daemon/runtime scope while still preserving a reviewable trail for the leftover code.
