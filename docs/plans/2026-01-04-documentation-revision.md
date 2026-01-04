# Trifecta MVP Documentation Revision Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Profesionalizar la documentación oficial de Trifecta para reflejar con precisión el MVP funcional y operativo.

**Architecture:** Revisión en 4 capas: Root Files, Trifecta _ctx Files, Core Docs, y Archival.

**Tech Stack:** Markdown, Trifecta CLI (`ctx validate`, `ctx sync`), GitHub-style alerts.

---

## Auditoría Inicial (Hallazgos)

| Archivo | Líneas | Estado | Issues Detectados |
|:--------|:-------|:-------|:------------------|
| `README.md` | 383 | 🟡 Needs Update | Refs a `braindope.md` (no existe), roadmap desactualizado, script deprecados |
| `skill.md` | 70 | 🟢 Good | Fecha obsoleta (2025-12-29) |
| `readme_tf.md` | 85 | 🔴 Broken | Placeholders `..` en paths, fecha obsoleta |
| `_ctx/prime_*.md` | 80 | 🟢 Good | Verificar paths actualizados |
| `_ctx/agent_*.md` | 158 | 🟢 Good | Verificar gates actualizados |
| `_ctx/session_*.md` | 397 | 🟡 Large | Session log muy largo, considerar archival |
| `docs/CLI_WORKFLOW.md` | ~175 | 🟢 Good | Documentación help-driven |
| `docs/RELEASE_NOTES_v1.md` | ~50 | 🟡 Needs Update | No hay v1.1 notes |

### AST Navigation Findings (Trifecta Advanced)

**Templates Engine** (`src/infrastructure/templates.py:6`):
```json
{"symbol": "TemplateRenderer", "line": 6, "methods": ["render_skill", "render_prime", "render_agent", "render_session", "render_readme"]}
```

**CLI Documentation Commands** (`src/infrastructure/cli.py`):
| Function | Line | Purpose | Documentation Status |
|:---------|:-----|:--------|:---------------------|
| `create` | L1102 | Create Trifecta pack | ✅ Documented in README |
| `refresh_prime` | L1200 | Refresh prime file | ✅ Documented |
| `session_append` | L1281 | Append to session | ⚠️ Missing from README |
| `sync` | L897 | Macro: build+validate | ✅ Documented |
| `legacy_scan` | L1394 | Scan legacy files | ❌ NOT documented |
| `obsidian_sync` | L1427 | Obsidian integration | ❌ NOT documented |

**Context Pack Stats** (from `ctx search`):
| Doc | Chunk ID | Tokens |
|:----|:---------|:-------|
| prime | `prime:5d535ae4c0` | ~645 |
| skill | `skill:03ba77a5e8` | ~634 |
| agent | `agent:abafe98332` | ~1067 |
| session | `session:dce1f3d3c9` | ~5165 (⚠️ LARGE) |
| README | `ref:README.md:c2d9` | ~3347 |

---

## Task 1: Update Root README.md

**Files:**
- Modify: `README.md`

**Step 1.1: Remove Dead References**

```bash
grep -n "braindope.md" README.md
# Expected: Line 338, 81 - REMOVE or update
```

**Step 1.2: Update Roadmap Section**

Replace the "Pending" section with actual status from Kanban:
- [x] Context Pack ✅
- [x] AST Symbols M1 ✅ (separate tool)
- [x] LSP Daemon ✅ (separate tool)
- [ ] Linter-Driven Loop (In Progress)

**Step 1.3: Remove Deprecated Script References**

```bash
grep -n "ingest_trifecta.py" README.md
# Remove or add stronger deprecation notice
```

**Step 1.4: Verify All Commands Work**

Run each documented command and verify output:
```bash
uv run trifecta --help
uv run trifecta ctx build --help
uv run trifecta ctx search --help
uv run trifecta ast symbols --help
```

**Step 1.5: Commit**

```bash
git add README.md
git commit -m "docs: update README with MVP status and remove dead refs"
```

---

## Task 2: Fix readme_tf.md Placeholders

**Files:**
- Modify: `readme_tf.md`

**Step 2.1: Replace Placeholders**

Current (BROKEN):
```markdown
├── prime_..md # Lista de lectura obligatoria
└── session_..md # Log de handoffs (runtime)
```

