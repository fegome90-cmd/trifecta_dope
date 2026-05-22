---
name: trifecta_dope
description: Use when working on Scope
---

# Trifecta_Dope

## Overview
Scope

## When to Use
Working on `./trifecta_dope/`

## Core Pattern

### Session Evidence Persistence (5 Steps)

1) **Persist intention** (CLI proactive):
```bash
trifecta session append --segment . --summary "<action>" --files "<csv>" --commands "<csv>"
```

2) **Sync context**:
```bash
trifecta ctx sync --segment .
```

3) **Read** session.md (confirm objective logged)

4) **Execute** context cycle:
```bash
trifecta ctx search --segment . --query "<topic>" --limit 6
trifecta ctx get --segment . --ids "<id1>,<id2>" --mode excerpt --budget-token-est 900
```

5) **Log result**:
```bash
trifecta session append --segment . --summary "Completed <task>" --files "<touched>" --commands "<executed>"
```

### Mandatory Validation Protocol (Law V)

**STALE FAIL-CLOSED**: If `ctx validate` fails or `stale_detected=true`:
- **STOP** immediately. Do NOT guess.
- Run: `trifecta ctx sync --segment .` + `trifecta ctx validate --segment .`
- Continue ONLY if state is **VALID**.
- **Evidence**: All mutations MUST be followed by a verification command.

## Common Mistakes
- Skipping session logging (Law I violation)
- Writing before reading (Law II violation)
- Continuing with stale pack (Law VI violation)
- Model-specific bias in naming (Law VII violation)

## Resources (On-Demand)
- `@_ctx/prime_trifecta_dope.md` - Reading list
- `@_ctx/agent_trifecta_dope.md` - Tech stack & gates
- `@_ctx/session_trifecta_dope.md` - Session log

---
**Profile**: `impl_patch` | **Updated**: 2026-03-06
