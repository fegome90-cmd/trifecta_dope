# Agent_trifecta_dope.md Update Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Actualizar _ctx/agent_trifecta_dope.md para reflejar CLI v2.0, features actuales (AST M1 production, telemetry system complete, LSP relaxed-ready, Error Cards, Deprecation tracking), y remover rutas obsoletas.

**Architecture:**
1. Reemplazar metadata con valores actuales (last_verified 2026-01-05, repo_root actualizado)
2. Ampliar Tech Stack con dependencias reales (tree-sitter, bandit, safety, etc.)
3. Reemplazar Workflow section con rutas relativas portables
4. Actualizar Gates con comandos Makefile modernos
5. Agregar nuevas secciones sobre features actuales (AST M1, Telemetry, Error Cards)
6. Refinar Troubleshooting con soluciones reales

**Tech Stack:**
- Trifecta CLI v2.0 (typer-based)
- Features verificadas en session.md hasta 2026-01-04
- Comandos: ctx, session, telemetry, ast (M1 PRODUCTION), obsidian (EXPERIMENTAL)
- Makefile-driven workflow

---

## Task 1: Audit Current agent_trifecta_dope.md

**Files:**
- Read: `_ctx/agent_trifecta_dope.md` (actual - ya obtenido via ctx get)
- Reference: `pyproject.toml`, `Makefile`, `session_trifecta_dope.md`

**Step 1: Identify outdated content**

From ctx get output, issues encontrados:
1. **Línea 5:** `repo_root: /Users/felipe_gonzalez/Developer/agent_h` - RUTA ABSOLETA OBSOLETA
2. **Línea 6:** `last_verified: 2026-01-01` - Desactualizada (hoy es 2026-01-05)
3. **Línea 16-18:** Tech Stack "Frameworks" usa nombres genéricos sin versiones
4. **Línea 20-26:** "LSP Infrastructure (Phase 3)" - Etiqueta desactualizada (ya está Phase STABLE)
5. **Línea 27-30:** "Herramientas" lista incompleta (falta bandit, safety, jupyter, plotly, etc.)
6. **Línea 37:** RUTA OBSOLETA nuevamente: `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope`
7. **Línea 56-60:** Session Evidence Protocol usa `--query "<tema>"` en lugar de instrucción específica
8. **Línea 79-83:** Gates usa comandos `uv run pytest` en lugar de Makefile shortcuts
9. **Línea 92:** Troubleshooting: `uv pip install -e .` es desactualizado (no se usa con uv)
10. **FALTA:** No menciona AST symbols M1 PRODUCTION READY
11. **FALTA:** No menciona telemetry system COMPLETE
12. **FALTA:** No menciona Error Cards system
13. **FALTA:** No menciona Deprecation tracking
14. **FALTA:** No menciona ctx plan, ctx eval-plan comandos nuevos

**Step 2: Collect verified information**

From pyproject.toml:
- ✅ typer[all]>=0.9.0
- ✅ pydantic>=2.0
- ✅ pyyaml>=6.0
- ✅ tree-sitter>=0.23.0
- ✅ tree-sitter-python>=0.23.0
- ✅ pytest>=7.0
- ✅ ruff, mypy, pyright==1.1.407
- ✅ bandit[toml]>=1.7.0
- ✅ safety>=2.0.0
- ✅ jupyter, plotly, pandas, kaleido (telemetry optional)

From Makefile:
- ✅ `make install` → uv sync
- ✅ `make test-unit` → pytest -q tests/unit
- ✅ `make test-integration` → pytest -q tests/integration
- ✅ `make test-acceptance` → pytest -q tests/acceptance -m "not slow"
- ✅ `make test-acceptance-slow` → pytest -q tests/acceptance -m "slow"
- ✅ `make test-roadmap` → pytest -q tests/roadmap
- ✅ `make gate-all` → test-unit + test-integration + test-acceptance
- ✅ `make audit` → gate-all + audit checks

From session.md (2026-01-04):
- ✅ AST M1 SkeletonMapBuilder - PRODUCTION READY (2026-01-03)
- ✅ Telemetry system - COMPLETE (2025-12-31) with report, export, chart
- ✅ LSP daemon - Relaxed READY contract (2026-01-02)
- ✅ Error Cards - SEGMENT_NOT_INITIALIZED (2026-01-02)
- ✅ Deprecation tracking - TRIFECTA_DEPRECATED env var (2026-01-02)
- ✅ Pre-commit gates - zero side-effects (2026-01-03)

---

## Task 2: Update Metadata Section

**Files:**
- Modify: `_ctx/agent_trifecta_dope.md` (lines 1-7)

**Step 1: Replace YAML frontmatter**

OLD:
```yaml
---
segment: .
scope: Verification
repo_root: /Users/felipe_gonzalez/Developer/agent_h
last_verified: 2026-01-01
default_profile: impl_patch
---
```

NEW:
```yaml
---
segment: .
scope: Verification
repo_root: /workspaces/trifecta_dope
last_verified: 2026-01-05
default_profile: impl_patch
python_version: ">=3.12"
package_manager: uv
---
```

