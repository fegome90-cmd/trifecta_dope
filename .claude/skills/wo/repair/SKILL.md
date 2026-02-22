---
name: wo/repair
description: Diagnose and fix Work Order state inconsistencies
---

# WO Repair - Troubleshooting and Recovery

## Overview

Diagnose and repair WO state inconsistencies: stale locks, orphaned worktrees, state drift.

## When to Use

- "Work order is locked" error
- Worktree exists but WO is done
- State mismatch between YAML and git
- Crashed `ctx_wo_take.py` execution
- Need to clean up abandoned work

## ⛔ NEVER

**Manual operations on `_ctx/` are FORBIDDEN:**

```bash
# ❌ FORBIDDEN
rm _ctx/jobs/running/WO-XXXX.lock

# ❌ FORBIDDEN
mv _ctx/jobs/running/WO-XXXX.yaml _ctx/jobs/pending/

# ❌ FORBIDDEN
rm -rf _ctx/jobs/running/*

# ❌ FORBIDDEN
echo "..." > _ctx/jobs/running/WO-XXXX.lock
```

**ALWAYS use official scripts:**
- `ctx_reconcile_state.py`
- `ctx_wo_finish.py`
- `git worktree` commands

## Diagnostic Commands

| Command | Purpose |
|---------|---------|
| `ctx_wo_take.py --status` | System health overview |
| `git worktree list` | Worktree inventory |
| `ctx_backlog_validate.py --strict` | Validate all WOs |
| `ctx_reconcile_state.py --dry-run` | Preview repairs |

## Common Issues and Solutions

### Issue 1: Stale Lock

**Symptoms**:
```
Error: Work order WO-XXXX is locked
```

**Diagnosis**:
```bash
# Check lock file
ls -la _ctx/jobs/running/WO-XXXX.lock

# Check lock age (DO NOT use hardcoded "1 hour")
# TTL is configured via WO_LOCK_TTL_SEC (default: 86400 = 24h)
```

**Solution**:
```bash
# 1. Preview repair
uv run python scripts/ctx_reconcile_state.py --dry-run

# 2. If safe, apply
uv run python scripts/ctx_reconcile_state.py --apply
```

### Issue 2: Orphaned Worktree

**Symptoms**:
- Worktree exists in `.worktrees/`
- No corresponding WO in `running/`

**Diagnosis**:
```bash
git worktree list
# Shows worktree but WO not in running/
```

**Solution**:
```bash
# 1. Check if worktree has uncommitted work
cd .worktrees/WO-XXXX
git status

# 2. If clean, remove worktree
git worktree remove .worktrees/WO-XXXX

# 3. If has work, either commit or stash first
```

### Issue 3: State Inconsistency

**Symptoms**:
- WO YAML says `running` but no worktree
- WO YAML says `pending` but has lock
- Files in wrong state directory

**Solution**:
```bash
# ALWAYS use reconcile script, never manual moves
uv run python scripts/ctx_reconcile_state.py --dry-run
# Review output carefully

uv run python scripts/ctx_reconcile_state.py --apply
```

### Issue 4: Schema Validation Failed

**Symptoms**:
```
Error: YAML parse error / Schema validation failure
```

**Solution**:
```bash
# Check specific WO
uv run python scripts/ctx_wo_lint.py --wo-id WO-XXXX --json

# Fix YAML issues
# Common: missing required fields, wrong types

# Format to canonical
uv run python scripts/ctx_wo_fmt.py --write
```

### Issue 5: Unknown epic_id

**Symptoms**:
```
Error: Unknown epic_id E-XXXX
```

**Solution**:
```bash
# Check if epic exists
grep "id: E-XXXX" _ctx/backlog/backlog.yaml

# If missing, add epic to backlog.yaml
# Or update WO to use existing epic
```

### Issue 7: Reconcile Falls with WO_INVALID_SCHEMA

**Symptoms**:
```
apply refused: WO_INVALID_SCHEMA
```

**Root Cause**: WOs or DoDs have invalid schemas that prevent reconcile from running.

**Diagnosis**:
```bash
# Identify schema issues
uv run python scripts/ctx_backlog_validate.py 2>&1 | head -30
```

**Common Schema Issues**:

1. **DoD con campo `items`** (debe tener campos requeridos):
   ```yaml
   # ❌ Inválido
   dod:
   - id: XXX
     items: [...]

   # ✅ Válido
   dod:
   - id: XXX
     title: "..."
     required_artifacts: [...]
     required_checks:
       - name: "check"
         commands: [...]
     rules: [...]
   ```

2. **WO con `required_flow` incompleto**:
   ```yaml
   # ❌ Inválido
   required_flow:
     - verify

   # ✅ Válido
   required_flow:
     - session.append:intent
     - ctx.sync
     - ctx.search
     - ctx.get
     - session.append:result
   ```

