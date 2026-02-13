---
name: agent-documentation
description: Use when creating or updating agent onboarding files (CLAUDE.md, agents.md, skill.md) to capture LLM attention on critical context with strategic positioning, warning symbols, and explicit consequences
---

# Agent Documentation Skill

## Overview

Agent Documentation ensures critical project context is prominently positioned so LLMs prioritize reading required files before proceeding. The skill uses positional priority, attention-capturing symbols, and explicit consequences to prevent assumptions and architectural violations.

## When to Use

**Situations:**
- Creating/updating CLAUDE.md or agents.md (onboarding files)
- Agents propose features that already exist (missing implementation docs)
- Agents skip reading critical context and make wrong assumptions
- Critical warnings are buried below other content
- Documentation spans multiple files and needs clear read order

## Core Pattern: 4 Layers of Documentation

```
Layer 1: CRITICAL (Position: FIRST) → ⚠️ "DO NOT PROCEED" + Mandatory Files
Layer 2: QUICK START → Copy-paste commands, confidence building
Layer 3: ARCHITECTURE → Design decisions, patterns, constraints
Layer 4: REFERENCE → Lookup tables, troubleshooting, appendix
```

**Layer 1 Key Techniques:**
- Position: First section, before anything else
- Symbols: ⚠️ ⛔ 🛑 warning icons
- Language: "**DO NOT PROCEED**", "**MANDATORY**", "breach of contract"
- Structure: Numbered list (0, 1, 2) with ← arrows + time estimates
- Consequences: Section "If You Skip" with explicit ⛔ failures and ✅ fixes

## Common Mistakes

| Mistake | Why Bad | Fix |
|---------|---------|-----|
| Burying Layer 1 below Quick Start | LLM forms assumptions before reaching critical context | Put CRITICAL section FIRST |
| Passive language ("should read") | Doesn't register as urgent | Use imperatives: "DO NOT PROCEED" |
| Generic descriptions | LLMs skim vague content | Be specific: "Skip → duplicate work, break things" |
| Lowercase warnings | Blends with normal text | Use `## ⚠️ CRITICAL: ALL CAPS` + **bold** |
| No time estimates | LLMs ignore with unknown cost | Add estimates: "← (3 min read)" |
| Unclear consequences | Why read if you don't know what happens? | "Skip → you'll violate patterns, fail gates" |
| Too many context files | Kills attention (10 files = skip all) | Limit to 3-5 files max |
| Stale paths (e.g., /Users/...) | Breaks trust and confuses context | Use relative paths only |

## Implementation

1. **Use templates** → See `resources/CLAUDE_md_template.md` and `resources/agents_md_template.md`
2. **Run verification** → See `resources/verify_documentation.sh`
3. **Review examples** → See `resources/examples/CLAUDE_md_good_vs_bad.md`
4. **Check your work** → See `resources/checklist.md`

## Resources

All templates, scripts, and examples are in `skills/documentation/resources/`:

```
resources/
├── CLAUDE_md_template.md          # Ready-to-use template
├── agents_md_template.md          # Ready-to-use template
├── skill_md_template.md           # Ready-to-use template
├── verify_documentation.sh        # Validation script
├── checklist.md                   # Implementation checklist
└── examples/
    └── CLAUDE_md_good_vs_bad.md   # Before/After example
```

Start with templates, validate with script, check against checklist.
