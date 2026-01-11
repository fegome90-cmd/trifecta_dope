#### ctx get --mode raw

```bash
$ uv run trifecta ctx get -s . -i "agent:abafe98332" --mode raw 2>&1 | head -60
Retrieved 1 chunk(s) (mode=raw, tokens=~1067):

## [agent:abafe98332] agent_trifecta_dope.md
---
segment: .
scope: Verification
repo_root: /Users/felipe_gonzalez/Developer/agent_h
last_verified: 2026-01-01
default_profile: impl_patch
---

# Agent Context - .

## Source of Truth

| Sección | Fuente |
|---------|--------|
| Reglas de Sesión | [skill.md](../skill.md) |
| Dependencias | `pyproject.toml` |
| Lógica Core | `src/domain/` y `src/application/` |
| Entry Points | `src/infrastructure/cli.py` |
| Estándar de Docs | `README.md` y `knowledge/` |
| Arquitectura LSP | `src/infrastructure/lsp_daemon.py` |

## Tech Stack

**Lenguajes:**
- Python 3.12+ (Backend/CLI)
- Fish Shell (Completions)

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

## Workflow
```bash
