# MCP Lifecycle Contract

## Readiness Lifecycle

The MCP server MUST manage its readiness through the following phases:

1. **Pre-flight Check**:
   - Executed during `initialize` or first tool call.
   - Detects existence of `_ctx/context_pack.json`.
   - Checks for a filesystem lock file (`_ctx/.build.lock`) to prevent concurrent builds.

2. **Ensuring Context Ready (`ensure_context_ready`)**:
   - **Mode: auto**: If pack is missing, start build. Wait up to `BUILD_TIMEOUT` (default: 30s).
   - **Mode: readonly**: If pack is missing, fail immediately.
   - **Mode: strict**: If pack is missing, build. If stale, fail.

3. **Concurrency Control**:
   - A filesystem lock MUST be used to ensure only one build/sync process happens at a time per repository.
   - If a lock exists, subsequent calls MUST wait or report `SYNCING` state.

## Health Payload
The `ctx_health` tool MUST return the following structured data:

```json
{
  "state": "READY | SYNCING | DEGRADED | FAILED",
  "sync_mode": "auto | readonly | strict",
  "pack_info": {
    "exists": true,
    "last_sync": "ISO_TIMESTAMP",
    "stale_days": 2,
    "error": null
  },
  "lock_active": false,
  "engram_discovery": {
    "detected": true,
    "method": "filesystem"
  }
}
```

## Error Handling
If a silent sync fails, the server SHALL NOT crash. It MUST transition to the `FAILED` state and return a structured error response for any subsequent tool calls explaining the failure.
