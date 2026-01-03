---
name: trifecta_dope
description: Use when working on Verification
---
## Overview
Verification

**Ubicación**: `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/`

## ⚠️ ONBOARDING OBLIGATORIO ⚠️

1. **skill.md** (este archivo) - Reglas y roles
2. **[PRIME](./_ctx/prime_trifecta_dope.md)** - Docs obligatorios
3. **[AGENT](./_ctx/agent.md)** - Stack técnico y gates
4. **[SESSION](./_ctx/session_trifecta_dope.md)** - Log de handoffs y estado actual

> NO ejecutes código ni hagas cambios sin leer los 4 archivos.

## Core Rules
1. **Sync First**: Valida `.env` antes de cambios
2. **Test Locally**: Tests del segmento antes de commit
3. **Read Before Write**: Lee código antes de modificar
4. **Document**: Actualiza `session_..md`

### Session Evidence Protocol

1. **Persist**: `trifecta session append --segment . --summary "<task>"`
2. **Sync**: `trifecta ctx sync --segment .`
3. **Execute**: `ctx search` → `ctx get`
4. **Record**: `trifecta session append --segment . --summary "Completed <task>"`

> Ver [agent.md](./_ctx/agent_trifecta_dope.md) para comandos completos y protocolos detallados.

Prohibido:
- YAML de historial largo
- rutas absolutas fuera del segmento
- ejecutar scripts legacy de ingestion
- "fallback silencioso"
- continuar con pack stale

## When to Use

- Cuando necesites sincronizar o validar el contexto de un segmento.
- Al realizar un handoff entre sesiones (registrar en `session.md`).
- Para buscar información específica en el pack de contexto sin cargar archivos completos.

## Core Pattern

### The Context Cycle (Search -> Get)
1. **Search**: Encuentra el `chunk_id` relevante.
2. **Get (Excerpt)**: Lee un resumen/inicio para confirmar relevancia.
3. **Get (Raw)**: Carga el contenido completo solo si es necesario y cabe en el presupuesto.

### Session Persistence

> [!IMPORTANT]
> **Todo** cambio significativo o comando ejecutado **DEBE** ser registrado en `session.md` para mantener la continuidad del agente. Sin esto, el sistema Trifecta es solo un CLI; la persistencia es lo que permite la colaboración multi-agente funcional.

## Common Mistakes

- **Indexar código**: El pack es para DOCS (`.md`). El código se accede vía prime links.
- **Ignorar validaciones**: Continuar si `ctx validate` falla es una violación crítica.
- **Presupuesto excedido**: Intentar cargar más de 1200 tokens en un solo turno degrada la atención del agente.
- **Rutas absolutas**: Siempre usa rutas relativas al segmento o al repo root.



---
**Profile**: `impl_patch` | **Updated**: 2025-12-29