---

## Task 3: Update Tech Stack Section

**Files:**
- Modify: `_ctx/agent_trifecta_dope.md` (Tech Stack section, ~18-35 líneas)

**Step 1: Replace with detailed versions**

Replace OLD:
```markdown
**Frameworks:**
- Typer (CLI Framework)
- Pydantic (Data Models/Schema)
- PyYAML (Artifacts parsing)

**LSP Infrastructure (Phase 3):**
- Daemon: UNIX Socket IPC, Single Instance (Lock), 180s TTL.
- Fallback: AST-only if daemon warming/failed.
- Audit: No PII, No VFS, Sanitized Paths.

**Herramientas:**
- uv (Project Management)
- pytest (Testing)
- ruff (Linting/Formatting)
- mypy (Static Types)
```

With NEW:
```markdown
**Core Dependencies:**
- typer[all]>=0.9.0 (CLI Framework)
- pydantic>=2.0 (Data Models/Schema)
- pyyaml>=6.0 (Artifacts parsing)
- tree-sitter>=0.23.0 (AST Parsing)
- tree-sitter-python>=0.23.0 (Python Language Support)

**Dev Dependencies:**
- pytest>=7.0 (Testing Framework)
- pytest-cov (Coverage)
- ruff (Linting/Formatting)
- mypy (Static Types)
- pyright==1.1.407 (Type Checker)
- bandit[toml]>=1.7.0 (Security Scanner)
- safety>=2.0.0 (Dependency Vulnerability Scanner)

**Telemetry Optional Dependencies:**
- jupyter>=1.0.0 (Analysis Notebooks)
- plotly>=5.18.0 (Interactive Charts)
- pandas>=2.0.0 (Data Analysis)
- kaleido>=0.2.0 (Static Image Export)

**LSP Infrastructure (STABLE):**
- Daemon: UNIX Socket IPC, Single Instance (Lock), 180s TTL
- Fallback: AST-only if daemon warming/failed
- Audit: No PII, No VFS, Sanitized Paths
- Contract: Relaxed READY (2026-01-02, verified test_lsp_ready_contract.py)

**Build System:**
- hatchling (Build Backend)
- uv (Package Manager & Environment)
```

---

## Task 4: Update Workflow Section

**Files:**
- Modify: `_ctx/agent_trifecta_dope.md` (Workflow section)

**Step 1: Replace with portable paths**

OLD:
```bash
# SEGMENT="." es válido SOLO si tu cwd es el repo target.
# Si ejecutas trifecta desde otro lugar, usa un path absoluto:
# SEGMENT="/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope"
cd /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/
# Validar entorno → Sync context → Ejecutar cambios → Validar gates
```

NEW:
```bash
# SEGMENT="." es válido SOLO si tu cwd es el repo target.
# Si ejecutas trifecta desde otro lugar, usa un path relativo o variable:
cd /workspaces/trifecta_dope/
# Workflow: Install → Search/Get → Test → Commit
make install
make ctx-search Q="instrucción específica" SEGMENT=.
make gate-all
```

---

## Task 5: Update Session Evidence Protocol

**Files:**
- Modify: `_ctx/agent_trifecta_dope.md` (Session Evidence Persistence section)

**Step 1: Replace ctx search example with instruction format**

OLD (line 56):
```bash
trifecta ctx search --segment . --query "<tema>" --limit 6
```

NEW:
```bash
# INSTRUCCIÓN (no keyword):
trifecta ctx search --segment . --query "Find documentation about how to implement X feature with examples and contracts" --limit 6
```

---

## Task 6: Update Gates Section

**Files:**
- Modify: `_ctx/agent_trifecta_dope.md` (Gates section, ~79-83 líneas)

**Step 1: Replace with Makefile shortcuts**

OLD:
```markdown
| **Unit** | `uv run pytest tests/unit/ -v` | Lógica interna |
| **Integración** | `uv run pytest tests/test_use_cases.py -v` | Flujos CLI/UseCases |
| **Daemon Tripwires** | `uv run pytest tests/integration/test_lsp_daemon.py` | Validar Lifecycle/TTL |
| **Lint** | `uv run ruff check .` | Calidad de código |
| **Type** | `uv run mypy src/` | Integridad de tipos |
| **Context** | `uv run trifecta ctx validate --segment .` | Integridad del pack |
```

NEW:
```markdown
| **Install** | `make install` | Instalar todas las dependencias |
| **Unit** | `make test-unit` | Lógica interna (tests/unit/) |
| **Integration** | `make test-integration` | Flujos CLI/UseCases (tests/integration/) |
| **Acceptance** | `make test-acceptance` | Contratos end-to-end (fast, sin @slow) |
| **Acceptance Slow** | `make test-acceptance-slow` | Tests lentos incluidos |
| **Roadmap** | `make test-roadmap` | Features en progreso |
| **Full Gate** | `make gate-all` | Unit + Integration + Acceptance (Fast) |
| **Audit** | `make audit` | Gate completo + validación de skips |
| **Lint** | `uv run ruff check .` | Calidad de código |
| **Type** | `uv run mypy src/` | Integridad de tipos |
| **Context** | `make ctx-sync` | Sincronizar context pack |
```

