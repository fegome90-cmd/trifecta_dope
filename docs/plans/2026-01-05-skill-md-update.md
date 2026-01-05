# Skill.md Update Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Actualizar skill.md para reflejar el estado actual del CLI Trifecta v2.0, protocolos de sesión reales y comandos disponibles, basado en --help, git history y session_trifecta_dope.md.

**Architecture:** 
1. Reemplazar sección "Core Rules" con protocolos actuales del CLI (session, ctx search, ctx get, ctx sync)
2. Actualizar "When to Use" con casos de uso reales del repo actual (LSP, AST symbols M1, telemetry, obsidian)
3. Reemplazar ejemplos de comandos antiguos con nuevos comandos CLI documentados
4. Mantener compacto (<100 líneas) pero exhaustivo

**Tech Stack:** 
- Trifecta CLI v2.0 (typer-based)
- Commands disponibles (según `--help`):
  - **ctx**: search, get, sync, plan, eval-plan, stats, validate, build, reset - **STABLE**
  - **session**: append (logging) - **STABLE**
  - **telemetry**: report, export, chart, stats - **COMPLETE (2025-12-31)**
  - **ast**: symbols (M1 PRODUCTION READY 2026-01-03), hover (WIP), snippet
  - **obsidian**: vault integration - **⚠️ EXPERIMENTAL (no mencionado en session.md, no usar en producción)**
  - **create**: scaffold new segment - **STABLE**
  - **load**: macro command - **STABLE**
  - **legacy**: burn-down commands - **DEPRECATED**
  
- Features activas (verificadas en session.md hasta 2026-01-04):
  - ✅ **M1 AST Symbols** (SkeletonMapBuilder con stdlib ast) - PRODUCTION READY
  - ✅ **LSP daemon** (UNIX socket, 180s TTL) - Relaxed READY contract
  - ✅ **Telemetry System** (report, export, chart) - COMPLETE
  - ✅ **Token Tracking** (estimación automática) - IMPLEMENTED
  - ✅ **Error Cards** (SEGMENT_NOT_INITIALIZED) - STABLE
  - ✅ **Deprecation Tracking** (TRIFECTA_DEPRECATED) - STABLE
  - ✅ **Pre-commit Gates** (zero side-effects) - STABLE
  - ⚠️ **Obsidian integration** - EXPERIMENTAL (inmaduro, no aprobado)
  
- Documentation format: YAML frontmatter + Markdown sections

---

## Task 1: Backup and Analyze Current skill.md

**Files:**
- Read: `skill.md` (actual)
- Reference: `_ctx/prime_trifecta_dope.md`, `_ctx/session_trifecta_dope.md`, `Makefile`

**Step 1: Read current skill.md**

Run: `head -50 skill.md`
Expected: Obtener estructura actual

**Step 2: Identify what's outdated**

Outdated sections:
- `### Session Evidence Protocol` - Usa comandos viejos (`trifecta session append` existe pero estructura cambió)
- `## Core Rules` - No menciona `make` commands, Makefile-driven workflow
- Examples - Hacen referencia a rutas absolutas de `/Users/...` que no existen

**Step 3: Collect actual commands from CLI**

Commands found via `--help`:
- `trifecta create` - Create new segment
- `trifecta ctx search --query "..."` - Search context (ACTUAL)
- `trifecta ctx get --ids "id1,id2" --mode excerpt` - Get excerpts (ACTUAL)
- `trifecta ctx sync` - Build + Validate (ACTUAL macro command)
- `trifecta session append` - Log session (ACTUAL)
- `trifecta ctx stats` - Show telemetry (NEW in v2.0)
- `trifecta ctx plan` - Generate plan using PRIME (NEW)

---

## Task 2: Write New Core Rules Section

**Files:**
- Modify: `skill.md` (Core Rules section, lines ~15-30)

**Step 1: Replace "Core Rules" with actual workflow**

Replace OLD:
```markdown
## Core Rules
1. **Sync First**: Valida `.env` antes de cambios
2. **Test Locally**: Tests del segmento antes de commit
3. **Read Before Write**: Lee código antes de modificar
4. **Document**: Actualiza `session_..md`
```

