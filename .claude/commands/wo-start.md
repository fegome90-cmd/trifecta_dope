---
description: Start work on a WO - from pending to working in worktree
---

# /wo-start - Start Work Order

Take a pending WO and set up isolated development environment.

## Usage

```
/wo-start WO-XXXX
```

## Pipeline

1. **wo/status** (read-only snapshot)
2. **wo/guard PRE-TAKE** (invariantes mínimas)
3. Si WO no existe → **wo/create** (bootstrap + preflight)
4. **wo/take** (crea lock + worktree + branch)
5. **wo/guard POST-TAKE** (verifica worktree correcto)
6. **wo/work** (imprime reglas y allowed next actions)

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

### Step 1: Status Snapshot

```bash
uv run python scripts/ctx_wo_take.py --status
uv run python scripts/ctx_wo_take.py --list
```

### Step 2: Guard PRE-TAKE

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
