---
description: Complete WO with DoD validation (verify + artifacts + close)
---

# /wo-finish - Complete Work Order

Close a WO with full DoD validation and artifact generation.

## Usage

```
/wo-finish WO-XXXX [--bypass=skip-dod|skip-verify|all]
```

## Pipeline

1. **wo/guard PRE-FINISH** - Verify worktree, branch, lock, markers, repo clean
2. **wo/finish** - Run verify/gates, DoD, generate artifacts

## Guard Checks (PRE-FINISH)

| Check | Expected |
|-------|----------|
| Worktree | Contains `.worktrees/WO-XXXX` |
| Branch | `feat/wo-WO-XXXX` |
| Lock | Exists in `running/` |
| Session markers | `[WO-XXXX] intent:` AND `result:` |
| Repo clean | `git status --porcelain` empty |

## If Guard Fails

STOP, diagnose, fix. Do not proceed until guard passes.

## Required Output

```
=== WO-XXXX FINISH ===

1. Guard PRE-FINISH: PASS
2. Verify commands: PASS
3. DoD artifacts: 5/5
4. Close: PASS

FINAL STATE: done
ARTIFACTS: _ctx/handoff/WO-XXXX/
```

## Process

### Step 0: Guard PRE-FINISH

```bash
# Verify in worktree
git rev-parse --show-toplevel | grep ".worktrees"

# Verify correct branch
git branch --show-current | grep "feat/wo-WO-XXXX"

# Verify clean
git status --porcelain

# Verify BOTH markers exist
grep "\[WO-XXXX\] intent:" _ctx/session.md
grep "\[WO-XXXX\] result:" _ctx/session.md
```

### Step 1: Run Verify Commands

```bash
# From WO YAML
grep -A 5 "verify:" _ctx/jobs/running/WO-XXXX.yaml

# Execute each
uv run pytest tests/unit/test_xxx.py
uv run ruff check src/
```

### Step 2: Log Result (if not done)

```bash
trifecta session append --segment . \
  --summary "[WO-XXXX] result: <what was completed>"
```

### Step 3: Execute Finish

```bash
uv run python scripts/ctx_wo_finish.py WO-XXXX --result done
```

### Step 4: Verify Artifacts

```bash
ls _ctx/handoff/WO-XXXX/
# tests.log, lint.log, diff.patch, handoff.md, verdict.json
```

## Emergency Bypass

**ONLY use bypass for genuine emergencies.**

### Bypass Requires INCIDENT NOTE

**Before using `--bypass`, you MUST create:**

```markdown
# INCIDENT-WO-XXXX-YYYY-MM-DD

## Motivo
[Why bypass is needed]

## Impacto
[What is skipped, risks]

## Plan de Remediación
[How to fix later]

## Autorización
[Who approved]
```

### Fail-Closed Rule

If `--skip-*` is requested AND `_ctx/incidents/INCIDENT-WO-XXXX-...md` does not exist → **STOP**.

### Bypass Commands

```bash
# Create incident note first!
mkdir -p _ctx/incidents
cat > _ctx/incidents/INCIDENT-WO-XXXX-$(date +%Y-%m-%d).md << 'EOF'
# INCIDENT-WO-XXXX

## Motivo
...

## Impacto
...

## Plan de Remediación
...

## Autorización
...
EOF

# Then bypass
uv run python scripts/ctx_wo_finish.py WO-XXXX --result done --skip-dod
```

### Bypass Output

```
BYPASS_USED=true
INCIDENT_NOTE=_ctx/incidents/INCIDENT-WO-XXXX-2026-02-22.md
FOLLOWUP_REQUIRED=true
```

## Example

```
> /wo-finish WO-0055

=== WO-0055 FINISH ===

1. Guard PRE-FINISH...
   - Worktree: PASS (.worktrees/WO-0055)
   - Branch: PASS (feat/wo-WO-0055)
   - Lock: PASS
   - Markers: PASS ([WO-0055] intent:, result:)
   - Repo clean: PASS

2. Verify commands...
   - pytest: PASS (12 tests)
   - ruff: PASS

3. DoD artifacts...
   - tests.log: ✓
   - lint.log: ✓
   - diff.patch: ✓
   - handoff.md: ✓
   - verdict.json: ✓

4. Closing...
   - SHA: abc1234
   - State: done
   - Moved to: _ctx/jobs/done/WO-0055.yaml

=== COMPLETE ===
FINAL STATE: done
ARTIFACTS: _ctx/handoff/WO-0055/
```

## Bypass Example

```
> /wo-finish WO-0055 --bypass=skip-dod

⚠️ BYPASS REQUESTED

Checking for INCIDENT NOTE...
  _ctx/incidents/INCIDENT-WO-0055-2026-02-22.md: FOUND

Proceeding with bypass...

BYPASS_USED=true
INCIDENT_NOTE=_ctx/incidents/INCIDENT-WO-0055-2026-02-22.md
FOLLOWUP_REQUIRED=true

=== COMPLETE (with bypass) ===
```
