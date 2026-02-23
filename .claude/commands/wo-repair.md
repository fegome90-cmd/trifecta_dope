---
description: Repair WO system state - fix locks, worktrees, inconsistencies
---

# /wo-repair - Repair WO System

Recover determinism when there's drift (locks, worktrees, state inconsistencies).

## Usage

```
/wo-repair [WO-XXXX|--all]
```

## Pipeline (v2 - Hardened)

1. **wo/snapshot** - Forensic snapshot before repair
2. **wo/status** - Full status audit
3. **wo/reconcile --apply** - Fix state drift
4. **wo/gc --apply** - Remove zombie/ghost worktrees
5. **wo/integrity** - Verify no P0 findings [BLOCKING]
6. If es "abortar" → **wo/abort** (deriva a script oficial, NO rm/mv manual)

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

### Step 1: Forensic Snapshot (Before Any Changes)

```bash
timestamp=$(date +%Y%m%d_%H%M%S)
snapshot_file="_ctx/incidents/FORENSIC-$(date +%Y-%m-%d).md"

# Capture current state
uv run python scripts/wo_audit.py --out /tmp/wo_audit_pre.json

# Create snapshot file
cat > "$snapshot_file" << 'EOF'
# FORENSIC SNAPSHOT
Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)

## WO Audit Summary
$(cat /tmp/wo_audit_pre.json | jq -r '.summary')

## Worktrees
$(git worktree list)

## Running WOs
$(ls -la _ctx/jobs/running/*.yaml 2>/dev/null || echo "None")

## Locks
$(ls -la _ctx/jobs/running/*.lock 2>/dev/null || echo "None")
EOF

echo "Snapshot saved: $snapshot_file"
```

### Step 2: Status Snapshot

```bash
uv run python scripts/ctx_wo_take.py --status
git worktree list
ls _ctx/jobs/running/*.lock 2>/dev/null
```

### Step 3: Diagnose Problems

Common problems:
| Problem | Diagnosis Command |
|---------|-------------------|
| Stale lock | `stat _ctx/jobs/running/WO-XXXX.lock` (check age vs TTL) |
| Orphaned worktree | `git worktree list` (worktree without running WO) |
| State mismatch | `ctx_reconcile_state.py --dry-run` |
| Lock without YAML | `ls _ctx/jobs/running/*.lock` vs `ls _ctx/jobs/running/*.yaml` |
| Zombie worktree | `ctx_wo_gc.py --dry-run` (worktree for done/failed WO) |

### Step 4: Apply Reconcile

```bash
# Preview first
uv run python scripts/ctx_reconcile_state.py --dry-run

# Apply if safe
uv run python scripts/ctx_reconcile_state.py --apply
```

### Step 5: Apply Garbage Collection

```bash
# Preview zombie/ghost worktrees
uv run python scripts/ctx_wo_gc.py --dry-run

# Apply cleanup
uv run python scripts/ctx_wo_gc.py --apply
```

### Step 6: Verify Integrity

```bash
make wo-integrity
# Expected: "WO Integrity: PASS"
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
