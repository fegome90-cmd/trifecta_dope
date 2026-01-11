# Work Order Workflow Guide

Complete guide to the Work Order (WO) lifecycle in Trifecta Dope.

## Overview

The WO system provides atomic, isolated development environments for each work order using git worktrees. Each WO follows a strict state machine with automatic branch creation, lock management, and verification.

## State Machine

```
                    ┌─────────────────────────────────────────────┐
                    │                                             │
                    ▼                                             │
┌─────────┐     ┌─────────┐     ┌──────────┐     ┌─────────┐    │
│ PENDING │ ──▶ │ RUNNING │ ──▶ │   DONE   │     │ FAILED  │ ◄──┘
└─────────┘     └─────────┘     └──────────┘     └─────────┘
                    │
                    │ (cleanup)
                    ▼
              ┌─────────┐
              │ STALE   │
              │ LOCK    │
              └─────────┘
```

**States:**
- **pending**: WO created, awaiting assignment
- **running**: WO taken, worktree created, in progress
- **done**: WO completed, DoD verified, SHA recorded
- **failed**: WO failed, moved to failed for analysis
- **stale lock**: Lock >1 hour old, auto-cleaned on next take

## Complete Lifecycle

### 1. Creation (Pending)

**Create WO YAML in `_ctx/jobs/pending/WO-XXXX.yaml`:**

```yaml
version: 1
id: WO-0013
epic_id: E-0001
title: "Descriptive title"
priority: P2
status: pending
scope:
  allow:
    - "docs/reports/wo0013_report.md"
    - "scripts/wo0013_script.py"
  deny:
    - "src/domain/**"
dod_id: DOD-DEFAULT
```

**Register in epic (optional but recommended):**
```bash
# Edit _ctx/backlog/backlog.yaml
epics:
  - id: E-0001
    wo_queue: [WO-0012, WO-0013]
```

### 2. Take (Pending → Running)

**Execute the take script:**
```bash
python scripts/ctx_wo_take.py WO-0013
```

**What happens automatically:**
1. **Lock acquisition**: Atomic lock created at `_ctx/jobs/running/WO-0013.lock`
2. **Branch generation**: Creates `feat/wo-WO-0013` from `main`
3. **Worktree creation**: Creates isolated environment at `.worktrees/WO-0013`
4. **Status transition**: YAML moved from `pending/` to `running/`
5. **Metadata update**: Owner, started_at, branch, worktree fields added

**Output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ✅ Work Order WO-0013 Taken Successfully
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  WO ID:     WO-0013
  Branch:    feat/wo-WO-0013
  Worktree:  .worktrees/WO-0013
  Owner:     felipe_gonzalez

Next steps:
  1. cd .worktrees/WO-0013
  2. Start working on WO-0013
  3. Run: python ctx_wo_finish.py WO-0013
```

### 3. Execution (Running)

**Navigate to worktree:**
```bash
cd .worktrees/WO-0013
```

**You're now in an isolated git environment:**
- Separate working directory from main repo
- On branch `feat/wo-WO-0013`
- Can commit changes without affecting main branch
- All git operations work normally

**Integrate with Trifecta CLI:**
```bash
# Sync context for this segment
make ctx-sync SEGMENT=.

# Search documentation
make ctx-search Q="Find telemetry implementation" SEGMENT=.

# Navigate AST symbols
uv run trifecta ast symbols "sym://python/mod/src.domain.result" --segment .
```

### 4. Verification (Running → Done/Failed)

**Prepare for completion:**
```bash
# Ensure all changes are committed
git status
git add .
git commit -m "WO-0013: Implement feature"

# Run Definition of DoD verification commands
# (specified in WO YAML under verify.commands)
```

**Complete the WO:**
```bash
python scripts/ctx_wo_finish.py WO-0013
```

**What happens:**
1. **DoD validation**: Runs verification commands from WO YAML
2. **SHA capture**: Records current commit SHA in `verified_at_sha`
3. **Status transition**: Moves YAML from `running/` to `done/`
4. **Lock release**: Removes atomic lock
5. **Backlog update**: Updates epic status in `backlog.yaml`

### 5. Cleanup (Optional)

**Worktree persists for reference** after completion. To cleanup:

```bash
# List all worktrees
git worktree list

