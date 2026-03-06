---
description: Run ctx sync + validate to fix stale context pack. Use when ctx search returns 0 results or after editing skill.md, agent/session/prime files.
---

# /ctx-md-sync - Sync Context Markdown Files

Synchronize Trifecta context files with the context pack.

> **Why it matters**: A stale pack causes `ctx search` to return zero results or outdated content.

## Usage

```
/ctx-md-sync
```

## What It Does

1. Validates current pack integrity
2. Syncs all tracked MD files to the pack
3. Re-validates and confirms PASS

## Files Tracked

| File | Purpose |
|------|---------|
| `skill.md` | Onboarding + rules |
| `_ctx/agent_*.md` | Tech stack + gates |
| `_ctx/session_*.md` | Session log |
| `_ctx/prime_*.md` | Entry points |

## Pipeline

### Step 1: Validate Current State

```bash
uv run trifecta ctx validate --segment .
```

### Step 2: Sync

```bash
uv run trifecta ctx sync --segment .
```

### Step 3: Verify

```bash
uv run trifecta ctx validate --segment .
```

## Required Output

```
=== CTX-MD-SYNC ===

1. Pre-sync validate:
   - Status: PASS/FAIL
   - If FAIL: hash mismatch details

2. Sync executed:
   - Files processed: X
   - Pack size: Y chars

3. Post-sync validate:
   - Status: PASS

=== SYNC COMPLETE ===
```

## STALE FAIL-CLOSED Protocol

If validation fails:

1. **STOP** - Do not run other commands
2. **SYNC** - Execute ctx sync
3. **RE-VALIDATE** - Must pass before continuing
4. **LOG** - Note in session.md if stale was detected

## When to Use

- After editing any tracked MD file
- Before ctx search commands
- When ctx validate reports errors
- At session start to verify integrity

## Example

```
> /ctx-md-sync

=== CTX-MD-SYNC ===

1. Pre-sync validate:
   - Status: FAIL
   - Hash mismatch: session_trifecta_dope.md

2. Sync executed:
   - Files processed: 4
   - Pack size: 3303769 chars

3. Post-sync validate:
   - Status: PASS

=== SYNC COMPLETE ===
```

## Related

- Skill: `ctx-md-sync` (detailed rules and troubleshooting)
- Command: `/ctx-md-sync` (quick execution wrapper)
