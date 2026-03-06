---
name: ctx-md-sync
description: Synchronize context pack after editing Trifecta MD files. Triggers when user says "ctx sync", "hash mismatch", "stale pack", "validate context", or edits skill.md, agent_*.md, session_*.md, prime_*.md files.
---

# MD Synchronization for Trifecta Context Files

## Overview

Maintain Trifecta context files synchronized with the context pack.

> **Why it matters**: A stale context pack causes `ctx search` to return zero results or outdated content, breaking the progressive disclosure workflow.

## Files Tracked

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `skill.md` | Onboarding + rules | Rare (major changes) |
| `_ctx/agent_*.md` | Tech stack + gates | After dep changes |
| `_ctx/session_*.md` | Session log | Every session |
| `_ctx/prime_*.md` | Entry points | After structure changes |

## Core Rules

### 1. POST-EDIT SYNC (Required)

After editing ANY tracked file, execute:

```bash
uv run trifecta ctx sync --segment .
```

### 2. PRE-WORK VALIDATE (Required)

Before starting work on a segment, execute:

```bash
uv run trifecta ctx validate --segment .
```

### 3. STALE FAIL-CLOSED Protocol

If ctx validate fails with hash mismatch:

1. **STOP** - Do not continue with other commands
2. **SYNC** - Execute `uv run trifecta ctx sync --segment .`
3. **RE-VALIDATE** - Execute `uv run trifecta ctx validate --segment .`
4. **CONTINUE** - Only if validation passes

## Common Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| Edit MD without sync | Hash mismatch on validate | Execute ctx sync |
| Skip validate before search | Stale pack, 0 hits returned | Always validate first |
| Long session.md | Pack size >3MB, slow ops | Archive old entries |
| Commit without sync | CI fails validation | Ensure pre-commit hooks enabled |

## Quick Reference

| Command | Purpose |
|---------|---------|
| `make ctx-sync SEGMENT=.` | Sync context pack (Makefile) |
| `uv run trifecta ctx validate --segment .` | Check sync status |
| `uv run trifecta ctx sync --segment .` | Full sync + validate |

## Prevention Checklist

- [ ] After editing MD files → execute ctx sync
- [ ] Before ctx search → execute ctx validate
- [ ] Session.md > 50KB → consider archiving
- [ ] Pre-commit hooks enabled → auto-validation on commit

---
**Profile**: impl_patch | **Updated**: 2026-02-22 | **Verified Against**: trifecta CLI v2.0, skill-creator v1.8.0
