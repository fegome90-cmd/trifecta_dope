# agents.md Template

Use this template to create a parallel onboarding file for external agents (Gemini, Claude, GPT, etc.).

```markdown
# agents.md

This file provides guidance for AI agents (Claude, Gemini, GPT, etc.) when working with code in this repository.

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

0. **[skill.md](skill.md)** ← START HERE FIRST (X min read)
   - **What**: [DESCRIBE FILE PURPOSE]
   - **Why**: [WHY IT MATTERS]
   - **Contains**: [KEY SECTIONS]
   - **CRITICAL**: Skip this → you'll [CONSEQUENCE]

1. **[_ctx/agent_XXX.md](_ctx/agent_XXX.md)** ← THEN READ THIS (X min read)
   - **What**: [DESCRIBE FILE PURPOSE]
   - **Why**: [WHY IT MATTERS]
   - **Contains**: [KEY SECTIONS]
   - **CRITICAL**: Skip this → you'll [CONSEQUENCE]

2. **[_ctx/session_XXX.md](_ctx/session_XXX.md)** ← THEN READ THIS (X min skim)
   - **What**: [DESCRIBE FILE PURPOSE]
   - **Why**: [WHY IT MATTERS]
   - **Contains**: [KEY SECTIONS]
   - **CRITICAL**: Skip this → you'll [CONSEQUENCE]

3. **[_ctx/prime_XXX.md](_ctx/prime_XXX.md)** ← REFERENCE THIS (X min check)
   - **What**: [DESCRIBE FILE PURPOSE]
   - **Why**: [WHY IT MATTERS]
   - **Contains**: [KEY SECTIONS]
   - **CRITICAL**: Skip this → you'll [CONSEQUENCE]

### If You Skip These Files

⛔ **YOU WILL:**
- [SPECIFIC FAILURE 1]
- [SPECIFIC FAILURE 2]
- [SPECIFIC FAILURE 3]

✅ **INSTEAD:**
1. Read the X files (X min total)
2. Then start your task
3. Reference them constantly
4. Update session_XXX.md when you finish

---

## Quick Start

```bash
# [INSTALLATION COMMAND]

# [KEY COMMANDS]

# [TESTING COMMANDS]
```

---

## Architecture Overview

[PROJECT ARCHITECTURE: Layers, patterns, constraints]

---

## Red Flags

| Issue | Why It's Wrong | Fix |
|-------|----------------|-----|
| [VIOLATION 1] | [REASON] | [SOLUTION] |
| [VIOLATION 2] | [REASON] | [SOLUTION] |
| [VIOLATION 3] | [REASON] | [SOLUTION] |

---

## Testing

[TESTING PRACTICES AND COMMANDS]

---

## Source of Truth

- **README.md** - Project overview
- **docs/CONTRACTS.md** - API contracts
- **docs/adr/** - Architecture decisions

---

**Living Document**: Update this file when friction is encountered or new patterns emerge.
```

## Key Differences from CLAUDE.md

**agents.md** is for external/diverse agents. Emphasize:

- More defensive language (external agents might not follow norms)
- "Red Flags" table instead of just "Architecture" (make violations explicit)
- Concrete MUST/MUST NOT rules
- More emphasis on testing gates
- Clearer consequences for failure

## Synchronization Rule

**CRITICAL: Keep CLAUDE.md and agents.md IN SYNC**

Both files MUST have:
- ✓ Identical mandatory files list (0-3)
- ✓ Identical time estimates
- ✓ Identical consequences
- ✓ Identical Quick Start commands
- ✓ Harmonized architecture/red flags content

Divergence = agent confusion. Use links or diff tools to verify sync weekly.
