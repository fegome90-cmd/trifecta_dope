# Work Order Troubleshooting Guide

Common issues, errors, and solutions for the Trifecta Dope WO system.

## Quick Diagnostics

**Run these commands first:**

```bash
# Check system status
python scripts/ctx_wo_take.py --status

# Validate backlog integrity
python scripts/ctx_backlog_validate.py --strict

# List worktrees
git worktree list

# Check for stale locks
find _ctx/jobs/running -name "*.lock" -mtime +1h
```

## Common Issues

### "Work order is locked"

**Error message:**
```
ERROR: Work order is locked: WO-0013
Lock info:
Locked by ctx_wo_take.py at 2026-01-09T20:00:00+00:00
PID: 12345
User: otheruser
```

**Cause:** Lock exists in `_ctx/jobs/running/WO-XXXX.lock`

**Diagnosis:**
```bash
# Check lock age
stat _ctx/jobs/running/WO-0013.lock

# View lock contents
cat _ctx/jobs/running/WO-0013.lock
```

**Solutions:**

1. **Wait for lock to expire** (if < 1 hour old)
   - Lock is active, wait for owner to complete
   - Contact owner if needed

2. **Remove stale lock** (if > 1 hour old)
   ```bash
   rm _ctx/jobs/running/WO-0013.lock
   ```

3. **Force unlock** (emergency only)
   ```bash
   # Remove lock manually
   rm _ctx/jobs/running/WO-0013.lock

   # Verify WO state
   ls -la _ctx/jobs/running/WO-0013.yaml

   # If WO is in running but no work exists, move back to pending
   mv _ctx/jobs/running/WO-0013.yaml _ctx/jobs/pending/
   ```

### "Worktree already exists"

**Error message:**
```
WARNING: Worktree already exists: .worktrees/WO-0013
Worktree .worktrees/WO-0013 is already registered with git
```

**Cause:** Worktree from previous WO execution wasn't cleaned up

**Diagnosis:**
```bash
# List worktrees
git worktree list

# Check if directory exists
ls -la .worktrees/WO-0013
```

**Solutions:**

1. **Re-use existing worktree** (safe)
   ```bash
   # The script will detect and re-use it
   cd .worktrees/WO-0013
   # Continue working
   ```

2. **Remove worktree** (if you want fresh start)
   ```bash
   # Remove worktree
   git worktree remove .worktrees/WO-0013

   # Remove branch (optional)
   git branch -D feat/wo-WO-0013

   # Try taking WO again
   python scripts/ctx_wo_take.py WO-0013
   ```

3. **Force cleanup** (if worktree is corrupted)
   ```bash
   # Prune stale references
   git worktree prune

   # Remove directory manually
   rm -rf .worktrees/WO-0013

   # Reconcile state
   python scripts/ctx_reconcile_state.py
   ```

### "fatal: invalid reference: feat/wo-WO-XXXX"

**Error message:**
```
ERROR: Command failed: git worktree add .worktrees/WO-0013 feat/wo-WO-0013
stderr: fatal: invalid reference: feat/wo-WO-0013
```

**Cause:** Code tried to use a branch that doesn't exist

**Diagnosis:**
```bash
# Check if branch exists
git rev-parse --verify feat/wo-WO-0013

# Check all branches
git branch -a
```

**Solutions:**

1. **Let script create branch** (recommended)
   - Don't specify branch in WO YAML
   - Script will auto-create from `main`

2. **Create branch manually**
   ```bash
   git branch feat/wo-WO-0013 main
   python scripts/ctx_wo_take.py WO-0013
   ```

3. **Remove branch from WO YAML**
   ```yaml
   # Edit _ctx/jobs/pending/WO-0013.yaml
   # Remove this line:
   # branch: feat/wo-WO-0013
   ```

### "Schema validation failed"

**Error message:**
```
ERROR: Schema validation failed: 'WO-0013' is not of type 'regex'
```

**Cause:** WO YAML doesn't match schema

**Diagnosis:**
```bash
# Validate specific WO
python scripts/ctx_backlog_validate.py --strict

# Validate all WOs
python scripts/ctx_backlog_validate.py --strict --wo WO-0013
```

**Common schema errors:**

| Error | Cause | Fix |
|-------|-------|-----|
| `WO-XXXX` not regex | Wrong ID format | Use `WO-XXXX` (4 digits) |
| Missing `epic_id` | No epic reference | Add `epic_id: E-XXXX` |
| Missing `dod_id` | No DoD reference | Add `dod_id: DOD-XXXX` |
| Invalid `status` | Wrong status value | Use: `pending`, `running`, `done`, `failed` |

