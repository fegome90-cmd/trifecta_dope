---
description: Start work on a WO - from pending to working in worktree (fail-closed)
---

# /wo-start - Start Work Order

Take a pending WO and set up isolated development environment.

**PRINCIPLE**: `/wo-start` no "arregla" silenciosamente. O está limpio, o se corta.
Arreglar es otra skill: `/wo-repair`.

## Usage

```
/wo-start WO-XXXX
```

## Pipeline (FAIL-CLOSED)

0. **dirty/check** - No uncommitted changes
1. **wo/status** (read-only snapshot)
2. **reconcile/preflight** (global drift detection)
3. **audit/forensic** (P0 findings check)
4. **wo/guard PRE-TAKE** (invariantes + preflight/lint)
5. Si WO no existe → **wo/create** (bootstrap)
6. **wo/take** (crea lock + worktree + branch)
7. **wo/guard POST-TAKE** (verifica worktree correcto)
8. **wo/work** (imprime reglas y allowed next actions)

## If ANY Guard Fails

STOP, diagnose, suggest `/wo-repair`. **Do not proceed. Do not auto-fix.**

## Required Output

```
=== WO-XXXX START ===

0. Dirty check: PASS
   - No uncommitted changes

1. Status snapshot:
   - Pending: X WOs
   - Running: Y WOs
   - System: OK

2. Reconcile Preflight: PASS
   - No P0/P1 issues detected

3. Forensic Audit: PASS
   - No P0 findings

4. Guard PRE-TAKE: PASS
   - WO-XXXX in pending (only): ✓
   - No existing lock: ✓
   - No existing worktree: ✓
   - Lint: ✓
   - Preflight: ✓

5. Take WO-XXXX:
   - Branch: feat/wo-WO-XXXX
   - Worktree: .worktrees/WO-XXXX
   - Lock: _ctx/jobs/running/WO-XXXX.lock
   - State: pending → running

6. Guard POST-TAKE: PASS
   - Worktree: ✓
   - Branch: ✓
   - YAML: ✓
   - Lock: ✓
   - Markers: ✓

=== READY TO WORK ===
ACTIVE_WO=WO-XXXX
WORKTREE=/path/.worktrees/WO-XXXX
BRANCH=feat/wo-WO-XXXX
STATE=running
NEXT_ALLOWED=["work (within scope)", "/wo-finish", "/wo-repair"]
PROHIBITED=["manual rm/mv _ctx", "work outside worktree", "bootstrap new WO to escape"]
```

## Process

### Step 0: Dirty Check (FAIL-CLOSED)

```bash
test -z "$(git status --porcelain)" || (echo "DIRTY_WORKTREE: cannot /wo-start" && exit 1)
```

**If FAIL**: Commit or stash changes before starting.

### Step 1: Status Snapshot

```bash
uv run python scripts/ctx_wo_take.py --status
git worktree list
```

### Step 1.5: Reconcile Preflight (Global Drift Detection)

```bash
uv run python scripts/ctx_reconcile_state.py --root .
```

**Abort Conditions** (any P0 or P1 in output):
| Code | Description | Action |
|------|-------------|--------|
| `WO_INVALID_SCHEMA` | Schema broken | ABORT → `/wo-repair` |
| `DUPLICATE_WO_ID` | Same WO in multiple states | ABORT → `/wo-repair` |
| `LOCK_WITHOUT_RUNNING_WO` | Orphan lock | ABORT → `/wo-repair` |
| `WORKTREE_WITHOUT_RUNNING_WO` | Orphan worktree | ABORT → `/wo-repair` |

**Output if abort:**
```
=== PREFLIGHT FAILED ===

Issues detected:
- WO_INVALID_SCHEMA: WO-0018A
- LOCK_WITHOUT_RUNNING_WO: WO-0015, WO-0046, WO-0048

CANNOT PROCEED. Run: /wo-repair
```

### Step 1.6: Forensic Audit (Optional but Recommended)

```bash
uv run python scripts/wo_audit.py --out /tmp/audit.json
```

**Abort if P0 found.** (P1 depends on tolerance)

### Step 2: Guard PRE-TAKE (Hardened)

