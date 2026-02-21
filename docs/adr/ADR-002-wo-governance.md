# ADR-002: Work Order Governance Architecture

## Status

**ACCEPTED** (2026-02-21)

## Context

The Trifecta Work Order (WO) system manages parallel development via git worktrees. Without governance, worktrees accumulate as "zombies" (done/failed WOs with live worktrees) and "ghosts" (worktrees without WO YAML), creating state drift and confusion.

Previous state:

- No automated detection of orphan worktrees
- Dirty worktrees required manual intervention without traceability
- No TTL for legacy exceptions (whitelist could become permanent)
- No weekly health check

## Decision

Implement a **3-layer governance architecture**:

### Layer 1: Forensic Auditor (`wo_audit.py`)

**Purpose**: Read-only detection of state violations.

**Finding Codes**:

| Code | Severity | Description |
|------|----------|-------------|
| `split_brain` | P0 | WO in multiple state directories |
| `running_without_lock` | P0 | Running WO without lock file |
| `ghost_worktree` | P0 | Worktree without WO YAML |
| `fail_but_running` | P0 | FAIL verdict but still in running/ |
| `zombie_worktree` | P1 | Worktree alive for done/failed WO |
| `lock_without_running` | P1 | Stale lock file |
| `duplicate_yaml` | P2 | Multiple YAMLs for same WO ID |

**Whitelist TTL**: Legacy duplicates have a `review_by` date. When expired, severity escalates to P1 and gate fails.

### Layer 2: Garbage Collector (`ctx_wo_gc.py`)

**Purpose**: Safe cleanup with evidence preservation.

**Policy**:

- Clean zombies/ghosts: auto-remove
- Dirty worktrees: export patch + create `decision.md`, require explicit `--force-dirty`
- Idempotent patches: `dirty.<hash>.patch` + symlink + checksum

**Dirty Exclusion Paths** (operational artifacts, not real changes):

- `_ctx/telemetry/` - Telemetry events
- `_ctx/handoff/` - Handoff artifacts
- `_ctx/logs/` - Execution logs
- `_ctx/index/` - Context index

### Layer 3: Weekly Gate (`wo_weekly_gate.sh`)

**Purpose**: CI-ready health check with fail-closed policy.

**Exit Codes**:

| Code | Meaning |
|------|---------|
| 0 | P0=0, no stale whitelist |
| 1 | P0 issues OR stale whitelist TTL |
| 2 | Script error |

**Output**:

- Exact WO IDs for ACTION_REQUIRED items
- Patch paths + SHA256 hashes
- Decision.md paths + existence status

## Decision Template (`decision.md`)

Standard format for auditability:

```markdown
| Field | Value |
|-------|-------|
| **WO ID** | WO-XXXX |
| **Date** | YYYY-MM-DD |
| **Type** | zombie/ghost |
| **Patch Hash** | `<sha256>` |
| **Status** | ACTION_REQUIRED |

## Patch Content Summary
- Content type: code/config/telemetry/other
- Files affected: ...
- Estimated risk: low/medium/high

## Decision
**Choose ONE**: [ ] APPLY | [ ] DISCARD | [ ] MANUAL REVIEW

### Justification
<!-- Why this decision? -->

### Evidence
| Item | Value |
|------|-------|
| Patch path | `dirty.<hash>.patch` |
| Patch SHA256 | `<full-hash>` |
| Command used | `uv run python scripts/ctx_wo_gc.py --export-patch` |
```

## Consequences

### Positive

1. **Traceability**: Every dirty worktree decision is documented with evidence
2. **Idempotency**: Patches are hash-named, never overwritten
3. **Fail-closed**: Gate fails on P0 or stale whitelist, preventing drift
4. **Reduced noise**: Operational artifacts excluded from dirty detection
5. **Audit-ready**: 20-second review per decision.md

### Negative

1. **Maintenance overhead**: Weekly gate requires someone to review ACTION_REQUIRED items
2. **Whitelist discipline**: TTL must be renewed with justification or migrated

### Mitigations

- Gate output includes exact IDs and paths for quick triage
- Decision template is minimal (no bureaucracy, just evidence)

## Implementation

- [`scripts/wo_audit.py`](../../scripts/wo_audit.py) - Forensic auditor
- [`scripts/ctx_wo_gc.py`](../../scripts/ctx_wo_gc.py) - Garbage collector
- [`scripts/wo_weekly_gate.sh`](../../scripts/wo_weekly_gate.sh) - Weekly gate
- [`scripts/wo_retention_gc.py`](../../scripts/wo_retention_gc.py) - Evidence retention GC
- [`_ctx/handoff/`](../../_ctx/handoff/) - Decision artifacts

## Layer 4: CI Scheduled Gate

**Purpose**: Automated weekly health check in CI with artifact preservation.

**Workflow**: [`.github/workflows/wo-weekly-gate.yml`](../../.github/workflows/wo-weekly-gate.yml)

**Schedule**: Every Monday at 06:00 UTC

**Features**:

- Runs `wo_weekly_gate.sh` with JSON output
- Uploads artifacts (audit report, GC report, stdout log)
- 90-day artifact retention
- Manual trigger support via `workflow_dispatch`
- Fail-closed: job fails if gate returns exit code 1

**Artifacts**:

| Artifact | Contents | Retention |
|----------|----------|-----------|
| `wo-weekly-gate-reports` | `wo_audit_*.json`, `wo_gc_*.json`, `wo_weekly_gate_*.json`, stdout log | 90 days |

## Layer 5: Evidence Retention

**Purpose**: Clean up old evidence files while preserving recent work and audit trail.

**Script**: [`scripts/wo_retention_gc.py`](../../scripts/wo_retention_gc.py)

**Policy**:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--days` | 90 | Minimum age for files to be eligible |
| `--dry-run` | True | Preview mode (no deletion) |
| `--apply` | False | Actually delete files |

**Eligible Files** (can be deleted):

- `dirty.*.patch` - Hashed patch files (not the symlink)
- `dirty.patch.sha256` - Checksum files

**Protected Files** (never deleted):

- `decision.md` - Audit decision record
- `handoff.md` - Handoff documentation
- `verdict.json` - WO verdict
- `diff.patch` - Original diff
- `dirty.patch` - Symlink to latest patch

**Protected Conditions** (prevent deletion):

1. **Active WO**: WO in `running/` or `pending/` state
2. **Incomplete Decision**: `decision.md` contains `ACTION_REQUIRED` or unchecked boxes

**Rationale**:

- 90-day retention balances storage efficiency with audit trail preservation
- Protecting active WOs prevents data loss during active development
- Protecting incomplete decisions ensures human review is completed
- Hashed patches allow multiple versions without conflict

**Usage**:

```bash
# Preview what would be deleted
uv run python scripts/wo_retention_gc.py --dry-run

# Apply cleanup with default 90-day retention
uv run python scripts/wo_retention_gc.py --apply

# Custom retention period
uv run python scripts/wo_retention_gc.py --apply --days 30

# Generate JSON report
uv run python scripts/wo_retention_gc.py --dry-run --json data/wo_retention_report.json
```

## References

- [WO Workflow](../backlog/WORKFLOW.md)
- [WO Operations](../backlog/OPERATIONS.md)
- [WO Troubleshooting](../backlog/TROUBLESHOOTING.md)
