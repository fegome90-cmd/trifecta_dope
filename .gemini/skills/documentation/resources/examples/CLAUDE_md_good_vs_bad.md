# ❌ BAD OnBoarding (Before Applying Skill)

```markdown
# CLAUDE.md

This file provides guidance to Claude Code.

## Quick Start

```bash
uv sync --all-groups
uv run trifecta --help
```

## Architecture Overview

**Python + Clean Architecture**:
- Domain (`src/domain/`) - Pure business logic
- Application (`src/application/`) - Use cases
- Infrastructure (`src/infrastructure/`) - Adapters

## Source of Truth

- agent_trifecta_dope.md - Stack info
- session_trifecta_dope.md - History
- prime_trifecta_dope.md - Architecture reference
```

### Problems with this version:

- ❌ CRITICAL section buried/missing
- ❌ Agent might run `uv sync` without understanding project state
- ❌ No warning about mandatory context files
- ❌ No consequences for skipping files
- ❌ "Quick Start" comes before understanding project
- ❌ No time estimates
- ❌ Passive language: "helpful guidance" vs "DO NOT PROCEED"
- ❌ Too many context files without clear prioritization

---

# ✅ GOOD Onboarding (After Applying Skill)

```markdown
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## ⚠️ CRITICAL: READ THIS FIRST BEFORE ANY TASK

**DO NOT PROCEED WITH ANY TASK WITHOUT READING THESE CONTEXT FILES.**

Assuming anything about this project without consulting these files is a breach of the work contract.

### Agent Context Files (MANDATORY - READ THESE FIRST)

These files contain **CURRENT PROJECT STATE, ACTIVE FEATURES, AND ARCHITECTURE DECISIONS**. Ignoring them will result in:
- ✗ Breaking existing implementations
- ✗ Duplicating work already done
- ✗ Misunderstanding the current system state
- ✗ Failing verification gates

**READ IN THIS ORDER:**

0. **[skill.md](skill.md)** ← START HERE FIRST (3 min read)
   - **What**: Skills, roles, and core rules for this project
   - **Why**: Know the mandatory patterns and commands to use
   - **Contains**: Setup instructions, context cycle, session persistence
   - **CRITICAL**: Skip this → you'll use wrong commands and waste cycles

1. **[_ctx/agent_trifecta_dope.md](_ctx/agent_trifecta_dope.md)** ← THEN READ THIS (5 min read)
   - **What**: Current implementation status and active features
   - **Why**: Know what's ACTUALLY implemented vs. what's planned
   - **Contains**: Tech stack versions, active patterns, completed work
   - **CRITICAL**: Skip this → you'll duplicate work or break things

2. **[_ctx/session_trifecta_dope.md](_ctx/session_trifecta_dope.md)** ← THEN READ THIS (2 min skim)
   - **What**: Session history and continuation points
   - **Why**: Understand what was done in the last session
   - **Contains**: Previous decisions, known workarounds, open issues
   - **CRITICAL**: Skip this → you'll miss workarounds and hit known bugs

3. **[_ctx/prime_trifecta_dope.md](_ctx/prime_trifecta_dope.md)** ← REFERENCE THIS (1 min check)
   - **What**: Architectural reference and system structure
   - **Why**: Understand the fundamental system design
   - **Contains**: Core patterns, layer separation, dependency rules
   - **CRITICAL**: Skip this → you'll violate architectural constraints

### If You Skip These Files

⛔ **YOU WILL:**
- Propose features that already exist
- Break working implementations
- Violate architectural patterns
- Fail the verification gate
- Waste time and tokens

✅ **INSTEAD:**
1. Read the 4 context files (11 min total)
2. Then start your task
3. Reference them constantly
4. Update session_trifecta_dope.md when you finish

---

## Quick Start

```bash
# Install
uv sync --all-groups

# Run CLI
uv run trifecta --help

# Tests
uv run pytest                    # All tests
uv run pytest -m "not slow"      # Skip slow tests
uv run pytest tests/acceptance/  # Acceptance gate
```

## Architecture Overview

**Python + Clean Architecture** with strict layer separation:

- **Domain** (`src/domain/`) - Pure business logic (no IO, no async, no framework dependencies)
- **Application** (`src/application/`) - Use cases, orchestration
- **Infrastructure** (`src/infrastructure/`) - Framework adapters, IO, external services

**Critical Rule:** Dependencies point INWARD. Domain → Application → Infrastructure.
```

### Improvements in this version:

- ✅ CRITICAL section FIRST (before Quick Start)
- ✅ Explicit "DO NOT PROCEED" language
- ✅ Numbered list (0, 1, 2, 3) with read order
- ✅ Time estimates for each file
- ✅ Specific consequences for each file
- ✅ "If you skip" section with ⛔ and ✅ contrast
- ✅ Exactly 4 mandatory files (not 10)
- ✅ Agent cannot miss the warning
- ✅ Professional tone with legal language ("breach of contract")
- ✅ Quick Start comes AFTER understanding context
- ✅ Architecture section is clear and structured

---

## Key Differences

| Aspect | ❌ Bad | ✅ Good |
|--------|---------|----------|
| **Position** | Context buried 3rd | CRITICAL FIRST |
| **Language** | "helpful guidance" | "**DO NOT PROCEED**" |
| **Urgency** | Passive ("should read") | Imperative (negation) |
| **Consequences** | None stated | Explicit failures listed |
| **Prioritization** | All files equal | Numbered 0-3 with order |
| **Time** | Unknown | 3 min, 5 min, 2 min, 1 min |
| **Symbols** | Generic | ⚠️ ⛔ ✅ ← |
| **Result** | Agent skips context | Agent reads context FIRST |
