---
name: trifecta_dope
description: Use when working on Scope
---

# Trifecta_Dope

## Overview
Scope

## When to Use
Working on `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/trifecta_dope/`

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

### Stale Fail-Closed Protocol

If `ctx validate` fails or `stale_detected=true`:
- STOP immediately
- Run: `trifecta ctx sync --segment .` + `trifecta ctx validate --segment .`
- Log: "Stale: true -> sync+validate executed"
- Continue ONLY if PASS

## Common Mistakes
- Skipping session logging
- Using absolute paths outside segment
- Continuing with stale pack
- Silent fallback to Plan B

## Resources (On-Demand)
- `@_ctx/prime_trifecta_dope.md` - Reading list
- `@_ctx/agent.md` - Tech stack & gates
- `@_ctx/session_trifecta_dope.md` - Session log

---
**Profile**: `impl_patch` | **Updated**: 2026-03-06
