# CLAUDE.md Best Practices

Aggregated from Anthropic documentation, HumanLayer, LinkedIn experts, and community research.

## Core Principles

### 1. Less (Instructions) is More

Include as few instructions as possible - only ones universally applicable to tasks.

**Rationale:** Claude wraps CLAUDE.md in a system reminder stating context "may or may not be relevant." More non-universal info = more likely Claude ignores the file entirely.

### 2. Progressive Disclosure

Keep task-specific instructions in separate markdown files with self-descriptive names. In CLAUDE.md, list these files with brief descriptions.

**Example:**
```markdown
## Additional Context

- `ARCHITECTURE.md` - Detailed layer rules and patterns
- `DEPLOYMENT.md` - Production deployment guide
- `API.md` - REST API documentation
```

### 3. Prefer Pointers to Copies

Don't include code snippets - they become outdated. Include `file:line` references to point to authoritative context.

**Example:**
❌ "Here's the parser function: [code block]"
✅ "See parser implementation at `src/domain/services/parsers.ts:14-55`"

### 4. Treat as Living Document

Start small, document based on what Claude gets wrong, iterate based on actual friction points. Not a "write once and forget" file.

## Recommended Structure

```markdown
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in this repository.

---

## Quick Start

```bash
# Common commands (simple, via scripts)
npm run build
npm test
npm run typecheck
```

---

## Architecture Overview

[Brief 2-3 sentences about architecture pattern]

See `ARCHITECTURE.md` for complete details.

---

## Key Patterns

[Bullet points of domain-specific patterns - max 5]

---

## Development Workflow

[How to work on this project - steps]

---

## Source of Truth

- `PRP.md` - Product requirements
- `ARCHITECTURE.md` - Architecture details
- `README.md` - Project overview
```

## Length Guidelines

| Source | Recommendation | Rationale |
|--------|----------------|-----------|
| HumanLayer | < 60 lines | Less is more; root file is tiny |
| LinkedIn expert | < 150 lines | Optimal performance |
| General consensus | < 300 lines | Maximum before severe degradation |
| Anthropic | "Concise" | No specific limit, emphasizes brevity |

## What to Include vs Exclude

### Include ✅

- Universal commands (build, test, typecheck)
- High-level architecture (2-3 sentences max)
- Domain-specific patterns (3-5 key ones)
- Development workflow steps
- Links to authoritative docs

### Exclude ❌

- Code style guidelines (use linters)
- Task-specific instructions (progressive disclosure)
- Long command documentation (create scripts)
- Code snippets (reference files instead)
- Redundant information (obvious from file structure)
- Commentary or nice-to-have info

## Verification Checklist

After generating CLAUDE.md, verify:

- [ ] File < 150 lines (or < 300 for complex projects)
- [ ] No code style guidelines included
- [ ] Commands use npm/py scripts
- [ ] Bullets > paragraphs
- [ ] References external docs
- [ ] Only universal instructions
- [ ] No "never" without alternatives
