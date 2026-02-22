---
name: wo/create
description: Create new Work Orders with proper scope, DoD, and verification commands
---

# WO Create - Bootstrap and Preflight

## Overview

Create new WO YAMLs with valid configuration: scope, DoD, verify commands, and dependencies.

## When to Use

- Starting a new feature or fix
- Breaking down an epic into WOs
- Need isolated development environment

## Prerequisites

1. **Epic exists** in `_ctx/backlog/backlog.yaml`
2. **DoD selected** (default: `DOD-DEFAULT`)
3. **Scope defined** (allow/deny patterns)

## Process

### Step 1: Reference Closed WOs

Always check closed WOs for patterns:

```bash
# List recent completed WOs
ls -lt _ctx/jobs/done/*.yaml | head -5

# Read a reference WO
cat _ctx/jobs/done/WO-0054.yaml
```

**Good reference WOs**:
| WO | Why reference it |
|----|------------------|
| WO-0054 | Documentation integration (P2, clear scope) |
| WO-0053 | Security work (P1, specific scope) |
| WO-0051 | Linter work (P2, good verify commands) |
| WO-0041 | Contract implementation (P0, complete DoD) |
| WO-0012.1 | Dev tool (P1, dependencies) |

### Step 2: Verify Epic Exists

```bash
# Check epic in backlog
grep -A 5 "id: E-XXXX" _ctx/backlog/backlog.yaml

# Or list all epics
grep "id: E-" _ctx/backlog/backlog.yaml
```

If epic doesn't exist, use `--register-epic` flag or add manually.

### Step 3: Define Scope

**Scope Structure**:
```yaml
scope:
  allow:
    - src/domain/*.py
    - tests/unit/test_*.py
  deny:
    - .env*
    - '**/production.*'
    - _ctx/index/**
```

**Rules**:
- `allow`: Only these files can be modified
- `deny`: These files are ALWAYS blocked (security, config)
- Be **specific**: Avoid `**/*` - it defeats the purpose

### Step 4: Define Verify Commands

```yaml
verify:
  commands:
    - uv run pytest tests/unit/test_xxx.py -q
    - uv run ruff check src/domain/
```

**Best practices**:
- Use specific test files, not broad patterns
- Include lint and type checks
- Keep commands fast (< 60s)

### Step 5: Execute Bootstrap

```bash
# Dry-run first (validates without creating)
uv run python scripts/ctx_wo_bootstrap.py \
  --id WO-0099 \
  --epic E-0001 \
  --title "Feature description" \
  --priority P1 \
  --dod DOD-DEFAULT \
  --scope-allow "src/**" "tests/**" \
  --scope-deny ".env*" "_ctx/index/**" \
  --verify-cmd "uv run pytest" \
  --dry-run

# If validation passes, create
uv run python scripts/ctx_wo_bootstrap.py \
  --id WO-0099 \
  --epic E-0001 \
  --title "Feature description" \
  --priority P1 \
  --dod DOD-DEFAULT \
  --scope-allow "src/**" "tests/**" \
  --scope-deny ".env*" "_ctx/index/**" \
  --verify-cmd "uv run pytest"
```

### Step 6: Validate with Preflight

```bash
# Validate before take
uv run python scripts/ctx_wo_preflight.py WO-0099

# Check format
uv run python scripts/ctx_wo_fmt.py --check

# Lint
uv run python scripts/ctx_wo_lint.py --wo-id WO-0099 --strict
```

## WO YAML Structure

```yaml
version: 1
id: WO-XXXX
epic_id: E-XXXX
title: "Brief description"
priority: P1  # P0/P1/P2/P3
status: pending
owner: null
branch: null
worktree: null
scope:
  allow:
    - src/**
    - tests/**
  deny:
    - .env*
    - _ctx/index/**
verify:
  commands:
    - uv run pytest tests/unit/
dod_id: DOD-DEFAULT
execution:
  engine: trifecta
  required_flow:
    - session.append:intent
    - ctx.sync
    - ctx.search
    - ctx.get
    - implement
    - session.append:result
  segment: .
dependencies: []
```

## Common Mistakes

| Mistake | Why Bad | Fix |
|---------|---------|-----|
| `scope.allow: ["**/*"]` | Defeats purpose | Be specific |
| Missing verify commands | Can't validate | Add test commands |
| Unknown epic_id | Breaks registry | Create epic first |
| Wrong DoD ID | Fails finish | Check `_ctx/dod/` |
| Missing dependencies | Blocks execution | List blocking WOs |

## Resources

- `scripts/ctx_wo_bootstrap.py` - Main creation script
- `scripts/ctx_wo_preflight.py` - Pre-take validation
- `scripts/ctx_wo_fmt.py` - Format YAML
- `scripts/ctx_wo_lint.py` - Lint YAML
- `docs/backlog/schema/work_order.schema.json` - JSON schema
- `_ctx/jobs/done/` - Reference WOs
- `_ctx/dod/DOD-DEFAULT.yaml` - Default DoD

## Quick Reference

```bash
# Create new WO (dry-run)
uv run python scripts/ctx_wo_bootstrap.py \
  --id WO-XXXX --epic E-XXXX --title "Title" --priority P1 \
  --scope-allow "src/**" --scope-deny ".env*" \
  --verify-cmd "pytest" --dry-run

# Validate
uv run python scripts/ctx_wo_preflight.py WO-XXXX

# Format check
uv run python scripts/ctx_wo_fmt.py --check

# Lint
uv run python scripts/ctx_wo_lint.py --wo-id WO-XXXX --strict
```
