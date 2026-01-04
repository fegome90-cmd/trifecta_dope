# Session JSONL Backend - Critical Analysis (Braindope)

**Date**: 2026-01-04  
**Status**: PROPOSAL - Needs Critical Evaluation  
**Author**: Technical Review

---

## 🎯 La Propuesta Original

**Idea**: Crear un backend JSONL para session.md que permita:
- session.md = Log humano (puede crecer indefinidamente)
- session.jsonl = Log estructurado para queries
- CLI hook en `session append` genera ambos
- Nuevo comando `session query --type X --last N`

**Justificación**: Alineado con "context as tool", no es RAG, permite session escalable.

---

## ❌ PROBLEMAS CRÍTICOS (Los que NO te conté)

### 1. **Duplicación de Sistemas de Logging**

**PROBLEMA**: Ya existe `_ctx/telemetry/events.jsonl`.

| Sistema | Propósito | Overlap? |
|:--------|:----------|:---------|
| `telemetry/events.jsonl` | Comandos ejecutados, tools usados, latencias | ✅ Tools, commands |
| `session_journal.jsonl` (propuesto) | Task type, files touched, tools used | ⚠️ 80% overlap |

**PREGUNTA SIN RESPUESTA**: ¿Por qué necesitamos DOS sistemas? ¿No deberíamos mejorar telemetry en lugar de crear otro silo?

**RIESGO**: Mantenimiento de dos sistemas que hacen casi lo mismo = technical debt.

---

### 2. **Sincronización session.md ↔ session.jsonl**

**PROBLEMA**: Ahora tienes DOS fuentes de verdad que deben estar sincronizadas.

**Escenarios de fallo**:
- ✅ session.md escrito, ❌ JSONL falla → Pérdida de metadata estructurada
- ❌ session.md falla, ✅ JSONL escrito → Inconsistencia humano vs máquina
- ⚠️ Script background muere → ¿Cuántas entradas se pierden?

**PREGUNTA SIN RESPUESTA**: ¿Cuál es el source of truth? Si difieren, ¿a cuál crees?

**SOLUCIÓN POSIBLE**: Hacer que session.md sea generado DESDE el JSONL (single source of truth). Pero eso invierte la arquitectura.

---

### 3. **Background Script es Frágil**

**PROPUESTA**: Script `.sh` corriendo en background.

**PROBLEMAS**:
- ¿Cómo detectas si el script murió?
- ¿Cómo lo reinicias automáticamente?
- ¿supervisor? ¿systemd? ¿launchd en macOS?
- ¿Qué pasa con entradas perdidas durante downtime?

**REALIDAD**: Background processes sin supervisión son una receta para bugs silenciosos.

**ALTERNATIVA MEJOR**: Hook directo en el CLI (síncrono), no background. Pero eso añade latencia.

---

### 4. **Schema Evolution y Backwards Compatibility**

**PROBLEMA**: El schema JSONL va a cambiar con el tiempo.

**Escenarios**:
- v1: `{"task_type": "debug"}`
- v2: Añades `{"priority": "high"}`
- v3: Cambias `task_type` a `activity_type`

**PREGUNTA SIN RESPUESTA**: ¿Cómo lees entradas antiguas? ¿Migración? ¿Versionado en cada entry?

**COSTO**: Sin un plan de versionado, terminas con JSONL corrupto o muy complejo de parsear.

---

### 5. **Query Performance con Crecimiento Indefinido**

**PROPUESTA**: "session puede crecer cuanto necesite el proyecto"

**PROBLEMA**: Un archivo JSONL de 10K entradas sin índices = búsqueda O(n).

**Escenario real**:
- 6 meses de proyecto = ~500 entradas
- `session query --type debug --last 5`
- Sin índice: Lee 500 líneas, filtra, retorna 5

**REALIDAD**: JSONL sin índices no escala bien. Necesitas:
- Índices externos (ej: SQLite)?
- Límites de tamaño (ej: 1000 entradas máx)?
- Archivado periódico (contradice "puede crecer cuanto necesite")?

**TRADE-OFF NO DISCUTIDO**: Escalabilidad vs Complejidad.

---

### 6. **Tool Use Detection - ¿Quién Parsea?**

**PROPUESTA**: "se puede identificar con el post tool use"

