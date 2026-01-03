# Telemetry Environment Contracts

This document defines the behavior of the Telemetry system regarding environment variables and worktree isolation.

## Precedence Rules

1.  **`TRIFECTA_NO_TELEMETRY=1` (Highest Priority)**
    - Mandatory NO-OP mode.
    - Behavior: `Telemetry` instance sets `level = "off"`.
    - No directories are created.
    - No file writes are performed.
    - Overrides all other settings.

2.  **`level="off"` (Argument Priority)**
    - Explicitly disables telemetry for a specific instance.
    - Behavior: Similar to `TRIFECTA_NO_TELEMETRY`.

3.  **`TRIFECTA_TELEMETRY_DIR=<path>` (Redirection Priority)**
    - Redirects all telemetry writes to a custom path.
    - Behavior: Used by `test-gate` to isolate test side-effects.
    - Writes go to `<path>`, and the repository's `_ctx/telemetry` is **NEVER** touched.

4.  **`Default`**
    - Telemetry is written to the segment's `_ctx/telemetry` directory.

## Implementation Details

- **Atomic Writes**: All telemetry writes are non-destructive (append for `events.jsonl`, overwrite for `last_run.json`).
- **Isolation**: During `pre-commit`, either NO-OP or Redirection MUST be active to ensure a clean worktree.
- **Cleanup**: Redirected telemetry in `/tmp` should be cleaned up by the triggering script (e.g., using `trap EXIT`).