**Checks:**
1. ✅ WO existe en `pending/` **y solo ahí**
2. ✅ No existe lock para WO
3. ✅ No existe worktree para WO
4. ✅ `ctx_wo_lint.py` pasa para WO
5. ✅ `ctx_wo_preflight.py` pasa para WO

```bash
# Verify WO in pending ONLY (not in running, done, or failed)
test -f _ctx/jobs/pending/WO-XXXX.yaml || (echo "WO_NOT_IN_PENDING" && exit 1)
test ! -f _ctx/jobs/running/WO-XXXX.yaml || (echo "WO_ALREADY_RUNNING" && exit 1)
test ! -f _ctx/jobs/done/WO-XXXX.yaml || (echo "WO_ALREADY_DONE" && exit 1)
test ! -f _ctx/jobs/failed/WO-XXXX.yaml || (echo "WO_IN_FAILED" && exit 1)

# Verify no lock
test ! -f _ctx/jobs/running/WO-XXXX.lock || (echo "LOCK_EXISTS" && exit 1)

# Verify no worktree (CORRECT: grep -q, not grep -v)
git worktree list | grep -q "WO-XXXX" && echo "FOUND_WORKTREE" && exit 1 || true

# Preflight + Lint
uv run python scripts/ctx_wo_preflight.py WO-XXXX || exit 1
uv run python scripts/ctx_wo_lint.py --wo-id WO-XXXX || exit 1
```

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

```bash
# Verify in worktree
pwd | grep -q "WO-XXXX" || (echo "NOT_IN_WORKTREE" && exit 1)

# Verify correct branch
git branch --show-current | grep -q "WO-XXXX" || (echo "WRONG_BRANCH" && exit 1)

# Verify YAML in running
test -f _ctx/jobs/running/WO-XXXX.yaml || (echo "YAML_NOT_IN_RUNNING" && exit 1)

# Verify lock exists
test -f _ctx/jobs/running/WO-XXXX.lock || (echo "LOCK_MISSING" && exit 1)
```

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

0. Dirty check: PASS
   - No uncommitted changes

1. Status snapshot:
   - Pending: 16 WOs
   - Running: 2 WOs
   - System: OK

2. Reconcile Preflight: PASS
   - No P0/P1 issues detected

3. Forensic Audit: PASS
   - No P0 findings

4. Guard PRE-TAKE: PASS
   - WO-0055 in pending (only): ✓
   - No existing lock: ✓
   - No existing worktree: ✓
   - Lint: ✓
   - Preflight: ✓

5. Take WO-0055:
   - Branch: feat/wo-WO-0055
   - Worktree: .worktrees/WO-0055
   - Lock: _ctx/jobs/running/WO-0055.lock
   - State: pending → running

6. Guard POST-TAKE: PASS
   - Worktree: ✓
   - Branch: ✓
   - YAML: ✓
   - Lock: ✓

=== READY TO WORK ===
ACTIVE_WO=WO-0055
WORKTREE=/Users/.../.worktrees/WO-0055
BRANCH=feat/wo-WO-0055
STATE=running
NEXT_ALLOWED=["work (within scope)", "/wo-finish", "/wo-repair"]
PROHIBITED=["manual rm/mv _ctx", "work outside worktree", "bootstrap new WO to escape"]
```

## Abort Example

```
> /wo-start WO-0015

=== WO-0015 START ===

0. Dirty check: PASS

1. Status snapshot:
   - Pending: 12 WOs
   - Running: 1 WOs
   - System: WARN

2. Reconcile Preflight: FAILED

Issues detected:
- LOCK_WITHOUT_RUNNING_WO: WO-0015, WO-0046, WO-0048
- DUPLICATE_WO_ID: WO-0008

CANNOT PROCEED. Run: /wo-repair

=== ABORT ===
REASON: Preflight detected P1 issues
ACTION: /wo-repair
```

## Scripts Used

| Step | Script | Purpose |
|------|--------|---------|
| 0 | (bash) | Dirty check |
| 1 | `ctx_wo_take.py --status` | Status snapshot |
| 1.5 | `ctx_reconcile_state.py` | Drift detection |
| 1.6 | `wo_audit.py` | Forensic audit |
| 2 | `ctx_wo_preflight.py` | WO validation |
| 2 | `ctx_wo_lint.py` | WO linting |
| 4 | `ctx_wo_take.py` | Take WO |
