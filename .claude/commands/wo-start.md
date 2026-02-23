---
description: Start work on a WO - from pending to working in worktree
---

# /wo-start - Start Work Order

Take a pending WO and set up isolated development environment.

**HARD RULES:**
- MUST run from CLEAN worktree (no uncommitted changes)
- MUST pass reconcile + audit P0 + preflight/lint guards BEFORE take
- MUST complete in <10s (deep audit is separate)
- NO silent fallback - any guard FAIL → STOP → suggest /wo-repair

## Usage

```
/wo-start WO-XXXX
```

## Pipeline (v2 - Hardened)

0. **wo/dirty-check** - Verify clean worktree [BLOCKING]
1. **wo/status** - Read-only snapshot
2. **wo/reconcile** - State drift check [BLOCKING]
3. **wo/audit-p0** - P0-only audit (<10s) [BLOCKING]
4. **wo/guard PRE-TAKE** - Preflight + lint [BLOCKING]
5. **wo/take** - Creates lock + worktree + branch
6. **wo/guard POST-TAKE** - Verifies worktree correct
7. **wo/work** - Prints rules and allowed next actions

## If Guard Fails

STOP, diagnose, suggest `/wo-repair`. Do not proceed.

## Required Output

```
=== WO-XXXX START ===

1. Status snapshot:
   - Pending: X WOs
   - Running: Y WOs
   - System: OK/WARN

2. Guard PRE-TAKE: PASS

3. Take WO-XXXX:
   - Branch: feat/wo-WO-XXXX
   - Worktree: .worktrees/WO-XXXX
   - Lock: _ctx/jobs/running/WO-XXXX.lock
   - State: pending → running

4. Guard POST-TAKE: PASS

5. Work rules loaded

=== READY TO WORK ===
ACTIVE_WO=WO-XXXX
WORKTREE=/path/.worktrees/WO-XXXX
BRANCH=feat/wo-WO-XXXX
STATE=running
NEXT_ALLOWED=["edit within scope","run verify","commit small","/wo-finish","/wo-repair"]
```

## Process

### Step 0: Dirty Check [BLOCKING]

```bash
if [ -n "$(git status --porcelain)" ]; then
  echo "BLOCKING: Dirty worktree - commit or stash changes first"
  echo "PROHIBITED: /wo-start with uncommitted changes"
  exit 1
fi
```

### Step 1: Status Snapshot

```bash
uv run python scripts/ctx_wo_take.py --status
uv run python scripts/ctx_wo_take.py --list
```

### Step 2: Reconcile Preflight [BLOCKING]

```bash
uv run python scripts/ctx_reconcile_state.py --dry-run
# Expected: "No drift detected" or abort with /wo-repair
```

### Step 3: Audit P0-Only [BLOCKING]

```bash
uv run python scripts/wo_audit.py --fast-p0 --out /tmp/wo_audit_p0.json --fail-on split_brain,fail_but_running
# Expected: exit 0 (no P0 findings) or abort with /wo-repair
```

### Step 4: Guard PRE-TAKE (Preflight + Lint) [BLOCKING]

```bash
uv run python scripts/ctx_wo_preflight.py WO-XXXX
uv run python scripts/ctx_wo_lint.py --strict --wo-id WO-XXXX
```

- No conflicting locks (from OTHER WOs)
- System healthy
- WO exists in pending

### Step 3: Create (if needed)

If WO doesn't exist:
```bash
uv run python scripts/ctx_wo_bootstrap.py --id WO-XXXX --epic E-YYYY ...
```

### Step 4: Take

```bash
uv run python scripts/ctx_wo_take.py WO-XXXX
```

### Step 5: Guard POST-TAKE

- Verify in worktree
- Verify correct branch
- Verify YAML in running
- Verify lock exists

### Step 6: Navigate and Sync

```bash
cd .worktrees/WO-XXXX
uv run trifecta ctx sync --segment .
```

### Step 7: Session Marker

```bash
trifecta session append --segment . --summary "[WO-XXXX] intent: <description>"
```

## Example

```
> /wo-start WO-0055

=== WO-0055 START ===

1. Status snapshot:
   - Pending: 16 WOs
   - Running: 2 WOs
   - System: OK

2. Guard PRE-TAKE: PASS
   - No conflicting locks
   - WO-0055 exists in pending

3. Take WO-0055:
   - Branch: feat/wo-WO-0055
   - Worktree: .worktrees/WO-0055
   - Lock: _ctx/jobs/running/WO-0055.lock
   - State: pending → running

4. Guard POST-TAKE: PASS
   - Worktree: ✓
   - Branch: ✓
   - YAML: ✓
   - Lock: ✓

5. Work rules loaded

=== READY TO WORK ===
ACTIVE_WO=WO-0055
WORKTREE=/Users/.../bilbao/.worktrees/WO-0055
BRANCH=feat/wo-WO-0055
STATE=running
NEXT_ALLOWED=["edit within scope","run verify","commit small","/wo-finish","/wo-repair"]
```
