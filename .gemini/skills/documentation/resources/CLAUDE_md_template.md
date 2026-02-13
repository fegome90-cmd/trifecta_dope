# CLAUDE.md Template

Copy this template and customize for your project.

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

## Key Patterns

[DEVELOPMENT PATTERNS AND RULES]

---

## Common Tasks

[ORGANIZED BY TASK TYPE]

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

## Customization Guide

1. **Replace `XXX`** with your project identifier (e.g., `trifecta_dope`)

2. **For each mandatory file (0-3):**
   - **What**: One sentence describing the file
   - **Why**: Why reading it prevents problems
   - **Contains**: 2-3 key sections
   - **CRITICAL**: Specific consequence if skipped

3. **"If You Skip" section:**
   - 3-5 specific, credible failures (not generic)
   - Make consequences concrete: "duplicate work", "break things", "fail gates"

4. **Time estimates:**
   - Be realistic - can someone really read in 3 min?
   - Add minutes: 3 min, 5 min, 10 min, etc.

5. **Quick Start:**
   - Copy/paste ready commands
   - Include install, help, test examples
   - Keep to 3-5 essential commands

6. **Architecture section:**
   - Keep brief (2-3 paragraphs max)
   - Link to detailed docs in `docs/adr/`
   - Focus on: layers, key patterns, critical rules

7. **Final check:**
   - Run CRITICAL section through checklist.md
   - Verify all links are valid
   - Ensure consistency with agents.md (if you have one)
