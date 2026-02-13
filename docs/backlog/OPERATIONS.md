# Work Order Operations Playbook

Daily operations guide for working with Trifecta Dope Work Orders.

## Quick Reference

```bash
# Start of day
python scripts/ctx_wo_take.py --list      # See pending WOs
python scripts/ctx_wo_take.py --status    # Check system status

# Take a WO
python scripts/ctx_wo_take.py WO-XXXX     # Start work

# Inside worktree
cd .worktrees/WO-XXXX
# ... work ...

# End of day
python scripts/ctx_wo_finish.py WO-XXXX   # Complete WO
```

## WO Hygiene Quickstart

```bash
# 1) Lint WO contracts (strict)
make wo-lint

# 2) Emit machine-readable findings
make wo-lint-json

# 3) Check canonical format (no writes)
make wo-fmt-check

# 4) Apply canonical format
make wo-fmt

# 5) Run full verification gate (includes WO fail-closed)
bash scripts/verify.sh --check-only
```

## Daily Workflow

### Morning Routine

**1. Check system status:**
```bash
python scripts/ctx_wo_take.py --status
```

Output:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   System Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Pending:   3
  Running:   1
  Done:      15
  Failed:    0

Active worktrees:
  /Users/felipe/trifecta_dope/.worktrees/WO-0013  feat/wo-WO-0013
```

**2. Review pending work orders:**
```bash
python scripts/ctx_wo_take.py --list
```

Output:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Pending Work Orders
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  WO-0004 [P2] - Implement feature flag system
  WO-0005 [P1] - Fix telemetry race condition
  WO-0013 [P2] - AST Persist Adoption Observability

Total: 3
```

**3. Select a WO to work on:**
```bash
python scripts/ctx_wo_take.py WO-0013
```

### During Work

**Navigate to worktree:**
```bash
cd .worktrees/WO-0013
```

**Check your environment:**
```bash
# Verify branch
git branch
# * feat/wo-WO-0013

# Verify worktree
git worktree list
# /Users/felipe/trifecta_dope              main
# /Users/felipe/trifecta_dope/.worktrees/WO-0013  feat/wo-WO-0013
```

**Sync Trifecta context:**
```bash
make ctx-sync SEGMENT=.
```

**Search documentation:**
```bash
# Instruction-based search (RECOMMENDED)
make ctx-search Q="Find documentation about AST persistence implementation" SEGMENT=.

# Get specific chunks
uv run trifecta ctx get --segment . --ids "prime:abc123,doc:design_p2" --mode excerpt
```

**Navigate AST symbols:**
```bash
# List symbols in a module
uv run trifecta ast symbols "sym://python/mod/src.domain.result" --segment .

# View cache stats
uv run trifecta ast cache-stats --segment .
```

**Normal git workflow:**
```bash
# Make changes
vim src/infrastructure/cache.py

# Stage and commit
git add src/infrastructure/cache.py
git commit -m "WO-0013: Implement AST persistence cache"

# Push to remote (optional)
git push -u origin feat/wo-WO-0013
```

### End of Day

**Verify work is complete:**
```bash
# Check git status
git status
# Should show: "nothing to commit, working tree clean"

# Run tests
uv run pytest tests/unit/test_cache.py -v

# Run DoD verification commands (from WO YAML)
# Example: make gate-all
```

**Complete the WO:**
```bash
python scripts/ctx_wo_finish.py WO-0013
```

Output:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Work Order WO-0013 Completed
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Status: done
  Verified at: c2d0338f1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p
  Closed at: 2026-01-09T21:30:00+00:00
