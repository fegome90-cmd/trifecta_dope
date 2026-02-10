# skill.md Template

Use this template as a starting point for your project's skill.md.

```markdown
---
name: [project_name]
description: Use when [specific triggering conditions] - [what it does]
---

## Overview

[What is this skill? Core principle in 1-2 sentences]

## When to Use

**Situations:**
- [Situation 1 where skill applies]
- [Situation 2 where skill applies]
- [Situation 3 where skill applies]

## Core Rules

1. **[Rule 1]** - [Explanation with consequence if violated]
2. **[Rule 2]** - [Explanation with consequence if violated]
3. **[Rule 3]** - [Explanation with consequence if violated]

## Common Mistakes

| Mistake | Why Bad | Fix |
|---------|---------|-----|
| [Violation 1] | [Consequence] | [Correct approach] |
| [Violation 2] | [Consequence] | [Correct approach] |
| [Violation 3] | [Consequence] | [Correct approach] |

## Quick Reference

| Command | Purpose |
|---------|---------|
| [cmd1] | [What it does] |
| [cmd2] | [What it does] |
| [cmd3] | [What it does] |

---

**Profile**: [impl_type] | **Updated**: [date] | **Verified Against**: [what was checked]
```

## Customization Guide

### Frontmatter
- **name**: Letters, numbers, hyphens only (max 64 chars)
- **description**: "Use when [trigger symptom] - [what it does]" (max 1024 chars)

### Overview
- Keep to 2-3 sentences max
- Answer: "What is the core insight?"
- Don't explain the whole thing (save for sections below)

### When to Use
- 3-5 concrete situations where skill applies
- Use "Situations:" header (not "Triggers" or "When")
- Make them recognizable to someone in the situation

### Core Rules
- 3-5 essential rules only (not 20)
- Format: **[Rule Name]** - [Explanation]
- Include consequences for violation
- Make rules testable (can you verify compliance?)

### Common Mistakes
- Real errors agents make (not hypothetical)
- Explain why it's bad (consequence)
- Provide actual fix (not just "don't do that")

### Quick Reference
- TL;DR table for lookups
- Commands, patterns, or quick facts
- Should fit on one screen (5-10 rows max)

### Footer
- **Profile**: What type (impl_patch, plan, debug, verify, etc.)
- **Updated**: Last update date (YYYY-MM-DD)
- **Verified Against**: What was tested (tools, versions, gate status)

## Length Target

- **Total**: 100-200 lines max
- **Overview**: 2-3 lines
- **When to Use**: 3-5 lines
- **Core Rules**: 10-15 lines
- **Common Mistakes**: 8-12 lines (as table)
- **Quick Reference**: 8-10 lines (as table)

Keep it concise. If you need more detail, create supporting files in `resources/`.

## Example Structure (Word Count)

```
---
name: example-skill
description: Use when X happens - does Y
---

## Overview
[3-4 sentences]              ~50 words

## When to Use
[3-5 bullet points]          ~50 words

## Core Rules
[3-4 rules with explanation]  ~100 words

## Common Mistakes
[Table 3x3]                   ~60 words

## Quick Reference
[Table 5-7 rows]              ~50 words

---
[Footer line]                ~10 words

TOTAL: ~320 words / 150 lines
```

Use this to balance content. If version is longer, consider moving details to `resources/` files.