**PROBLEMA**: ¿Quién parsea tool use?
- ¿El agente? (añade latencia al workflow)
- ¿El script background? (necesita acceso al contexto del agente)
- ¿El CLI? (necesita info que no tiene)

**REALIDAD**: `trifecta session append` recibe `--files` y `--commands` manualmente. No hay auto-detección de tool use actualmente.

**COSTO**: Implementar auto-detección = parsear output del agente = complejo y frágil.

---

### 7. **North Star Violation Potencial**

**PROPUESTA**: "session.md puede crecer cuanto necesite"

**PROBLEMA**: Esto contradice "pocos tokens, poco tiempo".

**ACLARACIÓN NECESARIA**:
- ¿session.md es para archivo humano (no se carga en prompt)?
- ¿session.jsonl es lo único que se query (máquina)?

**Si session.md NO se carga en prompt**: OK, sin problema.  
**Si session.md SÍ se carga**: Viola North Star.

**PREGUNTA SIN RESPUESTA**: ¿Cambia el contrato de uso de session.md?

---

## 🟡 PREGUNTAS QUE NECESITAN RESPUESTA

| # | Pregunta | Impacto |
|:--|:---------|:--------|
| 1 | ¿Por qué no extender telemetry en lugar de crear session_journal? | Design |
| 2 | ¿Cuál es source of truth: .md o .jsonl? | Architecture |
| 3 | ¿Cómo manejas schema evolution? | Maintenance |
| 4 | ¿Límite de tamaño del JSONL o crece indefinidamente? | Performance |
| 5 | ¿Background script o hook síncrono? | Reliability |
| 6 | ¿Auto-detección de tool use o manual? | Complexity |

---

## 🔄 ALTERNATIVAS A CONSIDERAR

### Alternativa A: Mejorar Telemetry Existente

**Idea**: Extender `_ctx/telemetry/events.jsonl` con session-level metadata.

**Pros**:
- ✅ Reutiliza infraestructura existente
- ✅ No duplica sistemas
- ✅ Ya tiene versionado de schema

**Contras**:
- ⚠️ Mezcla eventos fine-grained (commands) con coarse-grained (sessions)
- ⚠️ Telemetry puede tener propósito diferente (observability vs context)

---

### Alternativa B: Session.md como Single Source + Generator

**Idea**: session.md es el único source of truth. Script genera .jsonl DESDE .md.

**Pros**:
- ✅ No hay problema de sincronización
- ✅ session.md sigue siendo append-only

**Contras**:
- ❌ Parsing de markdown = frágil
- ❌ Estructura del .md debe ser estricta

---

### Alternativa C: SQLite en lugar de JSONL

**Idea**: `_ctx/session.db` (SQLite) en lugar de JSONL.

**Pros**:
- ✅ Queries rápidas con índices
- ✅ Schema evolution con migrations
- ✅ Transacciones (atomicidad)

**Contras**:
- ❌ No es "plain text" (menos debuggable)
- ❌ Añade dependencia (SQLite)

---

## 🎯 RECOMENDACIÓN REVISADA

**NO implementar hasta responder las 6 preguntas críticas.**

**Proceso recomendado**:
1. Documentar respuestas a las preguntas en ADR
2. Evaluar Alternativa A (extender telemetry) vs propuesta original
3. Prototipo mínimo (100 líneas) para validar supuestos
4. Revisión de diseño con evidencia del prototipo

**NO rushear a implementación sin plan de**:
- Sincronización entre .md y .jsonl
- Schema versioning
- Query performance a escala
- Supervisión de background script

---

## 📊 Scorecard de Riesgos

| Riesgo | Severidad | Mitigación |
|:-------|:----------|:-----------|
| Duplicación con telemetry | 🔴 Alta | Unificar o justificar separación |
| Sincronización .md/.jsonl | 🔴 Alta | Single source of truth |
| Background script fragility | 🟡 Media | Hook síncrono o supervisor |
| Schema drift | 🟡 Media | Versionado explícito |
| Query performance | 🟢 Baja | Límites de tamaño o índices |
| Tool use detection | 🟡 Media | Manual primero, auto después |

---

**Conclusión**: La idea tiene mérito, pero necesita más diseño. No es un "green light" automático.