```

## Command Reference

### ctx_wo_take.py

**Take a work order:**
```bash
python scripts/ctx_wo_take.py WO-XXXX
```

**With explicit owner:**
```bash
python scripts/ctx_wo_take.py WO-XXXX --owner "developer-name"
```

**List pending WOs:**
```bash
python scripts/ctx_wo_take.py --list
```

**Show system status:**
```bash
python scripts/ctx_wo_take.py --status
```

**Flags:**
| Flag | Purpose | Default |
|------|---------|---------|
| `--root PATH` | Repository root | `.` (current directory) |
| `--owner NAME` | Set owner explicitly | Current user |
| `--list` | List pending WOs | - |
| `--status` | Show system status | - |
| `--force` | Skip domain dependency gate only (does NOT bypass immediate schema/lint validation) | - |

### ctx_wo_finish.py

**Complete WO with verification:**
```bash
python scripts/ctx_wo_finish.py WO-XXXX
```

**Skip verification (emergency only):**
```bash
python scripts/ctx_wo_finish.py WO-XXXX --skip-verification
```

**What happens:**
1. Runs DoD verification commands from WO YAML
2. Captures current commit SHA
3. Moves WO from `running/` to `done/`
4. Removes lock
5. Updates epic status in `backlog.yaml`

### git worktree

**List all worktrees:**
```bash
git worktree list
```

**Remove specific worktree:**
```bash
git worktree remove .worktrees/WO-XXXX
```

**Prune stale references:**
```bash
git worktree prune
```

**Move worktree:**
```bash
git worktree move /old/path /new/path
```

### Trifecta CLI Integration

**Sync context pack:**
```bash
make ctx-sync SEGMENT=.
# OR
uv run trifecta ctx sync --segment .
```

**Search documentation:**
```bash
# Using Makefile wrapper
make ctx-search Q="Instruction describing what you need" SEGMENT=.

# Direct CLI
uv run trifecta ctx search --segment . --query "Instruction..." --limit 5
```

**Get context chunks:**
```bash
# Excerpt mode (recommended for preview)
uv run trifecta ctx get --segment . --ids "id1,id2" --mode excerpt --budget-token-est 900

# Full mode (for detailed reading)
uv run trifecta ctx get --segment . --ids "id1,id2" --mode full
```

**View telemetry:**
```bash
# Last 7 days
uv run trifecta telemetry report -s . --last 7

# Chart hits
uv run trifecta telemetry chart -s . --type hits
```

## Multiple WOs

### Handling Multiple Active WOs

You can have multiple WOs in `running` state simultaneously:

```bash
# Take first WO
python scripts/ctx_wo_take.py WO-0012
cd .worktrees/WO-0012
# ... work on WO-0012 ...

# Return to main repo
cd ../..

# Take second WO
python scripts/ctx_wo_take.py WO-0013
cd .worktrees/WO-0013
# ... work on WO-0013 ...
```

**Switch between worktrees:**
```bash
# From anywhere
cd /path/to/trifecta_dope/.worktrees/WO-0012
# OR
cd /path/to/trifecta_dope/.worktrees/WO-0013
```

**Dependencies management:**

If WO-0013 depends on WO-0012:
```yaml
# WO-0013.yaml
dependencies:
  - WO-0012
```

Best practice: Complete WO-0012 before starting WO-0013.

## Dependency Management

**View dependency graph:**
```bash
python scripts/ctx_wo_dependencies.py --graph
```

**Check WO dependencies:**
```bash
# What's blocking this WO?
python scripts/ctx_wo_dependencies.py --wo-id WO-0013 --list-blocking

# What does this WO block?
python scripts/ctx_wo_dependencies.py --wo-id WO-0012 --list-blocked
```

**Analyze all pending WOs:**
```bash
python scripts/ctx_wo_dependencies.py
```

## Transaction Recovery

**Check for orphaned resources:**
```bash
python scripts/ctx_reconcile_state.py --apply
```

**Manual rollback:**
```bash
# Remove stale lock
rm _ctx/jobs/running/WO-XXXX.lock

# Move WO back to pending
mv _ctx/jobs/running/WO-XXXX.yaml _ctx/jobs/pending/
```

## Monitoring

### Check WO Progress

**Per-epic progress:**
```bash
# Edit _ctx/backlog/backlog.yaml
epics:
  - id: E-0001
    title: "Core Infrastructure"
    wo_queue: [WO-0012, WO-0013, WO-0014]
    phase: "implementation"
    phase_sha: "abc123"  # Updated when phase complete
```

**System-wide status:**
```bash
python scripts/ctx_wo_take.py --status

