---
description: Repair WO system state - fix locks, worktrees, inconsistencies
---

# /wo-repair - Repair WO System

Recover determinism when there's drift (locks, worktrees, state inconsistencies).

## Usage

```
/wo-repair [WO-XXXX|--all]
```

## Pipeline

1. **wo/status** (foto completa)
2. **wo/guard** (si hay WO especificado: check invariantes)
3. **wo/repair**:
   - Primero `ctx_reconcile_state.py --dry-run`
   - Solo si plan seguro → `--apply`
4. Si es "abortar" → **wo/abort** (deriva a repair o script oficial, NO rm/mv manual)

## Required Output

```
=== WO REPAIR ===

1. Status:
   PROBLEM → FIX APPLIED → RESULT (tabla)

2. State Now:
   - Pending: X
   - Running: Y
   - Done: Z
   - Failed: W

3. Next:
   - volver a /wo-start
   - o /wo-finish
```

## Process

### Step 1: Status Snapshot

```bash
uv run python scripts/ctx_wo_take.py --status
git worktree list
ls _ctx/jobs/running/*.lock 2>/dev/null
```

### Step 2: Diagnose Problems

Common problems:
| Problem | Diagnosis Command |
|---------|-------------------|
| Stale lock | `stat _ctx/jobs/running/WO-XXXX.lock` (check age vs TTL) |
| Orphaned worktree | `git worktree list` (worktree without running WO) |
| State mismatch | `ctx_reconcile_state.py --dry-run` |
| Lock without YAML | `ls _ctx/jobs/running/*.lock` vs `ls _ctx/jobs/running/*.yaml` |

### Step 3: Preview Fix

```bash
uv run python scripts/ctx_reconcile_state.py --dry-run
```

**Review the plan before applying!**

### Step 4: Apply Fix (if safe)

```bash
uv run python scripts/ctx_reconcile_state.py --apply
```

### Step 5: Verify

```bash
uv run python scripts/ctx_wo_take.py --status
```

## ⛔ NEVER

**Manual operations on _ctx/ are FORBIDDEN:**
- `rm _ctx/jobs/running/*.lock`
- `mv _ctx/jobs/running/*.yaml`
- Direct file manipulation

**ALWAYS use official scripts.**

## Example

```
> /wo-repair --all

=== WO REPAIR ===

1. Status:
   Running WOs: 3
   Worktrees: 2
   Locks: 4

   PROBLEMS DETECTED:
   - WO-0048: lock exists, no YAML → stale lock
   - WO-0046: worktree missing, YAML running → orphaned state

2. Dry-run plan:
   - Remove stale lock: WO-0048
   - Move WO-0046 to failed (no worktree)

   Apply? [y/N] y

3. Applying...
   - Removed: _ctx/jobs/running/WO-0048.lock
   - Moved: WO-0046 → _ctx/jobs/failed/

4. State Now:
   - Pending: 16
   - Running: 1
   - Done: 33
   - Failed: 1

=== REPAIR COMPLETE ===
NEXT: /wo-start to resume work
```