Replace with:
```markdown
├── prime_<segment_id>.md  # Lista de lectura obligatoria
└── session_<segment_id>.md # Log de handoffs (runtime)
```

**Step 2.2: Update Date**

Replace `2025-12-29` with `2026-01-04`.

**Step 2.3: Commit**

```bash
git add readme_tf.md
git commit -m "docs: fix readme_tf placeholders and update date"
```

---

## Task 3: Update skill.md Date and Verify Content

**Files:**
- Modify: `skill.md`

**Step 3.1: Update Date**

Change line 69:
```markdown
**Profile**: `impl_patch` | **Updated**: 2026-01-04
```

**Step 3.2: Verify Protocols Match agent.md**

Confirm that "Session Evidence Protocol" in skill.md matches the detailed protocol in agent.md.

**Step 3.3: Commit**

```bash
git add skill.md
git commit -m "docs: update skill.md date to 2026-01-04"
```

---

## Task 4: Verify and Update _ctx Files

**Files:**
- Modify: `_ctx/prime_trifecta_dope.md`
- Modify: `_ctx/agent_trifecta_dope.md`

**Step 4.1: Validate Prime Paths**

```bash
# Check that all paths in prime exist
for path in $(grep -E "^\d+\." _ctx/prime_trifecta_dope.md | sed 's/.*`\(.*\)`.*/\1/'); do
  test -f "$path" || echo "MISSING: $path"
done
```

**Step 4.2: Update Agent Gates Table**

Verify all gate commands in agent.md work:
```bash
uv run pytest tests/unit/ -v --collect-only
uv run trifecta ctx validate --segment .
```

**Step 4.3: Update Dates**

Update `last_verified` in agent.md frontmatter to `2026-01-04`.

**Step 4.4: Commit**

```bash
git add _ctx/
git commit -m "docs: verify and update _ctx files for 2026-01-04"
```

---

## Task 5: Archive Old Session Entries

**Files:**
- Modify: `_ctx/session_trifecta_dope.md`
- Create: `docs/evidence/session_archive_2025.md`

**Step 5.1: Archive 2025 Entries**

Move all entries before 2026-01-01 to archive file.

**Step 5.2: Keep Recent Entries**

Keep only entries from 2026-01-01 onwards in active session file.

**Step 5.3: Add Archive Reference**

Add note at top of session.md:
```markdown
> For entries before 2026-01-01, see [archive](../docs/evidence/session_archive_2025.md)
```

**Step 5.4: Commit**

```bash
git add _ctx/session_trifecta_dope.md docs/evidence/
git commit -m "docs: archive 2025 session entries"
```

---

## Task 6: Create RELEASE_NOTES_v1.1.md

**Files:**
- Create: `docs/RELEASE_NOTES_v1.1.md`

**Step 6.1: Write Release Notes**

Document MVP features:
- Result Monad (FP)
- Context Pack v1 (PCC)
- AST Symbols M1
- LSP Daemon
- Error Cards
- Telemetry Kill Switch

**Step 6.2: Commit**

```bash
git add docs/RELEASE_NOTES_v1.1.md
git commit -m "docs: add v1.1 release notes for MVP"
```

---

## Task 7: Run Final Validation

**Step 7.1: Sync and Validate**

```bash
uv run trifecta ctx sync -s .
uv run trifecta ctx validate -s .
```

**Step 7.2: Log Session**

```bash
uv run trifecta session append -s . --summary "Documentation revision complete for MVP" --files "README.md,skill.md,readme_tf.md,docs/"
```

---

## Resumen de Entregables

| Entregable | Path | Descripción |
|:-----------|:-----|:------------|
| README.md | `README.md` | Updated with MVP status |
| readme_tf.md | `readme_tf.md` | Fixed placeholders |
| skill.md | `skill.md` | Updated date |
| _ctx files | `_ctx/*.md` | Verified and updated |
| Session Archive | `docs/evidence/session_archive_2025.md` | Historical entries |
| Release Notes | `docs/RELEASE_NOTES_v1.1.md` | MVP features documented |

---

**Plan completado. Dos opciones de ejecución:**

**1. Subagent-Driven (esta sesión)** — Despacho subagent fresco por task, review entre tasks, iteración rápida

**2. Parallel Session (separada)** — Nueva sesión con executing-plans, ejecución batch con checkpoints

**¿Cuál prefieres?**