# Output shows:
# - Pending count
# - Running count
# - Done count
# - Failed count
# - Active worktrees
```

### Telemetry Integration

**View CLI usage:**
```bash
uv run trifecta telemetry report -s . --last 30
```

**Track context searches:**
```bash
# Most searched topics
uv run trifecta telemetry chart -s . --type search --last 7
```

**Monitor AST cache:**
```bash
# Cache hit rate
uv run trifecta ast cache-stats --segment .
```

## Scope Enforcement

Each WO defines allowed and denied paths:

```yaml
# WO-0013.yaml
scope:
  allow:
    - "docs/reports/wo0013_report.md"
    - "scripts/analyze_adoption_telemetry.py"
  deny:
    - "src/domain/**"
```

**What this means:**
- You CAN edit files matching `allow` patterns
- You CANNOT edit files matching `deny` patterns
- This is enforced during DoD verification

**Check your WO's scope:**
```bash
# View WO YAML
cat _ctx/jobs/running/WO-0013.yaml | grep -A 5 scope
```

## Session Persistence

**Log work in session.md:**
```bash
uv run trifecta session append --segment . \
  --summary "Working on WO-0013: AST persistence adoption" \
  --files "src/infrastructure/cache.py,tests/unit/test_cache.py" \
  --commands "ctx search,ctx get,ast symbols"
```

**Why this matters:**
- Maintains context between sessions
- Provides audit trail
- Helps other agents understand progress

## Best Practices

### Start of Day
1. Run `--status` to see active WOs
2. Run `--list` to see pending work
3. Select WO based on priority and dependencies
4. Take WO with `ctx_wo_take.py`

### During Work
1. Stay within WO scope (allow/deny patterns)
2. Commit frequently with descriptive messages
3. Use Trifecta CLI for context search
4. Log session updates for complex tasks

### End of Day
1. Verify all tests pass
2. Ensure clean git status
3. Complete WO with `ctx_wo_finish.py`
4. Update session.md with summary

### Weekly
1. Review done/failed WOs
2. Clean up stale worktrees (`git worktree prune`)
3. Update epic phases in `backlog.yaml`
4. Check telemetry for usage patterns

## Common Scenarios

### Scenario 1: Quick Fix

```bash
# 1. List and select
python scripts/ctx_wo_take.py --list
python scripts/ctx_wo_take.py WO-0005

# 2. Navigate and fix
cd .worktrees/WO-0005
vim src/bug_fix.py
git commit -am "WO-0005: Fix race condition"

# 3. Complete
python scripts/ctx_wo_finish.py WO-0005
```

### Scenario 2: Multi-Day Feature

```bash
# Day 1: Start WO
python scripts/ctx_wo_take.py WO-0013
cd .worktrees/WO-0013
# Work, commit, leave for tomorrow

# Day 2: Continue
cd .worktrees/WO-0013
# Continue work, commit

# Day 3: Complete
make gate-all
python scripts/ctx_wo_finish.py WO-0013
```

### Scenario 3: Blocked WO

```bash
# WO-0013 is blocked by WO-0012
# Option 1: Complete WO-0012 first
python scripts/ctx_wo_take.py WO-0012
# ... complete WO-0012 ...
python scripts/ctx_wo_finish.py WO-0012

# Then take WO-0013
python scripts/ctx_wo_take.py WO-0013

# Option 2: Update dependencies if incorrect
# Edit WO-0013.yaml to remove false dependency
```

## Related Documentation

- **[WORKFLOW.md](WORKFLOW.md)** - Complete lifecycle guide
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions
- **[README.md](README.md)** - Overview and state machine
- **[MIGRATION.md](MIGRATION.md)** - Legacy format migration

## Tips and Tricks

### Speed Up Context Search

```bash
# Use Makefile wrapper (faster)
make ctx-search Q="..." SEGMENT=.

# Limit results for faster searches
uv run trifecta ctx search --segment . --query "..." --limit 3
```

### Quick Worktree Navigation

```bash
# Add to .bashrc or .zshrc
alias wo-list='git worktree list'
alias wo-cd='cd $(git worktree list | grep -o "/.worktrees/[^ ]*" | fzf)'
```

### Batch Operations

```bash
# List all running WOs
ls _ctx/jobs/running/WO-*.yaml

# Check status of all running WOs
for wo in _ctx/jobs/running/WO-*.yaml; do
  echo "Status of $(basename $wo .yaml):"
  python scripts/ctx_wo_take.py --status
done
```