# Remove specific worktree
git worktree remove .worktrees/WO-0013

# Prune stale references
git worktree prune

# Or use the helper
python scripts/ctx_reconcile_state.py
```

## Worktree Management

### Automatic Creation

The `create_worktree()` function in `helpers.py` automatically generates:

| Component | Pattern | Example |
|-----------|---------|---------|
| **Branch** | `feat/wo-{WO_ID}` | `feat/wo-WO-0013` |
| **Path** | `.worktrees/{WO_ID}` | `.worktrees/WO-0013` |

### Worktree Structure

```
.trifecta_dope/                    # Main repo
├── .worktrees/
│   ├── WO-0012/                   # Isolated environment for WO-0012
│   │   ├── .git                   # Git worktree metadata
│   │   └── [symlinks to main repo] # All repo files
│   └── WO-0013/                   # Isolated environment for WO-0013
│       ├── .git
│       └── [symlinks to main repo]
```

### Idempotent Creation

Calling `create_worktree()` multiple times is safe:
- First call: Creates new worktree and branch
- Subsequent calls: Detects existing worktree, returns same values
- Stale directories: Automatically cleaned up

## Lock Management

### Atomic Lock Pattern

Locks use the temp-rename pattern for filesystem atomicity:

```python
# From helpers.py
def create_lock(lock_path, wo_id):
    # 1. Create temp file with unique name
    temp_fd, temp_path = tempfile.mkstemp(prefix=f"{wo_id}.")

    # 2. Write metadata (PID, user, hostname, timestamp)
    with open(temp_path, "w") as f:
        f.write(f"Locked by ctx_wo_take.py at {datetime.now()}\n")
        f.write(f"PID: {os.getpid()}\n")
        f.write(f"User: {getpass.getuser()}\n")

    # 3. Atomic hard link (or rename fallback)
    try:
        os.link(temp_path, lock_path)  # Atomic
    except OSError:
        os.rename(temp_path, lock_path)  # Fallback
```

### Lock Metadata

Each lock contains:
```
Locked by ctx_wo_take.py at 2026-01-09T21:13:46.163816+00:00
PID: 48928
User: felipe_gonzalez
Hostname: MacBook-Pro-de-Felipe.local
```

### Stale Lock Detection

Locks older than 1 hour are considered stale:

```python
# Auto-cleaned by ctx_wo_take.py
if check_lock_age(lock_path, max_age_seconds=3600):
    logger.info("Found stale lock (>1 hour), removing")
    lock_path.unlink()
```

### Dependency Enforcement

Work Orders can declare dependencies that are validated before take:

```yaml
# WO-0013.yaml
dependencies:
  - WO-0012.1
  - WO-0012.2
```

**Behavior:**
- `ctx_wo_take.py` validates dependencies are in "done" state
- Clear error messages indicate blocking dependencies
- Use `--force` to override (not recommended)

**Analyze dependencies:**
```bash
python scripts/ctx_wo_dependencies.py --graph
python scripts/ctx_wo_dependencies.py --wo-id WO-0013 --list-blocking
```

### Transaction Rollback

All WO operations have automatic rollback on failure:

**Take Operations:**
1. Acquire lock → rollback: remove lock
2. Create worktree → rollback: remove worktree/branch
3. Move to running → rollback: move back to pending

**Example:**
```bash
python scripts/ctx_wo_take.py WO-0013
# If worktree creation fails:
# ✗ Failed to create worktree: [error]
# Executing rollback...
# ✓ Rollback completed
```

## Script Reference

### helpers.py

Core utilities for WO orchestration:

| Function | Purpose | Returns |
|----------|---------|---------|
| `get_branch_name(wo_id)` | Generate branch name | `"feat/wo-WO-XXXX"` |
| `get_worktree_path(wo_id, root)` | Generate worktree path | `Path(".worktrees/WO-XXXX")` |
| `create_worktree(root, wo_id)` | Create isolated git worktree | `(branch, path)` |
| `cleanup_worktree(root, wo_id)` | Remove worktree and branch | `bool` |
| `create_lock(lock_path, wo_id)` | Acquire atomic lock | `bool` |
| `check_lock_age(lock_path, max_age)` | Check if lock is stale | `bool` |
| `update_lock_heartbeat(lock_path)` | Update lock timestamp | `bool` |
| `check_lock_validity(lock_path)` | Check lock validity with PID | `(bool, metadata)` |
| `execute_rollback(transaction, root)` | Execute transaction rollback | `(bool, failed_ops)` |
| `list_worktrees(root)` | List all git worktrees | `list[dict]` |
| `run_command(cmd, cwd)` | Execute shell command | `CompletedProcess` |

### ctx_wo_take.py

Take a work order and create isolated worktree:

```bash
# Basic usage
python scripts/ctx_wo_take.py WO-0013

