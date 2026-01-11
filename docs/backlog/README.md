# Backlog + Work Orders Pipeline

## Quick Start

```bash
# 1. List pending work orders
python scripts/ctx_wo_take.py --list

# 2. Take a work order (auto-creates branch + worktree)
python scripts/ctx_wo_take.py WO-XXXX

# 3. Navigate to isolated worktree
cd .worktrees/WO-XXXX

# 4. Work and commit normally
git add .
git commit -m "WO-XXXX: Implement feature"

# 5. Complete work order (validates DoD)
python scripts/ctx_wo_finish.py WO-XXXX
```

## Documentation

- **[WORKFLOW.md](WORKFLOW.md)** — Complete lifecycle guide (states, transitions, automation)
- **[OPERATIONS.md](OPERATIONS.md)** — Daily operations playbook (commands, workflows, CLI integration)
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** — Common issues and solutions (errors, recovery, diagnostics)
- **[MIGRATION.md](MIGRATION.md)** — Legacy format migration guide

## State machine

Work orders move through these states:

```
┌─────────┐     ┌─────────┐     ┌──────────┐     ┌─────────┐
│ PENDING │ ──▶ │ RUNNING │ ──▶ │   DONE   │     │ FAILED  │
└─────────┘     └─────────┘     └──────────┘     └─────────┘
```

- `pending` → `running` → `done`
- `pending` → `running` → `failed`

A WO can only be `done` when its DoD artifacts are complete.

## Traceability invariants

- `backlog.yaml` is canonical for epics and WO queue.
- Each WO in `_ctx/jobs/{pending,running,done,failed}` must reference a valid `epic_id` and `dod_id`.
- Every WO must define `scope.allow` and `scope.deny` plus `verify.commands`.
- Context pack sources live under `_ctx/`; legacy stubs such as `_ctx/blacklog/README.md` are non-canonical.

## Rollback

- All changes are additive; rollback is a git revert.
- If state diverges (locks/worktrees), use `scripts/ctx_reconcile_state.py` to repair before any manual edits.

## Scripts Reference

### Core Orchestration

| Script | Purpose | Key Features |
|--------|---------|--------------|
| **helpers.py** | Core utilities | Worktree creation, lock management, branch generation |
| **ctx_wo_take.py** | Take WO | Auto branch (`feat/wo-WO-XXXX`), auto worktree (`.worktrees/WO-XXXX`), atomic lock |
| **ctx_wo_finish.py** | Complete WO | DoD validation, SHA capture, status transition |
| **ctx_reconcile_state.py** | Repair state | Fix inconsistencies, prune stale references |

### Validation

| Script | Purpose |
|--------|---------|
| **ctx_backlog_validate.py** | Validate YAML schemas against JSON schemas |

### Usage Examples

```bash
# List pending WOs
python scripts/ctx_wo_take.py --list

# Show system status (pending/running/done counts, active worktrees)
python scripts/ctx_wo_take.py --status

# Take WO with auto-generated branch and worktree
python scripts/ctx_wo_take.py WO-0013

# Take WO with explicit owner
python scripts/ctx_wo_take.py WO-0013 --owner "developer"

# Complete WO (runs DoD verification)
python scripts/ctx_wo_finish.py WO-0013

# Validate all WOs
python scripts/ctx_backlog_validate.py --strict

# Repair state inconsistencies
python scripts/ctx_reconcile_state.py
```

## Architecture

### Worktree Management

Each WO gets an isolated git worktree:

```
.trifecta_dope/
├── .worktrees/
│   ├── WO-0012/          # Isolated environment
│   │   └── [symlinks to main repo]
│   └── WO-0013/          # Another isolated environment
│       └── [symlinks to main repo]
```

**Automatic generation:**
- Branch: `feat/wo-WO-XXXX` (from `main`)
- Path: `.worktrees/WO-XXXX`

### Lock Management

Atomic locks prevent concurrent access:

```
_ctx/jobs/running/
├── WO-0013.lock         # Contains: PID, user, hostname, timestamp
└── WO-0013.yaml         # WO metadata (moved from pending/)
```

**Stale lock detection:** Locks >1 hour old are auto-cleaned.

## Directory Structure

```
_ctx/
├── backlog/
│   └── backlog.yaml          # Epic registry (canonical)
├── jobs/
│   ├── pending/              # WOs awaiting work
│   ├── running/              # WOs in progress (+ locks)
│   ├── done/                 # Completed WOs (with verified_at_sha)
│   └── failed/               # Failed WOs
└── dod/                      # Definition of Done catalog
    ├── DOD-DEFAULT.yaml
    └── DOD-XXXX.yaml
```

## Schema Validation

All WOs must validate against JSON schemas:

| Schema | Purpose |
|--------|---------|
| **work_order.schema.json** | WO YAML structure |
| **backlog.schema.json** | Epic registry structure |
| **dod.schema.json** | Definition of Done structure |

Validate with:
```bash
python scripts/ctx_backlog_validate.py --strict
```

## Integration with Trifecta CLI

The WO system integrates seamlessly with the Trifecta CLI:

```bash
# Inside a worktree, sync context
make ctx-sync SEGMENT=.

# Search documentation
make ctx-search Q="Find telemetry implementation" SEGMENT=.

# Navigate AST symbols
uv run trifecta ast symbols "sym://python/mod/src.domain.result" --segment .
```

See [OPERATIONS.md](OPERATIONS.md) for complete CLI integration guide.

## Testing

The WO orchestration system has comprehensive test coverage:

```bash
# Run full test suite
python tests/test_wo_orchestration.py
```

All 7 tests verify:
- Branch generation (`feat/wo-WO-XXXX`)
- Worktree path generation (`.worktrees/WO-XXXX`)
- Lock creation (atomic with metadata)
- Lock age detection (stale >1 hour)
- Worktree creation (from `main` branch)
- Worktree listing (git worktree list)
- Idempotency (safe re-creation)

## Best Practices

✅ **DO:**
- Always use `ctx_wo_take.py` to start WOs (never manually move YAMLs)
- Commit work before running `ctx_wo_finish.py`
- Stay within WO scope (`allow`/`deny` patterns)
- Run `--status` daily to check active WOs
- Clean up worktrees periodically with `git worktree prune`

❌ **DON'T:**
- Edit WO YAMLs directly (use scripts for state transitions)
- Skip DoD verification (use `--skip-verification` only in emergencies)
- Share worktrees between WOs (one WO per worktree)
- Ignore locks (stale locks indicate interrupted work)
- Delete worktrees manually (use `git worktree remove` or helpers)

## Related Documentation

- **[WORKFLOW.md](WORKFLOW.md)** — Complete lifecycle guide
- **[OPERATIONS.md](OPERATIONS.md)** — Daily operations playbook
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** — Common issues and solutions
- **[MIGRATION.md](MIGRATION.md)** — Legacy format migration
