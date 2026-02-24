# Scoped Verify Contract

**Document**: docs/backlog/SCOPED_VERIFY.md
**Created**: 2026-02-23
**Status**: ACTIVE

---

## Rationale

**Incident**: WO-0015 (2026-02-23)

During WO-0015, a split-brain state occurred:
- WO existed in `failed/` in main repo
- WO existed in `running/` in worktree with lock

**Root Cause**: Running verification from wrong location caused state divergence.

**Lesson**: Verification must be scoped to specific WO changes, not the entire codebase.

---

## Contract

### What ctx_verify_wo.py RUNS

| Runs | Description |
|------|-------------|
| `verify.commands` | Commands defined in WO YAML under `verify.commands` |
| Exit 0 | All commands passed |
| Exit 1 | One or more commands failed |

### What ctx_verify_wo.py DOES NOT RUN

| Does NOT Run | Belongs In |
|--------------|------------|
| Unit tests (`pytest tests/unit`) | CI: `make test-unit` |
| Integration tests (`pytest tests/integration`) | CI: `make test-integration` |
| Acceptance tests (`pytest tests/acceptance`) | CI: `make test-acceptance` |
| Full suite (`make gate-all`) | CI: PR merge |

### HARD RULES

1. **NO fallback PASS**: If WO has no `verify.commands` → FAIL (exit 2)
2. **Split-brain detection**: If WO found in >1 state → FAIL (exit 2)
3. **All commands must pass**: Single command failure → FAIL (exit 1)

---

## Integration

| Stage | Gate | Command | Runtime |
|-------|------|---------|---------|
| /wo-finish | Gate WO | `ctx_verify_wo.py WO-XXXX` | Fast (<30s) |
| CI PR | Gate Release | `make gate-all` | Slow (5-10 min) |
| CI Weekly | Gate Integrity | `make wo-integrity` | Fast (<10s) |

### Why Separate?

| Aspect | Gate WO | Gate Release |
|--------|---------|--------------|
| Speed | Fast (<30s) | Slow (5-10 min) |
| Scope | Specific WO changes | Entire codebase |
| When | During wo-finish | CI/PR |
| Purpose | Validate WO delivery | Prevent regressions |

---

## Exit Codes

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| 0 | All commands PASS | Continue with finish |
| 1 | Command FAIL | Fix code, re-run finish |
| 2 | Usage error (missing WO, split-brain, no commands) | Diagnose, fix WO or run /wo-repair |

---

## Failure Modes

| Mode | Detection | Recovery |
|------|-----------|----------|
| WO commands fail | `ctx_verify_wo.py` exit 1 | Fix WO code, re-run finish |
| No verify.commands | `ctx_verify_wo.py` exit 2 | Add commands to WO YAML |
| Split-brain | `ctx_verify_wo.py` exit 2 | Run `/wo-repair` |
| Full suite fails | CI fails | Fix regressions before merge |
| Integrity fails | `make wo-integrity` exit 1 | Run `/wo-repair` |

---

## Example WO YAML

```yaml
version: 1
id: WO-0055
epic_id: E-001
title: Fix hook bypass telemetry
priority: P1
status: running
scope:
  allow: ["src/infrastructure/telemetry.py", "scripts/hooks/"]
  deny: ["_ctx/"]
verify:
  commands:
    - "uv run pytest tests/unit/test_telemetry.py -v"
    - "uv run ruff check src/infrastructure/telemetry.py"
```

---

## Reference

- **Implementation**: `scripts/ctx_verify_wo.py`
- **Tests**: `tests/unit/test_ctx_verify_wo.py`
- **Integration Tests**: `tests/integration/test_wo_split_brain.py`
- **Commands**: `.claude/commands/wo-finish.md`
- **ADR**: `docs/adr/ADR-002-wo-governance.md`

---

## History

| Date | Change |
|------|--------|
| 2026-02-23 | Created after WO-0015 incident |
