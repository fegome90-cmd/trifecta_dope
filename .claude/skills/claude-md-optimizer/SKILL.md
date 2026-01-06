---
name: claude-md-optimizer
description: Create or optimize CLAUDE.md files based on expert research and anti-patterns
---

## Overview

Generates optimized CLAUDE.md files by:
1. Detecting project type from key files (pyproject.toml, package.json, tsconfig.json)
2. Analyzing existing CLAUDE.md against anti-patterns
3. Applying expert best practices from research
4. Presenting proposal for user confirmation

## When to Use

- Creating new CLAUDE.md for a project
- Optimizing existing CLAUDE.md against anti-patterns
- Updating CLAUDE.md after major architectural changes

## Process

### Step 1: Detect Project Type

Read these files in order (first match wins):
1. `pyproject.toml` → Check for FP indicators ('fp', 'clean-arch', 'domain/')
2. `tsconfig.json` + `src/domain/` → TypeScript + Clean Architecture
3. `package.json` → Check for framework (next, react, vue)
4. `requirements.txt` / `environment.yml` → Data Science

**If detection fails:** Present menu to user:
```
🔍 No pude determinar el tipo de proyecto automáticamente.

Archivos encontrados:
  - [list files]

¿Podrías ayudarme identificando el tipo de proyecto?

1) Python Backend (FP + Clean Architecture)
2) Python Backend (estándar/django/fastapi)
3) TypeScript Backend (Clean Architecture)
4) Web App (Next.js/React/Vue)
5) Data Science/ML
6) Otro (describir)
```

### Step 2: Analyze Existing CLAUDE.md

If CLAUDE.md exists, check for anti-patterns:
- File length > 150 lines
- Code style guidelines (should use linters)
- Verbose command documentation (should use npm scripts)
- Long narrative paragraphs
- Task-specific instructions (not universal)

### Step 3: Generate Optimized Version

Load template from `resources/templates/` based on detected type and customize with:
- Detected tech stack
- Commands from package.json/pyproject.toml scripts
- Architecture patterns from codebase structure
- References to existing docs (README.md, ARCHITECTURE.md, PRP.md)

### Step 4: Present and Confirm

Show proposal and ask: "¿Aplicar estos cambios? (y/n)"

## Resources

- `resources/anti-patterns.md` - Known anti-patterns from research
- `resources/best-practices.md` - Expert recommendations
- `resources/templates/*.md` - Project-type templates

## Anti-Patterns to Avoid

❌ Code style guidelines → Use linters (ESLint, Prettier, ruff)
❌ Files > 150 lines → Use progressive disclosure
❌ Verbose commands → Create npm/py scripts
❌ Long paragraphs → Use bullets
❌ Negative-only constraints → Always provide alternatives
❌ Embedded documentation → Reference file paths

## Best Practices

✅ Keep < 150 lines (HumanLayer: <60, experts: <150)
✅ Progressive disclosure → External docs
✅ Simple commands → npm/py scripts
✅ Bullets > paragraphs
✅ Pointers to files, not copies
✅ Living document → Iterate based on friction

## Quick Reference

### File Detection

| Type | Key Files | Indicators |
|------|-----------|------------|
| python-fp | pyproject.toml | 'fp', 'clean-arch', 'src/domain/' |
| typescript-clean | tsconfig.json | 'src/domain/', 'src/infrastructure/' |
| web-standard | package.json | 'next', 'react', 'vue', 'vite' |
| data-science | requirements.txt | 'pandas', 'scikit-learn', 'jupyter' |

### Template Selection

```bash
# Python + FP
resources/templates/python-fp.md

# TypeScript + Clean Architecture
resources/templates/typescript-clean.md

# Web Standard
resources/templates/web-standard.md

# Data Science
resources/templates/data-science.md
```
