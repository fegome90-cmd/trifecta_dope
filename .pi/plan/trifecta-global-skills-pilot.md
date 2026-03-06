# Plan Paralelo: Global Skills Pilot (Trifecta)

**Feature**: `trifecta-global-skills-pilot`
**Fecha**: 2026-03-05
**Complexity**: `MEDIUM`
**Status**: `PENDING`
**Tipo**: Piloto paralelo al plan `trifecta-global-architecture`

---

## 1. Restatement de Requerimiento

Habilitar una prueba donde los agentes usen trifecta en modo global para apuntar a una carpeta agregada con todas las skills del sistema, permitiendo invocarlas con una sola búsqueda.

**Objetivo del piloto**:
- No reemplazar arquitectura actual.
- Activar un índice/búsqueda global de skills.
- Validar que agentes encuentran skills más rápido con una sola consulta.

---

## 2. Supuestos y Preguntas Abiertas

### Supuestos
- Existe acceso local a rutas de skills:
  - `~/.pi/agent/skills/`
  - `~/.agents/skills/`
- Trifecta puede indexar directorios arbitrarios vía `ctx sync/search/get`.
- El piloto puede vivir en un workspace separado (sin tocar repos productivos).

### Preguntas abiertas
1. ¿El índice será solo lectura o también permitirá instalar/actualizar skills?
2. ¿Qué profundidad de indexación se quiere (solo SKILL.md vs recursos completos)?
3. ¿Necesitamos ranking por prioridad/frecuencia de uso?
4. ¿Multilenguaje en búsqueda (es/en) obligatorio desde el piloto?

---

## 3. Fases de Implementación (Piloto)

### Fase A — Segmento piloto global de skills
**Responsable**: agente ejecutor principal.
**Done criteria**: segmento creado + `_ctx/trifecta_config.json` presente + `ctx sync` inicial exitoso.

1. Crear un segmento trifecta dedicado (ej: `~/.trifecta/segments/skills-hub`).
2. Inicializar con `trifecta create --segment <skills-hub> --scope "Global Skills Hub"`.
3. Definir inventario de fuentes de skills con alcance explícito:
   - `~/.pi/agent/skills/`
   - `~/.agents/skills/`
   - `~/.claude/skills/` (si existe)
4. Excluir explícitamente paths no-skill (`node_modules`, `__pycache__`, `skill-evals`, `archive`).

### Fase B — Construcción del corpus unificado
1. Recolectar paths de skills fuente.
2. Crear un manifiesto único (`skills_manifest.json`) con:
   - nombre skill
   - ruta
   - descripción
   - tags
   - origen
3. Normalizar metadatos mínimos para indexación consistente.

### Fase C — Indexación y búsqueda
1. Ejecutar `trifecta ctx sync --segment <skills-hub>`.
2. Validar búsquedas de smoke test:
   - `ctx search --query "security"`
   - `ctx search --query "python testing"`
   - `ctx search --query "tmux"`
3. Verificar recuperación por `ctx get` para top hits.

### Fase D — Integración operacional para agentes
**Responsable**: agente de integración/documentación.
**Done criteria**: guideline publicado + comando de lookup documentado + fallback verificado.

1. Definir convención operativa explícita:
   - Paso 1: buscar en `skills-hub`.
   - Paso 2: si `0 hits` o error de segmento, fallback a rutas locales actuales.
2. Definir semántica de estado/exit para comandos del piloto:
   - `status=ok` + exit 0: búsqueda utilizable.
   - `status=empty` + exit 0: sin resultados (activar fallback).
   - `status=error` + exit 1: error técnico (activar fallback + log).
3. Agregar guideline en AGENTS/context (sin romper flujo actual).
4. Establecer comando estándar de lookup rápido para agentes.

### Fase E — Evaluación del piloto
1. Medir latencia de búsqueda.
2. Medir precisión percibida (top-3 relevantes).
3. Medir cobertura (% skills encontrables por query representativa).
4. Decidir go/no-go para integrar en plan global principal.

---

## 4. Archivos Candidatos a Modificar

