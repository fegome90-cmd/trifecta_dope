---
segment: trifecta_dope
scope: Scope
repo_root: .
last_verified: 2026-03-06
default_profile: impl_patch
---

# Agent Context - Trifecta_Dope

## Source of Truth
| Seccion | Fuente |
|---------|--------|
| LLM Roles | [skill.md](../skill.md) |
| Governance | [AGENTS.md](../AGENTS.md) |

## Tech Stack
**Lenguajes:**
- <!-- Ej: Python 3.12+, TypeScript 5.x -->

**Frameworks:**
- <!-- Ej: FastAPI, Pydantic v2 -->

**Herramientas:**
- <!-- Ej: pytest, ruff, uv -->

## Gates (Comandos de Verificacion)

**Unit Tests:**
```bash
pytest tests/unit/ -v
```

**Linting:**
```bash
ruff check .
```

**Type Checking:**
```bash
mypy src/
```

## Resilience Boundaries
- **Message Cap**: 5,000 messages (Circular Buffer)
- **Disk Safety**: 60s TTL for ephemeral handoffs in `.ai/traces/`

## Deep Intelligence Persistence
- **Symbol Graph**: `_ctx/graph.db` (SQLite)
- **AST Cache**: `.trifecta/cache/ast_cache_*.db` (SQLite)
- **LSP Socket**: `/tmp/trifecta_lsp_<id>.sock` (Unix Domain Socket)
