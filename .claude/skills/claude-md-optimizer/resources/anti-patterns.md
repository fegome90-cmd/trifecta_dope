# CLAUDE.md Anti-Patterns

Based on research from Anthropic docs, HumanLayer, blog.sshh.io, and expert sources.

## Critical Anti-Patterns

### 1. File Too Long (>150 lines)

**Problem:** Instruction following degrades with more instructions. Frontier models can follow ~150-200 instructions reasonably; smaller models show exponential decay.

**Solution:** Use progressive disclosure. Move task-specific info to external docs with clear names. Keep only universally applicable instructions.

**Sources:**
- HumanLayer: "Less is more; root CLAUDE.md is under sixty lines"
- LinkedIn expert: "< 150 lines for optimal performance"
- General consensus: "< 300 lines maximum"

### 2. Code Style Guidelines

**Problem:** LLMs are expensive and slow compared to traditional linters/formatters. Including style rules degrades performance and eats context window.

**Solution:** Use deterministic tools:
- TypeScript/JS: ESLint, Prettier, Biome
- Python: ruff, black, mypy
- "Stop" hooks: Run formatters and present errors to Claude for fixing

**Sources:**
- HumanLayer: "LLMs are expensive and slow compared to traditional linters"
- blog.sshh.io: "Use CLAUDE.md as a forcing function to simplify your tooling"

### 3. Verbose Command Documentation

**Problem:** Writing paragraphs to document complex CLI commands. This documents complexity instead of fixing it.

**Solution:** Create simple bash/npm/py scripts with intuitive APIs. Document the simple script, not the complex command.

**Example:**
❌ `npx tsx --import-module @swc-node/register src/infrastructure/scrapers/youtube-scraper.ts`
✅ `npm run scrape` (script in package.json)

**Sources:**
- blog.sshh.io: "Redefining tools instead of simplifying"
- Multiple experts: "Commands should be simple, memorable"

### 4. Long Narrative Paragraphs

**Problem:** LLMs struggle with lengthy documents when also processing code. Harder to parse and remember.

**Solution:** Use bullet points and short sentences. Be specific and direct.

**Sources:**
- MaxiRect blog: "Bullets and short sentences work better than paragraphs"
- Multiple experts: "Clear directives outperform lengthy explanations"

### 5. Negative-Only Constraints

**Problem:** "Never use the --foo-bar flag" without alternatives causes agent paralysis. Agent thinks it must use that flag.

**Solution:** Always provide alternatives. "Never use X, prefer Y"

**Sources:**
- blog.sshh.io: "Negative-only constraints create agent paralysis"

### 6. Embedded Documentation Files

**Problem:** Using `@` to embed entire documentation files. Bloats context window by embedding full file on every run.

**Solution:** Reference file paths and "pitch" when/why to read. For complex usage or specific errors, mention: "For advanced troubleshooting, see path/to/docs.md"

**Sources:**
- blog.sshh.io: "Embedding large docs bloats context"

## Quick Reference Table

| Anti-Pattern | Detection | Solution |
|--------------|------------|----------|
| File > 150 lines | Count lines | Progressive disclosure |
| Code style rules | Keywords: "style", "format", "lint" | Use linters |
| Verbose commands | Complex commands in backticks | Create scripts |
| Long paragraphs | Paragraphs > 3 lines | Use bullets |
| "Never" without alternative | "Never" + no "prefer" | Add alternatives |
| @file references | "@path/to/file.md" | Reference paths |
