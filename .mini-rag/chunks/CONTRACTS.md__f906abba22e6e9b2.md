## Implementation Details

- **Atomic Writes**: All telemetry writes are non-destructive (append for `events.jsonl`, overwrite for `last_run.json`).
- **Isolation**: During `pre-commit`, either NO-OP or Redirection MUST be active to ensure a clean worktree.
- **Cleanup**: Redirected telemetry in `/tmp` should be cleaned up by the triggering script (e.g., using `trap EXIT`).
