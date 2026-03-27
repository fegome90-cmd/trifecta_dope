---
name: trifecta_dope
description: Use when working on the Trifecta repository and its segment-level context workflow.
---

# Trifecta_Dope

## Overview
Operational runbook for this repository's context workflow.

## When to Use
Working on `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/`

## Core Pattern

### Session Evidence Persistence (5 Steps)

1) **Persist intention**
```bash
trifecta session append --segment . --summary "<action>" --files "<csv>" --commands "<csv>"
```

2) **Sync context**
```bash
trifecta ctx sync --segment .
```

3) **Read session state**
- Confirm the objective in `_ctx/session_trifecta_dope.md`

4) **Execute one context cycle**
```bash
trifecta ctx search --segment . --query "<topic>" --limit 6
trifecta ctx get --segment . --ids "<id1>,<id2>" --mode excerpt --budget-token-est 900
```

5) **Log result**
```bash
trifecta session append --segment . --summary "Completed <task>" --files "<touched>" --commands "<executed>"
```

### Stale Fail-Closed Protocol

If `ctx validate` fails or `stale_detected=true`:
- STOP immediately
- Run:
```bash
trifecta ctx sync --segment .
trifecta ctx validate --segment .
```
- Log: `Stale: true -> sync+validate executed`
- Continue only if validation passes

### Context Lookup Priority

**Rule: `skill-hub` for skills, `trifecta ctx` for context packs**

| Purpose | Tool | Notes |
|---------|------|-------|
| Find a skill | `skill-hub "<query>"` | Discovery, fuzzy matching, usage hints |
| Search repo context | `trifecta ctx search` | Find chunks |
| Retrieve evidence | `trifecta ctx get` | Prefer `mode=excerpt` |
| Refresh pack | `trifecta ctx sync` | Build + validate |
| Health check | `trifecta ctx validate` | Fail-closed gate |

Do not use `trifecta ctx` to discover skills.

## Current Operational Notes
- Canonical package manager and task runner: `uv`
- Canonical Python gates: `uv run pytest`, `uv run ruff`, `uv run mypy`
- Review flows such as `branch-review` / `reviewctl` must run from a clean isolated branch/worktree, not from dirty `main`
- Session history is append-only in `_ctx/session_trifecta_dope.md`

## Common Mistakes
- Skipping `trifecta session append`
- Continuing after failed `ctx validate`
- Treating `session` as editable summary instead of append-only evidence
- Mixing review/PR workflows into a dirty worktree
- Using `git add .` or `git add -A`

## Resources
- `README.md` — human onboarding and project overview
- `_ctx/agent_trifecta_dope.md` — active technical state, stack, gates
- `_ctx/prime_trifecta_dope.md` — prioritized reading list
- `_ctx/session_trifecta_dope.md` — append-only session log

---
**Profile**: `impl_patch` | **Updated**: 2026-03-27
