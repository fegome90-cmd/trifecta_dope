# Linear Viewer Mode (Fase 1)

## Scope

Viewer mode is outbound-only from Trifecta to Linear.

- No inbound sync from Linear to YAML.
- No WO state transitions from Linear to Trifecta.
- Drift `FATAL` is never auto-corrected.

## SSOT Rules

1. `_ctx/jobs/*/*.yaml` remains the operational SSOT.
2. Critical WO transitions are allowed only via `ctx_wo_take.py` and `ctx_wo_finish.py`.
3. Linear is a projection target, not a source of truth in this phase.

## Commands

- `trifecta linear bootstrap --root <repo>`
- `trifecta linear push WO-XXXX --root <repo>`
- `trifecta linear sync --root <repo>`
- `trifecta linear reconcile --root <repo> --dry-run`

## Exit Codes

### reconcile

- `0` ok
- `2` warn
- `3` fatal
- `1` technical

### sync

- `0` ok
- `3` fatal present
- `1` technical

### bootstrap

- `0` ok
- `1` technical

## Environment

- `LINEAR_MCP_CMD` (required): MCP stdio command
- `LINEAR_MCP_TIMEOUT_MS` (optional, default `5000`)
- `LINEAR_MCP_DEBUG=1` (optional): raw frame logging

## MCP Protocol

- Transport: JSON-RPC 2.0 over NDJSON (one JSON per line)
- Single in-flight request (no pipelining)

## Fake MCP test harness

Integration tests use:

```bash
LINEAR_MCP_CMD="python -m tests.fixtures.linear_mcp_fake"
```

Available fake toggles:

- `LINEAR_FAKE_MISSING_CAPABILITY`
- `LINEAR_FAKE_RATE_LIMIT_TOOL`
- `LINEAR_FAKE_RATE_LIMIT_COUNT`
- `LINEAR_FAKE_WORKFLOW_VARIANT`
- `LINEAR_FAKE_TEAM_ID`

## status_map cache

Runtime cache path: `_ctx/linear_sync/status_map.json`

Required fields:

- `team_id`
- `policy_version`
- `generated_at`
- `status_map`
- `linear_state_id_to_name`

Cache invalidates if `team_id` or `policy_version` mismatch, or required keys are missing.

## Reproducible Evidence Bundle

Run exactly:

```bash
# Unit
uv run pytest tests/unit/test_linear_policy_validation.py \
  tests/unit/test_linear_fingerprint.py \
  tests/unit/test_linear_drift_classification.py \
  tests/unit/test_linear_journal_state_rebuild.py -q

# Integration-ish (fake MCP)
export LINEAR_MCP_CMD="python -m tests.fixtures.linear_mcp_fake"
uv run pytest tests/integration/test_linear_bootstrap_capabilities.py \
  tests/integration/test_linear_push_idempotent.py \
  tests/integration/test_linear_sync_skips_fatal.py \
  tests/integration/test_linear_exit_codes.py -q
```

CLI happy path example:

```bash
export LINEAR_MCP_CMD="python -m tests.fixtures.linear_mcp_fake"
uv run trifecta linear bootstrap
uv run trifecta linear reconcile
```
