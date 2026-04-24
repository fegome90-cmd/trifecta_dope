# Proposal: WO-0043 — GraphStore como Señal Derivada del Oracle

## Veredicto

Conectar el GraphStore SQLite existente como señal relacional opcional del Oracle, exclusivamente para clases de consultas estructurales que PRIME+AST no resuelve. No se reemplaza nada. No se agrega autoridad nueva. No se tocan embeddings.

## 1. Problem Statement

### Qué resuelve mal hoy PRIME+AST

PRIME busca por keywords en títulos y cuerpos de chunks. AST extrae símbolos de un solo archivo (el top hit). Juntos no pueden responder:

| Query real | Qué falla |
|---|---|
| "quién llama a `SearchOracleUseCase.execute`" | PRIME devuelve docs sobre el Oracle. No sabe quién lo invoca. |
| "cadena de llamadas desde `cli.py` hasta `GraphStore.search_nodes`" | PRIME no tiene edges. AST sólo ve un archivo. |
| "todos los archivos que importan `ContextService`" | PRIME indexa chunks de documentación, no imports. |
| "funciones en `src/infrastructure/` que dependen de `src/domain/`" | Cruce archivo-límite. PRIME no tiene dependencias estructurales. |
| "qué funciones públicas expone el módulo X" | PRIME puede listar títulos pero no distingue public/private. |

### Qué sí justifica usar el grafo

Consultas con **predicado relacional** — donde la respuesta exige conocer quién llama a quién, qué importa qué, o cómo se conectan módulos entre sí. El grafo tiene nodes + edges. PRIME+AST no.

### Qué NO intenta resolver esta fase

- Búsqueda semántica por significado ("cómo manejo errores en la capa de aplicación")
- Ranking de relevancia por contenido
- Reemplazo del pipeline PRIME→AST→LSP
- Queries que PRIME ya resuelve bien (búsqueda de docs por keyword)

## 2. Non-Goals

- **No reemplazar `context_pack.json`**. Es el SSOT del hot path. Permanece intacto.
- **No convertir SQLite en SSOT**. GraphStore es un índice derivado, regenerable, no autoritativo.
- **No introducir embeddings/vector store**. Explícitamente postergado. No se agrega ninguna dependencia nueva.
- **No usar el grafo como señal universal**. Sólo se activa para queries con predicado relacional detectable.
- **No tocar el hot path F1**. El daemon, el context_service, y el fallback mode quedan como están.
- **No agregar capas de abstracción**. Se usa el `GraphStore` existente directamente.

## 3. Authority Model

```
context_pack.json  ←  AUTORIDAD ÚNICA del hot path
        |
        | (alimenta)
        v
   Oracle F1  ←  PRIME + AST + LSP (sin cambios)
        |
        | (consulta derivada, condicional)
        v
   GraphStore  ←  DERIVADO, REGENERABLE, NO AUTORITATIVO
```

**Reglas de autoridad:**

1. `context_pack.json` es la única fuente de verdad para contexto de documentación.
2. `GraphStore` se genera a partir del AST del código fuente (`GraphIndexer`). No tiene información que no exista en el código.
3. Si el grafo no existe, está corrupto, o excede el presupuesto de latencia → se ignora. No fallback a grafo.
4. Nunca se usa el grafo para validar o contradecir a PRIME.
5. El grafo se puede regenerar con `trifecta graph index` sin pérdida de datos.

**Split-brain prevention:**
- El grafo no almacena contenido de chunks — solo nombres, tipos, líneas, y relaciones.
- No hay overlap de autoridad: PRIME tiene docs, el grafo tiene estructura.
- Si hay inconsistencia entre grafo y código, se regenera el grafo. Punto.

## 4. Routing Model

### Queries que activan el grafo

Patrones detectables en el query:

| Patrón | Ejemplo | Señal activada |
|---|---|---|
| `who calls X` / `callers of X` | "quién llama a execute" | `GraphStore.get_callers()` |
| `what does X call` / `callees of X` | "qué llama ContextService" | `GraphStore.get_callees()` |
| `imports X` / `dependents of X` | "quién importa graph_models" | edge_kind="imports" (enrichment fase 2) |
| `call chain X to Y` | "cadena de cli.py a search_nodes" | Travesía multi-hop (enrichment fase 2) |

### Queries que permanecen en F1 fallback mode

Todo lo demás. Específicamente:
- Búsqueda de documentación por keyword
- Preguntas sobre configuración, comandos, workflows
- Queries donde no se detecta predicado relacional
- Queries donde el símbolo target no se resuelve en el grafo

### Degradación

