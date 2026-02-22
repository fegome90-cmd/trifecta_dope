---
name: wo/take
description: Take a pending Work Order and set up isolated development environment
---

# WO Take - Worktree Setup

## Overview

Take a pending WO and create an isolated development environment (worktree, branch, lock).

## When to Use

- Ready to start work on a pending WO
- Need isolated git environment

## Prerequisites

- WO exists in `_ctx/jobs/pending/`
- No conflicting locks (from OTHER WOs)
- Dependencies are completed (if any)

## Process

### Step 1: List Pending WOs

```bash
uv run python scripts/ctx_wo_take.py --list
```

### Step 2: Check System Status

```bash
uv run python scripts/ctx_wo_take.py --status
```

Look for:
- Existing running WOs
- Stale locks
- Worktree conflicts

### Step 3: Take the WO

```bash
uv run python scripts/ctx_wo_take.py WO-XXXX [--owner myname]
```

**What gets created**:
| Artifact | Location |
|----------|----------|
| Branch | `feat/wo-WO-XXXX` |
| Worktree | `.worktrees/WO-XXXX/` |
| Lock | `_ctx/jobs/running/WO-XXXX.lock` |
| YAML | Moved from `pending/` to `running/` |

### Step 4: Navigate to Worktree

```bash
cd .worktrees/WO-XXXX
```

**IMPORTANT**: All work happens in the worktree, NOT in main repo.

### Step 5: Sync Context

```bash
# Inside worktree
uv run trifecta ctx sync --segment .
```

### Step 6: Log Session Intent

```bash
# Required session marker
trifecta session append --segment . \
  --summary "[WO-XXXX] intent: <what you're going to do>" \
  --files "<files you'll modify>" \
  --commands "take,ctx sync"
```

**Session marker format** (REQUIRED):
```
[WO-XXXX] intent: <description>
```

This marker is validated by `wo/guard` before finish.

### Step 7: Run POST-TAKE Guard

**This kills the "I took WO but kept working in main" problem.**

```bash
# Verify you're in the right place
git worktree list --porcelain | grep -A2 "$(pwd)" | grep "branch feat/wo-WO-XXXX"

# Verify YAML is running
cat ../_ctx/jobs/running/WO-XXXX.yaml | grep "status: running"

# Verify lock exists
test -f ../_ctx/jobs/running/WO-XXXX.lock && echo "Lock OK"
```

If any check fails → STOP → diagnose → `/wo-repair`

## What Happens During Take

1. Validates WO exists in `pending/`
2. Validates execution contract (`engine: trifecta`, `required_flow`)
3. Validates epic_id exists in backlog
4. Runs lint validation (strict mode)
5. Validates dependencies (all must be `done/`)
6. **Acquires atomic lock** (`running/{wo_id}.lock`)
7. Creates git worktree at `.worktrees/{wo_id}`
8. Creates branch `feat/wo-{wo_id}`
9. Updates WO metadata (owner, status=running, started_at)
10. Moves WO from `pending/` to `running/`
11. Updates worktree index

## Transaction Rollback

If anything fails, the system automatically:
- Removes lock
- Removes worktree
- Removes branch
- Moves WO back to pending

## Common Mistakes

| Mistake | Why Bad | Fix |
|---------|---------|-----|
| Working in main repo | Breaks isolation | `cd .worktrees/WO-XXXX` |
| Forgetting session marker | Guard fails at finish | Add `[WO-XXXX] intent:` |
| Ignoring existing locks | Race condition | Check `--status` first |
| Skipping POST-TAKE guard | Working in wrong place | Always run guard |
| Skipping ctx sync | Missing context | Always run `ctx sync` |

## Resources

- `scripts/ctx_wo_take.py` - Main take script
- `scripts/helpers.py` - Worktree/lock helpers
- `docs/backlog/WORKFLOW.md` - Full workflow docs
- `docs/backlog/OPERATIONS.md` - Daily operations

## Quick Reference

```bash
# List pending
uv run python scripts/ctx_wo_take.py --list

# Check status
uv run python scripts/ctx_wo_take.py --status

# Take WO
uv run python scripts/ctx_wo_take.py WO-XXXX

# Navigate
cd .worktrees/WO-XXXX

# Sync context
uv run trifecta ctx sync --segment .

# Log intent
trifecta session append --segment . --summary "[WO-XXXX] intent: description"

# POST-TAKE guard
git worktree list --porcelain | grep -A2 "$(pwd)" | grep "branch feat/wo-WO-XXXX"
```

## Required Output

After take completes:

```
ACTIVE_WO=WO-XXXX
CWD=/path/.worktrees/WO-XXXX
BRANCH=feat/wo-WO-XXXX
STATE=running
NEXT_ALLOWED=["edit within scope","run verify","commit small","session append","finish when done"]
```
