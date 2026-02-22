---
name: wo/status
description: Read-only diagnostics for WO system health checks
---

# WO Status - System Diagnostics

## Overview

Quick health check commands for the WO system. This skill is **read-only** - it never modifies state.

**Note**: This skill has no corresponding `/wo-status` command. It's invoked implicitly by `/wo-start`, `/wo-repair`, and `/wo-finish`.

## When to Use

- Start of day / session
- Before taking a new WO
- Debugging state issues
- CI/CD pipeline checks
- Weekly maintenance

## Quick Commands

| Command | Output |
|---------|--------|
| `uv run python scripts/ctx_wo_take.py --status` | System health overview |
| `uv run python scripts/ctx_wo_take.py --list` | Pending WOs |
| `uv run python scripts/ctx_backlog_validate.py --strict` | Validate all WOs |
| `git worktree list` | Active worktrees |
| `git worktree prune` | Clean stale references |

## Red Flags (Automatic Detection)

**If ANY of these are detected, action is required:**

| Red Flag | Detection | Action |
|----------|-----------|--------|
| **Running > 2** | `ls _ctx/jobs/running/*.yaml \| wc -l` | Investigate abandoned work |
| **Locks without YAML** | Lock file exists, no corresponding YAML | Run `/wo-repair --all` |
| **Worktrees huérfanos** | Worktree exists, WO not in running | Run `/wo-repair --all` |
| **WOs running sin worktree** | YAML in running, no worktree | Run `/wo-repair --all` |
| **Failed > 1** | `ls _ctx/jobs/failed/*.yaml \| wc -l` | Review and address |

**Automatic recommendation**: If any red flag is detected, output suggests `/wo-repair --all`.

## Status Output Interpretation

### Pending WOs
```
Pending WOs:
  WO-0055: Fix hook bypass (P1)
  WO-0056: Add telemetry (P2)
```
**Action**: Review priorities, take highest priority first.

### Running WOs
```
Running WOs:
  WO-0046: ctx sync fix (owner: felipe, started: 2026-02-15)
    Lock age: 2h 34m
```
**Action**: If lock age > TTL, investigate. May need `/wo-repair`.

### Lock Warnings
```
⚠️ Stale lock detected: WO-0048 (age: 26h, TTL: 24h)
```
**Action**: Run `/wo-repair WO-0048` to clean up.

### Worktree Status
```
Worktrees:
  /Users/.../.worktrees/WO-0046 (branch: feat/wo-WO-0046)
  /Users/.../.worktrees/WO-0048 (ORPHANED - no running WO)
```
**Action**: Orphaned worktrees need cleanup via `/wo-repair --all`.

## Diagnostic Checklist

```bash
# Full status snapshot
echo "=== WO STATUS SNAPSHOT ==="
echo ""
echo "--- Pending ---"
ls _ctx/jobs/pending/*.yaml 2>/dev/null | wc -l
echo ""
echo "--- Running ---"
ls _ctx/jobs/running/*.yaml 2>/dev/null
echo ""
echo "--- Locks ---"
ls _ctx/jobs/running/*.lock 2>/dev/null
echo ""
echo "--- Done (last 7 days) ---"
find _ctx/jobs/done -name "*.yaml" -mtime -7 2>/dev/null | wc -l
echo ""
echo "--- Worktrees ---"
git worktree list
```

## State Counts

Expected healthy state:
- **Pending**: 1-20 (work queued)
- **Running**: 0-2 (active work)
- **Done**: Growing (completed work)
- **Failed**: 0-1 (needs attention)

**Warning signs**:
- Running > 2: May indicate abandoned work
- Failed > 1: Needs repair
- Locks without running WOs: Stale locks

## Resources

- `scripts/ctx_wo_take.py` - Source of `--status` and `--list`
- `scripts/ctx_backlog_validate.py` - Full validation
- `scripts/ctx_wo_dependencies.py` - Dependency analysis
- `docs/backlog/OPERATIONS.md` - Daily workflow

## Quick Reference

```bash
# One-liner status
uv run python scripts/ctx_wo_take.py --status

# List pending with priorities
uv run python scripts/ctx_wo_take.py --list | grep -E "P0|P1"

# Check for stale locks (older than TTL)
find _ctx/jobs/running -name "*.lock" -mtime +1

# Validate all WOs
uv run python scripts/ctx_backlog_validate.py --strict

# Red flag check
ls _ctx/jobs/running/*.yaml 2>/dev/null | wc -l  # Should be <= 2
```

## Required Output

After status check:

```
STATE COUNTS: X pending, Y running, Z done, W failed
RED FLAGS: <list or "none detected">
ACTIVE_WO=<current running WO or none>
SYSTEM_HEALTH=<OK|WARN|ERROR>
RECOMMENDED_ACTION: <"proceed" | "/wo-repair --all" | specific action>
```