With NEW:
```markdown
## Core Rules

1. **make install** - Siempre comienza con `make install` para sincronizar dependencias

2. **Search → Get (Con Instrucciones, NO Keywords)**
   
   ❌ **MAL (keyword):**
   ```bash
   trifecta ctx search --segment . --query "telemetry" --limit 6
   ```
   
   ✅ **BIEN (instrucción):**
   ```bash
   trifecta ctx search --segment . \
     --query "Encuentra documentación sobre cómo implementar el sistema de telemetría con event schema y ejemplos de uso" \
     --limit 6
   ```
   
   Luego: `trifecta ctx get --segment . --ids "id1,id2" --mode excerpt --budget-token-est 900`

3. **Log Evidence** - Registra en `session.md` vía `trifecta session append --segment . --summary "..."`

4. **Test Gates** - Antes de commit: `make gate-all` (Unit + Integration + Acceptance fast)

5. **No Silent Fallback** - Si `ctx validate` falla: STOP → `make ctx-sync` → re-validate

> ⚠️ Violaciones críticas: YAML long history, rutas absolutas, scripts legacy, fallback silencioso, pack stale
```

**Step 2: Run command to verify structure**

Run: `grep -A 10 "## Core Rules" skill.md`
Expected: Ver nueva estructura

---

## Task 3: Write New Session Evidence Protocol Section

**Files:**
- Modify: `skill.md` (Session Evidence Protocol subsection)

**Step 1: Replace with actual CLI commands**

Replace OLD:
```markdown
### Session Evidence Protocol

1. **Persist**: `trifecta session append --segment . --summary "<task>"`
2. **Sync**: `trifecta ctx sync --segment .`
3. **Execute**: `ctx search` → `ctx get`
4. **Record**: `trifecta session append --segment . --summary "Completed <task>"`
```

With NEW (condensed and accurate):
```markdown
### Session Evidence Protocol (The 4-Step Cycle)

```bash
# 1. PERSIST intent
trifecta session append --segment . --summary "<what you'll do>" \
  --files "file1.py,file2.md" --commands "ctx search,ctx get"

# 2. SEARCH with instruction (not keyword)
trifecta ctx search --segment . \
  --query "Find documentation about how to implement the session persistence protocol" \
  --limit 6

# 3. GET excerpt to confirm relevance
trifecta ctx get --segment . --ids "id1,id2" --mode excerpt --budget-token-est 900

# 4. RECORD result
trifecta session append --segment . --summary "Completed: found and reviewed context"
```

Or use **Makefile shortcuts**:
```bash
make install              # Sync dependencies
make ctx-search Q="instruction" SEGMENT=.
make ctx-sync SEGMENT=.
make gate-all            # Full test gate before commit
```
```

---

## Task 4: Rewrite "When to Use" Section

**Files:**
- Modify: `skill.md` (When to Use section)

**Step 1: Replace outdated "When to Use"**

Replace OLD section with NEW cases based on actual repo usage:

```markdown
## When to Use

**Use skill.md when:**
- Necesitas sincronizar contexto de un segmento (vía Trifecta CLI)
- Implementando cambios en código/docs del segmento
- Realizando handoff entre sesiones (log en session.md)
- Buscando info específica sin cargar archivos completos (ctx search → ctx get)
- Validando integridad del context pack antes de cambios (ctx validate)
- Trabajando con AST symbols M1 PRODUCTION (`trifecta ast symbols`)
- Analizando telemetría del CLI (`trifecta telemetry report/chart/stats`)

**Triggers to activate:**
- Entraste al workspace sin leer skill.md + prime + agent + session
- El CLI falla con "SEGMENT_NOT_INITIALIZED" Error Card
- `ctx validate` reporta stale pack
- Necesitas buscar documentación sin RAG (solo PRIME index)
- Quieres extraer símbolos de módulos Python sin tree-sitter

**⚠️ NO usar (experimental/inmaduro):**
- `trifecta obsidian` - Integración no aprobada, en desarrollo
```

---

## Task 5: Update "Common Mistakes" Section

**Files:**
- Modify: `skill.md` (Common Mistakes section)

