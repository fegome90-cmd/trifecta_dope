# CLAUDE.md

This file provides guidance to Claude Code when working on this repository.

---

## ⚠️ CRITICAL: READ THIS FIRST BEFORE ANY TASK

**DO NOT PROCEED WITH ANY TASK WITHOUT READING THESE CONTEXT FILES.**

### Agent Context Files (MANDATORY - READ IN ORDER)

0. **[skill.md](skill.md)** ← START HERE FIRST (3 min)
   - Skills, roles, and core rules
   - **CRITICAL**: Skip this → you'll use wrong commands and waste cycles

1. **[_ctx/agent_trifecta_dope.md](_ctx/agent_trifecta_dope.md)** ← THEN READ (5 min)
   - Current implementation status, active features
   - **CRITICAL**: Skip this → you'll duplicate work or break things

2. **[_ctx/session_trifecta_dope.md](_ctx/session_trifecta_dope.md)** ← SKIM (2 min)
   - Session history, handoff log
   - **CRITICAL**: Skip this → you'll miss workarounds and hit known bugs

3. **[_ctx/prime_trifecta_dope.md](_ctx/prime_trifecta_dope.md)** ← REFERENCE (1 min)
   - Architectural reference, system structure
   - **CRITICAL**: Skip this → you'll violate architectural constraints

### If You Skip

Skip these → you'll:
- ⛔ Break existing implementations
- ⛔ Duplicate work already done
- ⛔ Fail verification gates

✅ READ CONTEXT FIRST → THEN PROCEED

---

## Quick Start

```bash
uv sync --all-groups
uv run trifecta --help
uv run pytest -m "not slow"
```

See [skill.md](skill.md) for detailed commands, patterns, and troubleshooting.
