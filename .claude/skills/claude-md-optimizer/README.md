# CLAUDE.md Optimizer Skill

Optimizes CLAUDE.md files based on expert research from Anthropic and community best practices.

## Installation

Located at: `~/.claude/skills/claude-md-optimizer/`

## Usage

```bash
# In any project directory
Skill: claude-md-optimizer
```

## What It Does

1. **Detects project type** from key files (pyproject.toml, package.json, tsconfig.json)
2. **Analyzes existing CLAUDE.md** for anti-patterns
3. **Generates optimized version** using best practices
4. **Asks for confirmation** before writing

## Supported Project Types

- Python + FP
- TypeScript + Clean Architecture
- Web Standard (Next.js, React, Vue)
- Data Science

## Key Improvements

- Reduces file length to < 150 lines (often < 60)
- Removes code style guidelines (use linters instead)
- Simplifies commands (uses npm/py scripts)
- Uses bullets instead of long paragraphs
- References external docs (progressive disclosure)

## Research Sources

- Anthropic Claude Code best practices
- HumanLayer "Writing a good CLAUDE.md"
- blog.sshh.io "How I Use Every Claude Code Feature"
- LinkedIn expert recommendations
- Community best practices

## Example

Before: 142 lines with verbose documentation
After: 66 lines with progressive disclosure

**Result**: 53% reduction while maintaining all critical guidance.

See `examples/youtube-scraper/` for before/after comparison.