```
query llega → ¿tiene predicado relacional?
    NO  → F1 fallback normal (PRIME+AST+LSP)
    SÍ  → ¿grafo disponible?
        NO  → F1 fallback normal + metadata: {"graph_signal": "unavailable"}
        SÍ  → ¿resolución de target < 10ms?
            NO  → F1 fallback normal + metadata: {"graph_signal": "timeout"}
            SÍ  → ejecutar query relacional
                  → agregar resultado como campo derivado en OracleResult
```

El grafo NUNCA bloquea el pipeline. Es best-effort con presupuesto.

## 5. Minimal Enrichment Scope

### Qué se agrega primero (Fase 1)

Nada en el schema. El `GraphStore` actual ya tiene todo lo necesario:
- `nodes` con `symbol_name`, `qualified_name`, `kind`, `file_rel`, `line`
- `edges` con `from_node_id`, `to_node_id`, `edge_kind="calls"`
- `search_nodes()` con fuzzy search
- `get_callers()` / `get_callees()` con traversal

**Lo único que falta es el wiring** — conectar `GraphService` al `SearchOracleUseCase` como señal condicional.

### Qué queda fuera por ahora

| Enrichment | Por qué queda fuera |
|---|---|
| `metadata_json` con docstrings | No necesario para callers/callees. Agregar después si el wiring demuestra valor. |
| edge_kind="imports" | El `GraphIndexer` actual solo extrae "calls". Agregar imports requiere cambiar el collector. Fase 2. |
| Travesía multi-hop | `get_callers`/`get_callees` son 1-hop. N- Hopkins requiere query recursiva. Fase 2. |
| Type references | Extraer tipos de parámetros/returns del AST. Fase 2. |

### Justificación del scope mínimo

El wiring puro (sin enrichment) basta para validar:
1. ¿El agente usa la señal relacional cuando está disponible?
2. ¿Mejora la calidad de las respuestas para queries de "quién llama a X"?
3. ¿El overhead de latencia es aceptable?

Si la respuesta a las 3 es sí → justifica el enrichment de fase 2. Si no → se elimina sin haber invertido en schema changes.

## 6. Latency and Reliability Gates

### Presupuesto por query con grafo

| Operación | Presupuesto | Nota |
|---|---|---|
| Detección de predicado relacional | < 1ms | Pattern matching en el query string |
| Resolución de target en grafo | < 10ms | `find_target_candidates()` es indexed lookup |
| Caller/callee traversal | < 5ms | Indexed JOIN en SQLite |
| **Total grafo** | **< 15ms** | |
| **Total Oracle + grafo** | **< 65ms** | F1 baseline ~50ms + 15ms grafo |

### Estrategia de fallback

- Timeout por operación: cada operación del grafo tiene un budget individual.
- Si cualquier operación excede su budget → se descarta el resultado del grafo.
- El OracleResult incluye `metadata.graph_signal` con estado: `"used"`, `"unavailable"`, `"timeout"`, `"no_predicate"`.

### Requisitos de consistencia

- El grafo se regenera on-demand con `trifecta graph index`.
- No hay consistencia eventual entre context_pack y grafo — son artefactos independientes.
- Si el grafo tiene más de 7 días sin re-indexar → `probe_status()` reporta `stale=true` y se omite.

## 7. Evaluation Plan

### Benchmark orientado a queries relacionales reales

Conjunto de 20 queries divididas en 4 clases:

| Clase | Queries | Ejemplo |
|---|---|---|
| Caller | 5 | "quién llama a `SearchOracleUseCase.execute`" |
| Callee | 5 | "qué funciones llama `ContextService.search`" |
| No-relacional | 5 | "cómo configuro el daemon" (control: NO debe activar grafo) |
| Ambigua | 5 | "context service" (border case: keyword que también es símbolo) |

### Métricas

| Métrica | Target | Cómo se mide |
|---|---|---|
| Routing accuracy | 100% no-relacional no activa grafo | Inspección de `metadata.graph_signal` |
| Caller recall | ≥1 caller para queries con target existente | Conteo de nodos devueltos vs. grep manual |
| Latencia p95 | <65ms con grafo activo | Benchmark 100 runs |
| Fallback correctness | 0 regresiones vs. F1 baseline sin grafo | A/B comparison |

### Cómo demostrar valor

Para cada query relacional, comparar:
- **Sin grafo**: PRIME devuelve docs sobre el símbolo, AST devuelve su firma. El agente NO sabe quién lo llama.
- **Con grafo**: Oracle devuelve lo mismo + lista de callers con archivo y línea.

Si el agente no usa la información de callers para responder mejor → el grafo no aporta valor y se desactiva.

## 8. Rollout Plan

### Fase 0: Propuesta y Benchmark (esta fase)
- Aprobar esta propuesta
- Ejecutar benchmark con queries reales contra GraphStore existente
- Producir reporte con métricas de la sección 7
- **Kill criterion**: Si routing accuracy <95% o latencia p95 >80ms → NO seguir.

