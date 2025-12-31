# Plan: Reducir Zero-Hits sin Convertir PCC en RAG

> **Objetivo**: Reducir zero-hits a <20% sin embeddings ni RAG
> **Enfoque**: Mejorar routing y fallback usando PRIME (Progressive Context Compression)
> **Fecha inicio**: 2025-12-31

---

## Contexto

**Problema Actual** (del diagnóstico ANTES):
- Hit rate: 31.6% (6/19 searches)
- Zero-hits: 68.4% (13/19 searches)
- 89.5% de queries clasificadas como "unknown" (sin keywords claras)

**Restricciones Críticas**:
- ❌ NO embeddings
- ❌ NO vector DB
- ❌ NO "indexar src/* por defecto"
- ❌ NO "mejorar recall metiendo más corpus"
- ✅ SOLO mejorar routing y fallback (PCC)

---

## Tasks

### ✅ A) Diagnóstico de Telemetría ANTES

**Status**: COMPLETADO

**Archivos**:
- `scripts/telemetry_diagnostic.py` - Script reproducible
- `docs/plans/telemetry_before.md` - Reporte ANTES

**Comando de reproducción**:
```bash
python3 scripts/telemetry_diagnostic.py --segment .
python3 scripts/telemetry_diagnostic.py --segment . --output docs/plans/telemetry_before.md
```

**Resultados clave**:
- total_searches: 19
- hits: 6
- zero_hits: 13
- hit_rate: 31.6%
- Top zero-hit: "parser" (2x)

---

### ✅ B) Implementar ctx.stats

**Status**: COMPLETADO

**Archivos creados/modificados**:
- `src/application/use_cases.py` - Agregado `StatsUseCase`
- `src/infrastructure/cli.py` - Agregado comando `ctx stats`

**Comando**:
```bash
trifecta ctx.stats --segment . --window 30
```

**Output**:
- Resumen general (total_searches, hits, zero_hits, hit_rate, avg_latency_ms)
- Top zero-hit queries (top 10)
- Breakdown por query_type (meta/impl/unknown)
- Breakdown por hit_target (skill/prime/session/agent/other)

---

### ⏳ C) Implementar ctx.plan

**Objetivo**: Planificación usando SOLO PRIME (no RAG)

**Spec**:
```bash
trifecta ctx.plan --segment <path> --task "<texto>"
```

**C1) Fuente ÚNICA**: PRIME
- Leer `_ctx/prime_*.md`
- PRIME debe exponer:
  - `index.entrypoints`: puntos de entrada (paths + razón)
  - `index.feature_map`: feature → {chunk_ids, paths, keywords}

**C2) Salida JSON + legible**:
```json
{
  "selected_feature": "string|null",
  "plan_hit": true|false,
  "chunk_ids": ["chunk:abc", "chunk:def"],
  "paths": ["src/file.py", "docs/feature.md"],
  "next_steps": [
    {"action": "read", "target": "src/file.py"},
    {"action": "implement", "target": "function X"}
  ],
  "budget_est": {"tokens": 1500, "why": "2 chunks + implementation"}
}
```

**C3) Telemetría nueva**:
```json
{
  "event": "ctx.plan",
  "plan_hit": true|false,
  "selected_feature": "feature_name",
  "task_hash": "sha256(task)",
  "returned_chunks_count": 2,
  "returned_paths_count": 1,
  "latency_ms": 45
}
```

**Archivos a crear/modificar**:
- `src/application/plan_use_case.py` - Nuevo
- `src/infrastructure/cli.py` - Agregar comando `ctx plan`
- `_ctx/prime_trifecta_dope.md` - Agregar index.entrypoints y index.feature_map

---

### ⏳ D) Acceptance Gate

#### D1) Dataset de Evaluación

**Archivo**: `docs/plans/t9_plan_eval_tasks.md` o `.json`

**20 tareas totales**:
- 10 meta (how/what/where/plan/guide)
- 10 impl (function/class/method/file/code)

**Ejemplos**:

Meta tasks:
1. "how does the context pack build process work?"
2. "what is the architecture of the telemetry system?"
3. "where are the CLI commands defined?"
4. "plan the implementation of token tracking"
5. "guide me through the search use case"
6. "overview of the clean architecture layers"
7. "explain the telemetry event flow"
8. "design a new ctx.stats command"
9. "status of the context pack validation"
10. "description of the prime structure"

Impl tasks:
1. "implement the stats use case function"
2. "find the SearchUseCase class"
3. "code for telemetry.event() method"
4. "symbols in cli.py for ctx commands"
5. "files in src/application/ directory"
6. "function _estimate_tokens implementation"
7. "class Telemetry initialization"
8. "import statements in telemetry_reports.py"
9. "method flush() implementation details"
10. "code pattern for use case execute"

#### D2) Baseline con ctx.search

```bash
for task in "${tasks[@]}"; do
  trifecta ctx search -s . --query "$task" --limit 5
done | tee baseline_results.txt
```

Métricas:
- % zero_hits
- % hits

#### D3) Evaluación con ctx.plan

```bash
for task in "${tasks[@]}"; do
  trifecta ctx.plan -s . --task "$task"
done | tee plan_results.txt
```

Métricas:
- % plan_hit
- % zero_hits resultante (search puede seguir igual)

#### D4) Reporte ANTES/DESPUÉS

**Archivo**: `docs/plans/telemetry_before_after.md`

Contenido:
- Tabla comparativa
- Outputs literales (pegados o como anexos)

---

### ⏳ E) Criterio de Aceptación

**Meta**: `ctx.plan` reduce zero-hits a <20% en el set de 20 tareas

- WITHOUT: mejorar ctx.search
- WITHOUT: embeddings

---

## Restricciones de Cambio

**Archivos permitidos**:
- `src/infrastructure/cli.py` - stats, plan commands
- `src/application/use_cases.py` - StatsUseCase, PlanUseCase
- `src/application/plan_use_case.py` - Nuevo
- `_ctx/prime_*.md` - index.entrypoints, index.feature_map
- `scripts/telemetry_diagnostic.py` - Ya creado
- `docs/plans/` - Reportes y dataset

**NO permitido**:
- Cambiar arquitectura fuera de estos archivos
- Introducir dependencias pesadas
- Modificar scripts deprecados

---

## Handoff / Contexto Reanudación

**Estado actual**:
- Token tracking: ✅ COMPLETADO
- Diagnóstico ANTES: ✅ COMPLETADO
- ctx.stats: ⏳ PENDIENTE
- ctx.plan: ⏳ PENDIENTE
- Evaluación: ⏳ PENDIENTE

**Próximo paso inmediato**:
Implementar `ctx.stats` command en CLI

**Contexto técnico**:
- CLI framework: Typer
- Telemetry: `_ctx/telemetry/events.jsonl`
- Heurísticas ya definidas en `scripts/telemetry_diagnostic.py`
- Prime file: `_ctx/prime_trifecta_dope.md`

**Comandos útiles**:
```bash
# Ver eventos
tail -20 _ctx/telemetry/events.jsonl | jq .

# Generar diagnóstico
python3 scripts/telemetry_diagnostic.py --segment .

# Sync context
trifecta ctx sync -s .
```

---

**Última actualización**: 2025-12-31 @ Token tracking completado