**Step 1: Replace with real errors from recent sessions**

Based on `session_trifecta_dope.md` recent entries, replace:

```markdown
## Common Mistakes

| Mistake | Why Bad | Fix |
|---------|---------|-----|
| Using keywords instead of instructions | Produce noise/zero-hits | Use `--query "Find documentation about how to implement X"` |
| Exceeding token budget in single ctx.get | Degrades agent attention | Use `--mode excerpt` + budget ~900 tokens max |
| Absolute paths in commands | Not portable, breaks on different machines | Use relative paths or `SEGMENT=.` |
| Ignoring ctx validate failures | Pack may be stale/corrupted | STOP → `make ctx-sync` → `make ctx-validate` |
| Skipping session.md logging | Lose continuity between agent runs | Always `trifecta session append` after significant work |
| Executing legacy ingestion scripts | Data corruption, duplication | Use `trifecta ctx sync` (official command) |
```

---

## Task 6: Add "Quick Reference" Box

**Files:**
- Modify: `skill.md` (new Quick Reference section before Common Mistakes)

**Step 1: Insert quick command reference**

```markdown
## Quick Reference

| Task | Command |
|------|---------|
| **Install deps** | `make install` |
| **Search docs** | `make ctx-search Q="instruction" SEGMENT=.` |
| **Sync context** | `make ctx-sync SEGMENT=.` |
| **Run tests** | `make gate-all` |
| **Full validation** | `trifecta ctx validate --segment .` |
| **View telemetry** | `trifecta telemetry report -s . --last 30` |
| **Generate plan** | `trifecta ctx plan --segment . --task "..."` |
| **Extract symbols (M1)** | `trifecta ast symbols "sym://python/mod/path"` |
| **Chart telemetry** | `trifecta telemetry chart -s . --type hits` |
| **Check git status** | `git status` (before each commit) |
```

---

## Task 7: Update Metadata and Final Verification

**Files:**
- Modify: `skill.md` (footer + YAML frontmatter)

**Step 1: Update last_verified date and profile**

Replace footer:
```markdown
---
**Profile**: `impl_patch` | **Updated**: 2025-12-29
```

With:
```markdown
---
**Profile**: `impl_patch` | **Updated**: 2026-01-05 | **Verified Against**: CLI v2.0, Makefile, session.md 2026-01-04
```

**Step 2: Verify final line count**

Run: `wc -l skill.md`
Expected: < 110 lines (condensed, no long YAML history)

**Step 3: Test commands in the new skill.md**

Run (from skill.md Quick Reference):
```bash
make install
make ctx-search Q="session evidence protocol" SEGMENT=.
make gate-all
```

Expected: All commands work without errors

---

## Task 8: Commit and Verify

**Files:**
- Modified: `skill.md`

**Step 1: Review diff**

Run: `git diff skill.md | head -100`
Expected: Old commands → new CLI commands, consolidated structure

**Step 2: Commit changes**

```bash
git add skill.md
git commit -m "docs: update skill.md for Trifecta v2.0 CLI and actual protocols"
```

**Step 3: Verify no regressions**

Run: `grep -c "Users/felipe" skill.md || echo "✅ No stale paths"`
Expected: Zero matches (no absolute paths from old env)

Run: `grep "trifecta ctx" skill.md | wc -l`
Expected: ≥ 5 lines with new CLI commands

---

## Summary

**What changes:**
- Core Rules: Added make install, Search→Get pattern, test gates, fail-closed protocol
- Session Protocol: Condensed to 4-step cycle with Makefile aliases
- When to Use: Real triggers from actual repo usage
- Common Mistakes: Based on actual errors from session.md
- New: Quick Reference table with essential commands

**What stays the same:**
- Philosophy (PRIME-only, no RAG, progressive disclosure)
- Session persistence importance
- Token budget constraints

**Lines saved:** 40→ 45 (condensed YAML, removed long history section)

---

**EXECUTION PLAN READY**
Options:
1. **Subagent-Driven** - I dispatch fresh subagent per task with code review
2. **This Session** - I implement tasks sequentially with verification

Which approach?