### Nuevos (piloto)
- `.pi/plan/trifecta-global-skills-pilot.md` (este plan)
- `~/.trifecta/segments/skills-hub/_ctx/skills_manifest.json`
- `~/.trifecta/segments/skills-hub/_ctx/sources.yaml`
- `~/.trifecta/segments/skills-hub/_ctx/query_pack.md` (queries de prueba)

### Potenciales (si el piloto pasa)
- `AGENTS.md` (regla de lookup global skills primero)
- docs operativas internas (flujo de descubrimiento de skills)

---

## 5. Riesgos + Mitigaciones

1. **Ruido en resultados** (muchas skills similares)
   - Mitigación: tags + ranking por origen/prioridad
2. **Indexación pesada** (latencia alta)
   - Mitigación: scope inicial limitado a SKILL.md + descripción
3. **Staleness del índice** (skills nuevas no aparecen)
   - Mitigación: sync programado + comando manual refresh
4. **Confusión con repos locales**
   - Mitigación: separar claramente `skills-hub` como segmento dedicado

---

## 6. Estrategia de Pruebas

### Smoke tests
- Búsquedas por dominio: security, python, frontend, tmux, docs
- Validar que top-3 incluye skills correctas

### Tests de regresión operativa
- Verificar que flujo actual de trabajo no se rompe
- Si skills-hub falla, fallback a rutas actuales

### Métricas del piloto
- `search_latency_ms` p50/p95
- `top3_relevance_rate`
- `coverage_rate` en set de queries representativas

---

## 7. Complejidad

**`MEDIUM`**

Justificación:
- Es paralelo, aislado y reversible.
- Requiere normalización e indexación de múltiples fuentes.
- No requiere migrar arquitectura core para validar valor.

---

## 8. Criterios de Éxito del Piloto

- `ctx sync` del skills-hub estable y repetible.
- Queries representativas encuentran skill correcta en top-3 en >=80% casos.
- Latencia p95 aceptable para uso interactivo.
- Integración con agentes sin romper flujo actual.

---

## 9. Salida esperada para decisión

Al finalizar piloto:
1. Reporte de métricas
2. Lista de ajustes necesarios
3. Recomendación: `GO` / `NO-GO` para fusionar al plan global principal

---

## 10. Observabilidad, Errores y Logs Estructurados

### 10.1 Eventos mínimos del piloto
Registrar (JSONL) por ejecución:
- `skills_hub.sync` (status, duración, cantidad de chunks)
- `skills_hub.search` (query, status, hits, duración)
- `skills_hub.fallback` (reason: empty|error, ruta fallback)

Campos recomendados:
- `ts`, `run_id`, `cmd`, `status`, `timing_ms`, `segment`, `query`, `hits`, `fallback_reason`

### 10.2 Checklist de errores
1. Segmento inexistente (`skills-hub` no creado) → crear segmento + reintentar.
2. Sync fallido (`ctx sync`) → revisar `sources.yaml` y paths inexistentes.
3. 0 resultados constantes → validar exclusiones excesivas o manifiesto incompleto.
4. Error de permisos en rutas home → validar `chmod`/ownership.
5. Latencia alta p95 → reducir corpus inicial o mejorar filtros.

### 10.3 Contrato de fallback (operacional)
- Si búsqueda devuelve `status=empty` → fallback local obligatorio.
- Si búsqueda devuelve `status=error` → fallback local obligatorio + log de incidente.
- Si búsqueda devuelve `status=ok` con hits > 0 → no fallback.

---

## 11. Scope de Quality Gates del Piloto

Para evitar ruido de stacks no relacionados:
- Gate principal del piloto: `uv run pytest` (tests del piloto/plan).
- Opcional repo-wide: `uv run mypy src/ --strict` y `uv run ruff check src/`.
- No bloquear piloto por gates fuera de scope (por ejemplo `bun run lint`), salvo que el piloto toque código JS/TS.

---

## 12. Checklist de implementación (atómico)

- [ ] A1 Crear segmento `skills-hub`.
- [ ] A2 Definir `sources.yaml` + exclusiones.
- [ ] B1 Generar `skills_manifest.json`.
- [ ] C1 Ejecutar `ctx sync` exitoso.
- [ ] C2 Ejecutar query pack y guardar métricas.
- [ ] D1 Publicar guideline de uso + fallback.
- [ ] E1 Reporte final con `GO/NO-GO`.

