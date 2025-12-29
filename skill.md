---
name: .
description: Use when working on Verification
---

# .

## Overview
Verification

**Ubicación**: `/Users/felipe_gonzalez/Developer/agent_h/./`

## ⚠️ ONBOARDING OBLIGATORIO ⚠️

1. **skill.md** (este archivo) - Reglas y roles
2. **[PRIME](./_ctx/prime_..md)** - Docs obligatorios
3. **[AGENT](./_ctx/agent.md)** - Stack técnico y gates

> NO ejecutes código sin leer los 3 archivos.

## Core Rules
1. **Sync First**: Valida `.env` antes de cambios
2. **Test Locally**: Tests del segmento antes de commit
3. **Read Before Write**: Lee código antes de modificar
4. **Document**: Actualiza `session_..md`

## CRITICAL PROTOCOL: History Persistence
Antes de ejecutar cualquier herramienta, DEBES seguir este estricto orden de operaciones.

1. **GENERA** el historial y resumen de la conversación en formato YAML.
2. **ESCRIBE** (usando `write_file`) este contenido en: `/Users/felipe_gonzalez/Developer/agent_h/./_ctx/session_..md`
3. **LEE** el contenido que acabas de preparar (o úsalo de tu memoria).
4. **EJECUTA** el script de ingestión de trifecta (ej: `python scripts/ingest_trifecta.py --segment .`) pasando ese contenido como el prompt instruction del agente al iniciar tareas.

## Workflow
```bash
cd /Users/felipe_gonzalez/Developer/agent_h/.
# Validar entorno → Ejecutar tests → Hacer cambios → Commitear
```

## Setup

**Python:**
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt  # o: uv pip install -r requirements.txt
```

**Node:**
```bash
npm install  # o: pnpm install
```

## Commands

**Tests:**
```bash
pytest tests/unit/ -v              # Unitarios
pytest tests/unit/test_..py -k "test_name"
pytest --cov=src tests/             # Con coverage
```

**Lint:**
```bash
# Python
ruff check . --fix && black .
# Node
npm run lint && npm run format
```

## Troubleshooting
| Problema | Solución |
|----------|----------|
| `ImportError` | `pip install -e .` desde repo root |
| `.env` faltante | Copiar desde `.env.example` |
| Lint errors | `ruff check . --fix` o `npm run lint:fix` |
| TypeError | Check versiones de dependencias |

## Integration Points
**Upstream:** <!-- listar -->
**Downstream:** <!-- listar -->
**API:** <!-- contratos si aplica -->

## Resources (On-Demand)
- `@_ctx/prime_..md` - Docs obligatorios
- `@_ctx/agent.md` - Stack y configuración
- `@_ctx/session_..md` - Log de cambios

## LLM Roles
| Rol | Modelo | Uso |
|-----|--------|-----|
| **Worker** | `deepseek-reasoner` | General |
| **Senior** | `claude-sonnet-4-5` | Complejo |
| **Fallback** | `gemini-3.0-flash-preview` | Fallos |

---
**Profile**: `impl_patch` | **Updated**: 2025-12-29
