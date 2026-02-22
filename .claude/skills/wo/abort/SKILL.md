---
name: wo/abort
description: Safely release a WO using official scripts only (NO manual file operations)
---

# WO Abort - Mid-Execution Release

## Overview

Safely release a WO when work must be abandoned. **Use official scripts only.**

## ⛔ PROHIBITED

**NEVER execute these commands directly**:

```bash
# ❌ FORBIDDEN - Breaks traceability
rm _ctx/jobs/running/WO-XXXX.lock

# ❌ FORBIDDEN - Creates state corruption
mv _ctx/jobs/running/WO-XXXX.yaml _ctx/jobs/pending/

# ❌ FORBIDDEN - Bypasses audit trail
rm -rf .worktrees/WO-XXXX
```

These commands break traceability and create state corruption. **ALWAYS use official scripts.**

## When to Use

- Blocked by external dependencies
- Scope creep requires new WO
- Need to switch to higher priority work
- WO cannot be completed

## Process

### Step 1: Diagnose State

```bash
# Check current state
uv run python scripts/ctx_wo_take.py --status

# Preview what reconcile would do
uv run python scripts/ctx_reconcile_state.py --dry-run
```

### Step 2: Commit or Stash Work

```bash
# If you have uncommitted work
cd .worktrees/WO-XXXX

# Option A: Commit partial work
git add .
git commit -m "wip(WO-XXXX): partial work, aborting"

# Option B: Stash for later
git stash push -m "WO-XXXX partial work"
```

### Step 3: Use Official Script

**Preferred: If `ctx_wo_abort.py` exists**:
```bash
uv run python scripts/ctx_wo_abort.py WO-XXXX --reason "blocked by dependency"
```

**Fallback: Use reconcile only**

Do NOT assume `ctx_wo_finish.py --result failed` exists or works.

```bash
# Reconcile to clean state
uv run python scripts/ctx_reconcile_state.py --apply

# Let the USER decide what state the WO should end in:
# - failed
# - partial
# - back to pending
```

**If neither works**, derive to `wo/repair`:
```bash
# Use the repair skill - it will use official scripts only
```

### Step 4: Verify State

```bash
# Check WO is in correct state
uv run python scripts/ctx_wo_take.py --status

# Confirm WO is NOT in running
ls _ctx/jobs/running/ | grep WO-XXXX
# Should be empty or not found
```

## Abort vs Other Options

| Scenario | Action |
|----------|--------|
| Work started, can't complete | User decides: `failed` or `partial` |
| Work not really started | `reconcile` moves back to `pending` |
| External blocker, will resume later | User decides: `partial` or keep `running` |
| WO was taken in error | `reconcile` to clean up |

**Key point**: Abort just cleans up. The USER decides the final state.

## Session Logging

Always log the abort:

```bash
trifecta session append --segment . \
  --summary "[WO-XXXX] result: aborted - <reason>" \
  --commands "reconcile,abort"
```

## Resources

- `scripts/ctx_reconcile_state.py` - State reconciliation
- `scripts/ctx_wo_abort.py` - Official abort (if exists)
- `docs/backlog/TROUBLESHOOTING.md` - Troubleshooting guide

## Quick Reference

```bash
# PREFERRED: Official abort script (if exists)
uv run python scripts/ctx_wo_abort.py WO-XXXX --reason "blocked"

# FALLBACK: Reconcile only (user decides final state)
uv run python scripts/ctx_reconcile_state.py --dry-run
uv run python scripts/ctx_reconcile_state.py --apply

# NEVER: Manual file operations
# rm/mv on _ctx/ files is FORBIDDEN
```

## Required Output

After abort completes:

```
ACTIVE_WO=none
CWD=/path/main/repo
BRANCH=main (or previous branch)
STATE=<pending|failed|partial - as decided>
NEXT_ALLOWED=["/wo-start","take different WO","review abandoned work"]
```