---

## Task 7: Add Features Section

**Files:**
- Insert BEFORE "Integration Points": New section on current features

**Step 1: Insert Features section**

```markdown
## Active Features (Verified 2026-01-04)

| Feature | Status | Verified | Commands |
|---------|--------|----------|----------|
| **AST Symbols M1** | ✅ PRODUCTION READY | 2026-01-03 | `trifecta ast symbols "sym://..."` |
| **Telemetry System** | ✅ COMPLETE | 2025-12-31 | `trifecta telemetry report/chart/export` |
| **LSP Daemon** | ✅ RELAXED READY | 2026-01-02 | Auto-invoked, 180s TTL, UNIX socket |
| **Error Cards** | ✅ STABLE | 2026-01-02 | `SEGMENT_NOT_INITIALIZED` error |
| **Deprecation Tracking** | ✅ STABLE | 2026-01-02 | `TRIFECTA_DEPRECATED` env var |
| **Pre-commit Gates** | ✅ STABLE | 2026-01-03 | Zero side-effects guaranteed |
| **ctx plan** | ✅ STABLE | NEW v2.0 | `trifecta ctx plan --segment . --task "..."` |
| **ctx eval-plan** | ✅ STABLE | NEW v2.0 | Evaluate plans against datasets |
| **Obsidian Integration** | ⚠️ EXPERIMENTAL | NONE | Not production-ready, not recommended |
```

---

## Task 8: Update Troubleshooting

**Files:**
- Modify: `_ctx/agent_trifecta_dope.md` (Troubleshooting section)

**Step 1: Replace with actual solutions**

OLD:
```markdown
| `ImportError` | `uv pip install -e .` desde el root |
```

NEW (from agent_trifecta_dope.md in attachment):
```markdown
| `ImportError` | `make install` desde el root |
| Python < 3.12 | `uv` maneja automáticamente versión correcta |
| `.env` faltante | Copiar desde `.env.example` y configurar |
| Pack Stale | `make ctx-sync` o `uv run trifecta ctx sync --segment .` |
| Tests Fallan | Revisar logs en `_ctx/telemetry/` |
| CLI no funciona | `uv run trifecta --help` (no requiere activar entorno) |
| Telemetry tools | `uv sync --extra telemetry` para jupyter/plotly |
```

---

## Task 9: Final Verification and Commit

**Files:**
- Verify: `_ctx/agent_trifecta_dope.md` (entire file)
- Commit with message

**Step 1: Verify no stale paths**

Run: `grep -c "Users/felipe" _ctx/agent_trifecta_dope.md || echo "✅ No stale paths"`
Expected: Zero matches

**Step 2: Verify metadata updated**

Run: `head -10 _ctx/agent_trifecta_dope.md | grep "last_verified\|repo_root"`
Expected: `last_verified: 2026-01-05` and `/workspaces/trifecta_dope`

**Step 3: Verify features section exists**

Run: `grep -A 2 "Active Features" _ctx/agent_trifecta_dope.md`
Expected: Table with AST, telemetry, LSP, Error Cards, Deprecation tracking

**Step 4: Verify Makefile commands**

Run: `grep -c "make install\|make test-\|make gate-all\|make audit" _ctx/agent_trifecta_dope.md`
Expected: ≥ 8 references to make commands

**Step 5: Commit**

```bash
git add _ctx/agent_trifecta_dope.md
git commit -m "docs: update agent_trifecta_dope.md for CLI v2.0 and current features

- Update metadata: repo_root to /workspaces, last_verified to 2026-01-05
- Add dependencies versions: typer, pydantic, tree-sitter, bandit, safety, etc.
- Add telemetry optional deps: jupyter, plotly, pandas, kaleido
- Update Workflow section with portable paths (no /Users/...)
- Update Session Evidence Protocol with instruction format example
- Replace pytest commands with Makefile shortcuts (make install, make gate-all, etc.)
- Add new 'Active Features' section with AST M1, telemetry, LSP, Error Cards status
- Update Troubleshooting with real solutions (uv sync --extra telemetry, etc.)
- Mark Obsidian integration as EXPERIMENTAL

Verified against: session.md (2026-01-04), pyproject.toml, Makefile"
```

---

## Summary

**Changes:**
- 1 metadata update (repo_root, last_verified, python_version, package_manager)
- 1 tech stack expansion (detailed versions + new deps)
- 2 path updates (Workflow + Session protocol)
- 1 gates modernization (pytest → Makefile)
- 1 new section (Active Features)
- 1 troubleshooting refresh

**Lines:** Expected ~170-180 lines (was ~100 lines, adding ~80 lines)

**Verification required:** No stale paths, metadata updated, features table present, Makefile commands prevalent

---

**EXECUTION PLAN READY**

Options:
1. **Subagent-Driven** - Fresh subagent per task (8 tasks)
2. **This Session** - Implement sequentially with verification

Which approach?