**Solution**:
```bash
# 1. Fix DoD schemas first
# Edit _ctx/dod/*.yaml to have required fields

# 2. Fix WO required_flow
# Use script to batch fix:
python3 -c "
import re
from pathlib import Path

old = r'required_flow:\n  - verify\n  segment: \.'
new = '''required_flow:
  - session.append:intent
  - ctx.sync
  - ctx.search
  - ctx.get
  - session.append:result
  segment: .'''

for f in Path('_ctx/jobs/done').glob('WO-*.yaml'):
    content = f.read_text()
    if 'required_flow:\n  - verify' in content:
        f.write_text(re.sub(old, new, content))
        print(f'Fixed: {f}')
"

# 3. Retry reconcile
uv run python scripts/ctx_reconcile_state.py --apply
```

**Note**: Modifying WOs in `done/` requires bypass (see `wo/finish` bypass options).

---

### Issue 6: Scope Violation

**Symptoms**:
- Modified files outside `scope.allow`
- Files in `scope.deny` were changed

**Solution**:
```bash
# Check what was modified
git diff --name-only origin/main...HEAD

# Compare with scope
grep -A 10 "scope:" _ctx/jobs/running/WO-XXXX.yaml

# Either:
# 1. Revert out-of-scope changes
git checkout origin/main -- <out-of-scope-file>

# 2. Or update scope (requires review)
# Edit WO YAML, add files to scope.allow
```

## Stale Lock Detection

**DO NOT use hardcoded "1 hour" rule.**

The TTL is configurable:
- Environment variable: `WO_LOCK_TTL_SEC` (default: `86400` = 24h)
- Checker function: `scripts/helpers.py` → `check_lock_age()`

```bash
# Check lock age via Python
uv run python -c "
from scripts.helpers import check_lock_age
from pathlib import Path
result = check_lock_age(Path('_ctx/jobs/running/WO-XXXX.lock'))
print(f'Lock valid: {result}')
"
```

## `--force` Usage Conditions

`--force` flags (e.g., `git worktree remove --force`) are ONLY allowed if:

1. **`git status` inside the worktree is clean** OR commit/stash was done
2. **`ctx_reconcile_state.py --dry-run` explains the plan**
3. **Decision is logged in session**

```bash
# Example: Force remove worktree
cd .worktrees/WO-XXXX
git status  # Must be clean OR committed/stashed

uv run python scripts/ctx_reconcile_state.py --dry-run  # Review plan

git worktree remove --force .worktrees/WO-XXXX

trifecta session append --segment . \
  --summary "Forced remove worktree WO-XXXX because <reason>"
```

## Recovery Procedures

### Crashed Take

If `ctx_wo_take.py` crashed mid-execution:

```bash
# 1. Check state
uv run python scripts/ctx_wo_take.py --status

# 2. Run reconcile
uv run python scripts/ctx_reconcile_state.py --dry-run
uv run python scripts/ctx_reconcile_state.py --apply

# 3. Retry take
uv run python scripts/ctx_wo_take.py WO-XXXX
```

### Worktree Corruption

```bash
# 1. Prune stale references
git worktree prune

# 2. Check remaining worktrees
git worktree list

# 3. Remove corrupted worktree (only if conditions met!)
# See --force usage conditions above
git worktree remove --force .worktrees/WO-XXXX

# 4. Re-run reconcile
uv run python scripts/ctx_reconcile_state.py --apply
```

### Lock Race Condition

```bash
# 1. Check if process is alive
cat _ctx/jobs/running/WO-XXXX.lock

# 2. If PID is dead, safe to reconcile
# But USE RECONCILE, not manual rm

uv run python scripts/ctx_reconcile_state.py --apply
```

## Resources

- `scripts/ctx_reconcile_state.py` - State reconciliation
- `scripts/helpers.py` - Lock age validation
- `scripts/ctx_wo_lint.py` - YAML validation
- `docs/backlog/TROUBLESHOOTING.md` - More troubleshooting

## Quick Reference

```bash
# System status
uv run python scripts/ctx_wo_take.py --status

# Preview repairs
uv run python scripts/ctx_reconcile_state.py --dry-run

# Apply repairs
uv run python scripts/ctx_reconcile_state.py --apply

# Check worktrees
git worktree list
git worktree prune

# Validate all WOs
uv run python scripts/ctx_backlog_validate.py --strict

# NEVER: rm/mv on _ctx/ files
```

## Required Output

After repair completes:

```
PROBLEM → FIX APPLIED → RESULT (table)
STATE NOW: X pending, Y running, Z done, W failed
ACTIVE_WO=<current or none>
NEXT: /wo-start to resume work OR /wo-finish to close
```