**Solutions:**

1. **Fix WO YAML**
   ```yaml
   # Correct format
   version: 1
   id: WO-0013        # Must be WO-XXXX format
   epic_id: E-0001    # Must reference existing epic
   status: pending    # Must be valid status
   dod_id: DOD-DEFAULT  # Must reference existing DoD
   ```

2. **Reference schema**
   ```bash
   # View schema requirements
   cat docs/backlog/schema/work_order.schema.json
   ```

### "Unknown epic_id"

**Error message:**
```
ERROR: Unknown epic_id: E-9999
```

**Cause:** WO references epic that doesn't exist in backlog

**Diagnosis:**
```bash
# Check existing epics
grep "id: E-" _ctx/backlog/backlog.yaml
```

**Solutions:**

1. **Create epic first**
   ```yaml
   # Edit _ctx/backlog/backlog.yaml
   epics:
     - id: E-9999
       title: "New Epic"
       wo_queue: [WO-0013]
   ```

2. **Fix epic_id in WO**
   ```yaml
   # Edit _ctx/jobs/pending/WO-0013.yaml
   epic_id: E-0001  # Use existing epic
   ```

### "Work order not found"

**Error message:**
```
ERROR: Work order not found: _ctx/jobs/pending/WO-0013.yaml
```

**Cause:** WO YAML doesn't exist in expected location

**Diagnosis:**
```bash
# Check if WO exists anywhere
find _ctx/jobs -name "WO-0013.yaml"

# Check pending directory
ls -la _ctx/jobs/pending/
```

**Solutions:**

1. **Create WO YAML**
   ```bash
   # Copy template
   cp _ctx/jobs/pending/WO-0000.template.yaml _ctx/jobs/pending/WO-0013.yaml

   # Edit with correct values
   vim _ctx/jobs/pending/WO-0013.yaml
   ```

2. **Check if WO is already running/done**
   ```bash
   ls -la _ctx/jobs/running/WO-0013.yaml
   ls -la _ctx/jobs/done/WO-0013.yaml
   ```

### "Scope violation"

**Error message (during DoD verification):**
```
ERROR: Scope violation: modified src/domain/entity.py
This file is denied by WO scope.
```

**Cause:** Modified file that WO is not allowed to edit

**Diagnosis:**
```bash
# Check WO scope
cat _ctx/jobs/running/WO-0013.yaml | grep -A 10 scope

# Check what you modified
git status
```

**Solutions:**

1. **Revert disallowed changes**
   ```bash
   git checkout src/domain/entity.py
   ```

2. **Update WO scope** (if needed)
   ```yaml
   # Edit _ctx/jobs/running/WO-0013.yaml
   scope:
     allow:
       - "src/domain/entity.py"  # Add this file
     deny:
       - "src/domain/other/**"
   ```

3. **Create new WO** for disallowed changes
   ```bash
   # Create separate WO for domain changes
   python scripts/ctx_wo_create.py --epic E-0001
   ```

### "Context pack validation failed"

**Error message:**
```
ERROR: ctx validate reported stale pack
```

**Cause:** Context pack is out of sync with codebase

**Diagnosis:**
```bash
# Validate context
uv run trifecta ctx validate --segment .
```

**Solutions:**

1. **Sync context pack**
   ```bash
   make ctx-sync SEGMENT=.
   # OR
   uv run trifecta ctx sync --segment .
   ```

2. **Re-validate**
   ```bash
   uv run trifecta ctx validate --segment .
   ```

### State Inconsistencies

**Symptom:** WO in `running/` but no lock exists

**Diagnosis:**
```bash
# Check for running WOs without locks
for wo in _ctx/jobs/running/WO-*.yaml; do
  id=$(basename "$wo" .yaml)
  lock="_ctx/jobs/running/${id}.lock"
  if [ ! -f "$lock" ]; then
    echo "Missing lock for $id"
  fi
done
```

**Solution:**
```bash
# Repair state
python scripts/ctx_reconcile_state.py
```

**Symptom:** Worktree exists but WO is `done`

**Diagnosis:**
```bash
# Find orphaned worktrees
git worktree list | while read path branch; do
  wo=$(echo "$branch" | grep -o "WO-[0-9]\{4\}")
  if [ -n "$wo" ]; then
    if [ -f "_ctx/jobs/done/${wo}.yaml" ]; then
      echo "Orphaned worktree: $path ($wo)"
    fi
  fi
done
```