# With explicit owner
python scripts/ctx_wo_take.py WO-0013 --owner "developer"

# List pending WOs
python scripts/ctx_wo_take.py --list

# Show system status
python scripts/ctx_wo_take.py --status
```

**Flags:**
- `--root PATH`: Repository root (default: current directory)
- `--owner NAME`: Override owner (default: current user)
- `--list`: List pending work orders
- `--status`: Show system status and active worktrees
- `--force`: Skip dependency validation (not recommended)

### ctx_wo_finish.py

Complete a work order with DoD validation:

```bash
# Complete WO (runs DoD verification)
python scripts/ctx_wo_finish.py WO-0013

# Skip verification (not recommended)
python scripts/ctx_wo_finish.py WO-0013 --skip-verification
```

### ctx_reconcile_state.py

Repair state inconsistencies:

```bash
# Validate and repair all state
python scripts/ctx_reconcile_state.py

# Dry run (no changes)
python scripts/ctx_reconcile_state.py --dry-run
```

## Best Practices

### ✅ DO

1. **Always take WOs via script**: Never manually move YAML files
2. **Commit before finish**: Ensure all work is committed before `ctx_wo_finish.py`
3. **Use worktrees for isolation**: Don't work on main branch for WOs
4. **Check status daily**: Use `--status` to see active WOs
5. **Clean up stale worktrees**: Use `git worktree prune` periodically

### ❌ DON'T

1. **Don't edit WO YAMLs directly**: Use scripts for state transitions
2. **Don't skip DoD verification**: Use `--skip-verification` only in emergencies
3. **Don't share worktrees**: One WO per worktree
4. **Don't ignore locks**: Stale locks indicate interrupted work
5. **Don't delete worktrees manually**: Use `git worktree remove` or helpers

## Testing

The WO orchestration system has comprehensive test coverage:

```bash
# Run full test suite
python tests/test_wo_orchestration.py

# Test coverage includes:
# - Branch generation (feat/wo-WO-XXXX)
# - Worktree path generation (.worktrees/WO-XXXX)
# - Lock creation (atomic, with metadata)
# - Lock age detection (stale >1 hour)
# - Worktree creation (from main branch)
# - Worktree listing (git worktree list)
# - Idempotency (safe re-creation)
```

All 7 tests should pass:
```
✓ PASS: branch_generation
✓ PASS: worktree_path_generation
✓ PASS: lock_creation
✓ PASS: lock_age_detection
✓ PASS: worktree_creation
✓ PASS: worktree_list
✓ PASS: worktree_idempotency
```

## Related Documentation

- **[README.md](README.md)** - Overview and state machine
- **[OPERATIONS.md](OPERATIONS.md)** - Daily operations playbook
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions
- **[MIGRATION.md](MIGRATION.md)** - Legacy format migration

## Schema Reference

- **[work_order.schema.json](schema/work_order.schema.json)** - WO YAML validation
- **[backlog.schema.json](schema/backlog.schema.json)** - Epic registry validation
- **[dod.schema.json](schema/dod.schema.json)** - Definition of Done validation
