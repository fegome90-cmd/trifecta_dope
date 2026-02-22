---
name: wo/work
description: Rules for working inside a WO worktree (isolation, commits, controlled drift)
---

# WO Work - Working Rules

## Overview

Rules for working inside a WO worktree. These rules ensure isolation, traceability, and clean state.

## When to Use

- After taking a WO (`/wo-start`)
- During development work
- Before commits

## Working Rules

### Rule 1: Stay in the Worktree

**ALWAYS** work in `.worktrees/WO-XXXX/`, NEVER in main repo.

```bash
# Verify you're in worktree
git worktree list --porcelain | grep -A2 "$(pwd)" | grep "branch feat/wo"
```

### Rule 2: Stay in Scope

**ONLY** modify files in `scope.allow`:

```bash
# Check your scope
grep -A 10 "scope:" _ctx/jobs/running/WO-XXXX.yaml

# Verify files before commit
git diff --name-only
```

**If a file is NOT in scope.allow**:
1. STOP
2. Either: Update scope (requires new WO or scope change)
3. Or: Don't modify that file

### Rule 3: Small, Frequent Commits

```bash
# Good: Small commits
git add src/domain/feature.py
git commit -m "feat(WO-XXXX): add feature X"

# Bad: Large commits
git add .
git commit -m "lots of changes"
```

### Rule 4: Controlled Drift (NOT Absolute Prohibition)

**Absolute prohibition causes worse workarounds.** Sometimes you need changes from main (hotfix, compatibility).

**Allowed IF**:
1. Run `wo/guard` first
2. Log explicit decision in session:
   ```
   [WO-XXXX] note: drift introduced because <reason>
   ```
3. Run `verify` before continuing

```bash
# If you MUST bring changes from main
# 1. Guard check
wo/guard PRE-COMMIT

# 2. Merge/rebase
git merge main --no-ff
# or
git rebase main

# 3. Log decision
trifecta session append --segment . \
  --summary "[WO-XXXX] note: drift introduced because <specific reason>"

# 4. Verify
uv run pytest tests/
```

**If drift causes problems**: Consider creating a new WO instead.

### Rule 5: Session Append After Changes

After each significant change, log it:

```bash
trifecta session append --segment . \
  --summary "Completed: <what you did>" \
  --files "<files modified>" \
  --commands "<commands run>"
```

## Prohibited Actions

| Action | Why Prohibited | Alternative |
|--------|----------------|-------------|
| Working in main repo | Breaks isolation | Use worktree |
| Modifying `scope.deny` files | Security/policy | Request exception |
| Large commits | Hard to review | Small commits |
| Skipping session logs | Loses traceability | Always log |
| Drift without logging | Invisible state | Log + verify |

## Session Markers

**Required format**:

```
[WO-XXXX] intent: <what you plan to do>
[WO-XXXX] result: <what you actually did>
[WO-XXXX] note: <any significant decisions (optional)>
```

**When to add**:
- **Intent**: Immediately after taking WO
- **Result**: After completing work, before finish
- **Note**: When making significant decisions (drift, scope changes)

**Validation**: `wo/guard` checks for intent AND result markers before allowing finish.

## Daily Workflow

```bash
# 1. Navigate to worktree
cd .worktrees/WO-XXXX

# 2. Sync context
uv run trifecta ctx sync --segment .

# 3. Make changes (stay in scope!)
# ... edit files ...

# 4. Run tests
uv run pytest tests/unit/test_xxx.py

# 5. Commit
git add src/ tests/
git commit -m "feat(WO-XXXX): description"

# 6. Log progress
trifecta session append --segment . --summary "Progress: ..."

# 7. Repeat 3-6

# 8. When done, run /wo-finish
```

## Resources

- `docs/backlog/WORKFLOW.md` - Full workflow
- `docs/backlog/OPERATIONS.md` - Daily operations
- `_ctx/jobs/running/WO-XXXX.yaml` - Your WO config

## Quick Reference

```bash
# Check you're in worktree
git worktree list --porcelain | grep -A2 "$(pwd)"

# Check scope
grep -A 5 "scope:" ../_ctx/jobs/running/WO-XXXX.yaml

# Check modified files
git diff --name-only

# Session log
trifecta session append --segment . --summary "Progress update"

# If drift needed
trifecta session append --segment . --summary "[WO-XXXX] note: drift because ..."
```

## Required Output

After completing work session:

```
ACTIVE_WO=WO-XXXX
CWD=/path/.worktrees/WO-XXXX
BRANCH=feat/wo-WO-XXXX
STATE=running
NEXT_ALLOWED=["commit","session append","run verify","/wo-finish","/wo-repair"]
```