**Solution:**
```bash
# Remove orphaned worktrees
git worktree remove .worktrees/WO-XXXX
```

## Recovery Procedures

### Recover from crashed `ctx_wo_take.py`

**Symptom:** Script crashed during execution

**Steps:**
```bash
# 1. Check for partial state
python scripts/ctx_wo_take.py --status

# 2. Check for lock
ls -la _ctx/jobs/running/*.lock

# 3. Reconcile state
python scripts/ctx_reconcile_state.py

# 4. Retry take operation
python scripts/ctx_wo_take.py WO-XXXX
```

### Recover from git worktree corruption

**Symptom:** Worktree directory exists but not functional

**Steps:**
```bash
# 1. Prune stale references
git worktree prune

# 2. Remove corrupted worktree
rm -rf .worktrees/WO-XXXX

# 3. Remove branch (if needed)
git branch -D feat/wo-WO-XXXX

# 4. Retake WO
python scripts/ctx_wo_take.py WO-XXXX
```

### Recover from lock race condition

**Symptom:** Two processes tried to take same WO

**Steps:**
```bash
# 1. Check lock contents
cat _ctx/jobs/running/WO-XXXX.lock

# 2. Verify only one process should own it
ps aux | grep $(cat _ctx/jobs/running/WO-XXXX.lock | grep PID)

# 3. If process is dead, remove lock
rm _ctx/jobs/running/WO-XXXX.lock

# 4. Reconcile state
python scripts/ctx_reconcile_state.py
```

## Prevention

### Best Practices to Avoid Issues

1. **Always use scripts** - Never manually move YAML files
2. **Complete WOs before leaving** - Don't leave WOs in `running` overnight
3. **Regular cleanup** - Run `git worktree prune` weekly
4. **Validate before commits** - Run `ctx_backlog_validate.py --strict`
5. **Monitor locks** - Check `--status` for unexpected running WOs

### Regular Maintenance

```bash
# Weekly maintenance script
#!/bin/bash
echo "=== WO System Maintenance ==="

echo "1. Pruning worktrees..."
git worktree prune

echo "2. Validating backlog..."
python scripts/ctx_backlog_validate.py --strict

echo "3. Checking status..."
python scripts/ctx_wo_take.py --status

echo "4. Reconciling state..."
python scripts/ctx_reconcile_state.py --dry-run

echo "=== Maintenance Complete ==="
```

## Getting Help

### Information to Gather

Before asking for help, collect:

```bash
# System status
python scripts/ctx_wo_take.py --status > status.txt

# Git status
git status > git_status.txt

# Worktree list
git worktree list > worktrees.txt

# Validation results
python scripts/ctx_backlog_validate.py --strict > validation.txt 2>&1

# Lock info
find _ctx/jobs/running -name "*.lock" -exec cat {} \; > locks.txt
```

### Diagnostic Script

```bash
#!/bin/bash
# Full diagnostic dump

echo "=== WO System Diagnostics ==="
echo "Date: $(date)"
echo ""

echo "=== System Status ==="
python scripts/ctx_wo_take.py --status
echo ""

echo "=== Git Status ==="
git status
echo ""

echo "=== Worktrees ==="
git worktree list
echo ""

echo "=== Lock Files ==="
find _ctx/jobs/running -name "*.lock" -type f
echo ""

echo "=== Pending WOs ==="
ls -1 _ctx/jobs/pending/WO-*.yaml 2>/dev/null || echo "None"
echo ""

echo "=== Running WOs ==="
ls -1 _ctx/jobs/running/WO-*.yaml 2>/dev/null | grep -v ".lock" || echo "None"
echo ""

echo "=== Done WOs (last 5) ==="
ls -1t _ctx/jobs/done/WO-*.yaml 2>/dev/null | head -5 || echo "None"
echo ""

echo "=== Validation ==="
python scripts/ctx_backlog_validate.py --strict
echo ""

echo "=== End Diagnostics ==="
```

## Related Documentation

- **[WORKFLOW.md](WORKFLOW.md)** - Complete lifecycle guide
- **[OPERATIONS.md](OPERATIONS.md)** - Daily operations playbook
- **[README.md](README.md)** - Overview and state machine
- **[MIGRATION.md](MIGRATION.md)** - Legacy format migration