### Fase 1: Wiring Opcional por Routing
- Agregar `GraphService` como dependencia opcional en `SearchOracleUseCase.__init__`
- Implementar detección de predicado relacional (pattern matching)
- Agregar `graph_signal` a `OracleResult.metadata`
- Tests unitarios del routing
- Tests de integración del wiring
- **Kill criterion**: Si <3 de 5 queries caller/callee devuelven resultados útiles → NO seguir a fase 2.

### Fase 2: Enrichment Incremental (solo si Fase 1 demuestra valor)
- Agregar edge_kind="imports" al `GraphIndexer`
- Agregar docstrings a `metadata_json`
- Implementar N-hop traversal
- Agregar detección de "call chain" queries
- **Kill criterion**: Si el enriquecimiento no aumenta el recall en ≥30% → detener.

### Postergadas Explícitamente

| Feature | Razón de postergación |
|---|---|
| Embeddings / Vector store | Requiere dependencia nueva, modelo de embeddings, y justificación de storage. Evaluar solo si Fases 0-2 demuestran que el grafo relacional aporta valor insuficiente. |
| Cross-repo graph | Fuera de scope. El grafo es intra-segmento. |
| Real-time graph updates | El grafo se regenera on-demand. Watcher/file observer es complejidad innecesaria ahora. |

## Scope Exacto

### Archivos a modificar

| Archivo | Cambio |
|---|---|
| `src/application/oracle_use_case.py` | Agregar `graph_service: Optional[GraphService]` al constructor. Agregar lógica de routing y consulta condicional. |
| `src/domain/context_models.py` | Agregar `graph_data: Optional[Dict]` a `OracleResult`. |

### Archivos SIN cambios

| Archivo | Razón |
|---|---|
| `src/infrastructure/graph_store.py` | Ya funciona. No se toca. |
| `src/application/graph_service.py` | Ya funciona. Se inyecta como dependencia. |
| `src/application/graph_indexer.py` | Ya funciona. No se toca en Fase 1. |
| `src/application/context_service.py` | Hot path. No se toca. |
| `src/infrastructure/cli_hybrid.py` | Hot path. No se toca. |
| `src/interfaces/mcp/server.py` | No se toca en Fase 1. |

### Tests nuevos

| Test | Qué valida |
|---|---|
| `test_graph_routing_predicate_detection` | Pattern matching detecta correctamente queries relacionales |
| `test_graph_routing_no_predicate` | Queries no-relacionales no activan grafo |
| `test_graph_signal_callers` | Caller query devuelve nodos correctos |
| `test_graph_signal_callees` | Callee query devuelve nodos correctos |
| `test_graph_signal_fallback_on_missing` | Grafo no disponible → fallback limpio |
| `test_graph_signal_fallback_on_timeout` | Grafo excede budget → fallback limpio |
| `test_oracle_latency_with_graph` | Latencia total <65ms |

## Riesgos

| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| Routing false positives: queries no-relacionales activan el grafo | Media | Pattern matching conservador. Default a NO activar. |
| Latencia del grafo excede budget en segmentos grandes | Baja | SQLite indexed queries son predecibles. Benchmark antes de wiring. |
| Grafo stale después de refactors | Alta | `probe_status()` reporta staleness. Regeneración manual barata. |
| El agente ignora la información del grafo | Media | Evaluar en Fase 0 benchmark. Si el agente no la usa → kill. |

## Acceptance Criteria

1. `SearchOracleUseCase` acepta `GraphService` opcional sin breaking changes.
2. Queries con predicado relacional retornan `graph_data` con callers/callees.
3. Queries sin predicado relacional no consultan el grafo (verificable en `metadata.graph_signal = "no_predicate"`).
4. Latencia p95 del Oracle con grafo <65ms.
5. Fallback correcto cuando grafo no disponible o stale.
6. Zero regresiones en tests existentes.
7. Zero nuevas dependencias en `pyproject.toml`.

## Kill Criteria (cuándo NO seguir)

- **Fase 0**: Si el benchmark muestra que PRIME+AST ya responde correctamente ≥80% de las queries relacionales evaluadas → el grafo no agrega valor. Cerrar WO-0043.
- **Fase 1**: Si el routing accuracy es <95% (muchos false positives o false negatives) → la detección de predicados no es confiable. Reevaluar diseño o cerrar.
- **Fase 1**: Si <3 de 5 queries caller/callee devuelven callers reales que el agente usa → la señal no es útil. Cerrar.
- **Fase 2**: Si enrichment no aumenta recall en ≥30% → el scope mínimo basta. No justifica más inversión. Cerrar.

En todos los casos, el cleanup es trivial: se elimina `graph_service` del constructor del Oracle y el campo `graph_data` del resultado. Zero estado residual.
