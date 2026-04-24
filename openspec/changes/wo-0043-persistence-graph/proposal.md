# Proposal: WO-0043 — GraphStore como Señal Derivada del Oracle

## 1. Veredicto

**GO condicionado a benchmark de valor**. El wiring mecánico está implementado y verificado (`d427889c`, 35 tests, 0 regresiones). Pero la propuesta no se declara aprobada hasta que el benchmark de valor demuestre que el grafo agrega información correcta y útil que PRIME+AST no provee. Si el information gain <50% → cerrar.

## 2. Scope Ejecutivo de la Fase

**Phase 1 = one-hop callers/callees sobre `edge_kind="calls"` exclusivamente.**

El Oracle consulta GraphStore cuando detecta un predicado relacional en la query, ejecuta un traversal de 1 hop sobre edges de tipo `calls`, y agrega el resultado como campo derivado opcional en `OracleResult.graph_data`.

### Qué incluye
- Detección de predicados relacionales EN+ES (8 patterns: `who calls X`, `callers of X`, `quién llama a/al/a la X`, `what does X call`, `callees of X`, `qué llama/llaman a/al/a la X`)
- Fuzzy target resolution via `search_nodes` LIKE match
- 1-hop traversal: `get_callers()` / `get_callees()`
- 6 signal states con metadata verificable
- Degradación automática sin tocar el hot path

### Qué queda fuera explícitamente

| Feature | Razón |
|---------|-------|
| `edge_kind="imports"` | GraphIndexer solo extrae calls. Requiere collector change. |
| Multi-hop traversal (N-hop) | get_callers/get_callees son 1-hop. Recursión es fase 2. |
| Type references | Extraer tipos de parámetros/returns del AST. |
| Docstrings en metadata_json | No necesario para callers/callees. |
| Real-time graph updates | Regeneración on-demand basta. |
| Cross-segment queries | Grafo es intra-segmento. |
| Embeddings / vector store | Postergado. No se agrega dependencia. |
| Latencia del hot path F1 | No se toca. WO-0043 no resuelve latencia. |

## 3. Modelo de Autoridad

```
context_pack.json   =  AUTORIDAD ÚNICA del hot path F1
                         SSOT para búsqueda de documentación
                         
GraphStore/SQLite   =  DERIVADO, REGENERABLE, NO AUTORITATIVO
                         Generado desde AST del código fuente
                         No almacena contenido, solo estructura
```

**Contrato operativo**:

1. `context_pack.json` es la única fuente de verdad para contexto de documentación.
2. GraphStore se genera a partir del AST del código. No tiene información que no exista en el código.
3. Si el grafo falta, está stale, o excede budget → el sistema degrada a PRIME+AST sin cambiar contrato de salida.
4. El grafo nunca contradice a PRIME porque no comparten dominio: PRIME tiene docs, el grafo tiene estructura.
5. El grafo se puede eliminar y regenerar con `trifecta graph index` sin pérdida de datos.
6. No hay overlap de autoridad. No hay split-brain posible.

## 4. Routing y Degradación

### Routing

```
query → classify_query() → predicado relacional?
    NO → PRIME+AST+LSP normal (graph_signal = "no_predicate")
    SÍ → ¿graph_service disponible?
        NO → PRIME+AST+LSP normal (graph_signal = "unavailable")
        SÍ → ¿grafo existe y no stale?
            NO → PRIME+AST+LSP normal (graph_signal = "stale")
            SÍ → ¿target encontrado en <10ms?
                NO → PRIME+AST+LSP normal (graph_signal = "target_not_found" | "timeout")
                SÍ → traversal callers/callees en <5ms
                    → OracleResult.graph_data = {relation, target, nodes, latency_ms, over_budget}
                    → metadata.graph_signal = "used"
```

### Contrato de Degradación (verificable)

Cada caso de degradación registra metadata específica en `OracleResult.metadata`:

| Estado | Causa | Metadata registrada | Comportamiento |
|--------|-------|---------------------|----------------|
| `no_predicate` | Query sin predicado relacional detectable | `graph_signal_ms = 0` | Pipeline normal, grafo nunca consultado |
| `unavailable` | GraphService es None o lanza excepción | `graph_signal_ms = elapsed` | Pipeline normal |
| `stale` | Grafo no existe o indexado hace >7 días (fallback heurístico) | `graph_signal_ms = elapsed` | Pipeline normal |
| `timeout` | Target resolution o traversal excede budget | `graph_signal_ms = elapsed` | Pipeline normal |
| `target_not_found` | Fuzzy search no encuentra el símbolo | `graph_signal_ms = elapsed` | Pipeline normal |
| `used` | Traversal exitoso | `graph_signal_ms = elapsed`, `graph_data` poblado | Pipeline normal + graph_data como campo derivado |

El grafo **nunca** bloquea el pipeline. Es best-effort con presupuesto.

### Patrones soportados

| Relación | EN | ES |
|----------|----|----|
| callers | `who calls X`, `callers of X` | `quién llama a X`, `quién llama al X`, `quién llama a la X` |
| callees | `what does X call`, `callees of X` | `qué llama X`, `qué llaman al X`, `qué llaman a la X` |

### Casos negativos (NO activan grafo)

```
"how to configure the daemon"       → no_predicate
"what is context_pack.json"         → no_predicate
"show me the skill hub index"       → no_predicate
"context service"                   → no_predicate
"explain the oracle architecture"   → no_predicate
"who uses execute"                  → no_predicate (patrón no soportado)
"donde se usa init"                 → no_predicate (patrón no soportado)
"call graph of main"                → no_predicate (ambiguo: callers o callees)
"import chain cli.py to store"      → no_predicate (multi-hop, fuera de scope)
```

## 5. Gates y Thresholds Justificados

### Gate de Staleness

**Estado actual**: `_GRAPH_STALE_DAYS = 7` es un **fallback heurístico temporal**. No es un criterio robusto — no correlaciona con cambios reales en el código. Se usa porque la tabla `graph_index` solo tiene `indexed_at`, sin referencia al estado del repositorio.

**Dirección recomendada**: Agregar columna `indexed_commit` a `graph_index`. Al indexar, capturar `git rev-parse --short HEAD`. Al consultar staleness, comparar con HEAD actual. Si difiere → stale. Si no es repo git → fallback a 7 días. Esto es un **enrichment de schema** para Fase 2.

**Justificación del fallback**: 7 días es conservador. En un proyecto activo, el grafo se indexa frecuentemente. En un proyecto inactivo, 7 días es razonablemente fresco. No es ideal pero es safe-default hasta que el commit-hash esté implementado.

### Presupuesto de Latencia

| Operación | Budget | Justificación |
|-----------|--------|---------------|
| Predicate detection | <1ms | Regex sobre string. Predecible. |
| Target resolution (search_nodes) | <10ms | SQLite LIKE query con índice. Predecible para ~500 nodos. |
| Traversal (callers/callees) | <5ms | Indexed JOIN en SQLite. Predecible. |
| **Total graph signal** | **<15ms** | Basado en benchmark Phase 0: p95 = 3.7ms medido. |
| **Total Oracle + graph** | **<65ms** | F1 baseline ~50ms + 15ms graph. |

**Por qué 65ms?** El baseline Oracle sin graph es ~50ms (PRIME+AST). Agregar 15ms de graph signal mantiene el total dentro del presupuesto de un solo tool call del agente (<100ms). Si el total supera 80ms, el agente percibe latencia y el overhead no se justifica.

### Thresholds de Aceptación

| Métrica | Target | Justificación del número |
|---------|--------|--------------------------|
| Information gain | ≥70% | 70% significa que en 7 de 10 queries relacionales, el graph agrega info correcta y útil que PRIME+AST no tiene. Es un piso razonable para justificar el wiring. No es 100% porque algunas queries pueden referir símbolos que no están en el grafo. |
| Kill criterion info gain | <50% | Menos de la mitad de las queries se benefician → la señal no justifica la complejidad. El 50% es el punto donde el costo de mantenimiento (indexar, mantener fresco, testear) iguala el beneficio. |
| Routing precision | 100% para no-relacional | Un solo false positive (activar graph en query no-relacional) desperdicia budget y agrega ruido. 100% es alcanzable con classifier conservador y patrones estrechos. |
| Latencia p95 | <65ms Oracle+graph | Ver justificación arriba. |

## 6. Benchmark de Valor Ejecutable

### Metodología

Para cada query relacional Q en el conjunto de prueba:

```
1. Ejecutar Oracle(graph_service=None)  → Result_sin = {prime_chunks, ast_symbols, graph_data=None}
2. Ejecutar Oracle(graph_service=gs)    → Result_con = {prime_chunks, ast_symbols, graph_data={...}}
3. Evaluar 3 dimensiones:
   a) NOVEDAD: ¿graph_data contiene info que Result_sin no tiene?
   b) CORRECCIÓN: ¿los nodos en graph_data son callers/callees reales del target?
   c) UTILIDAD: ¿esa info responde la intención relacional del query?
```

### Conjunto de Prueba

Queries con targets que existen en el grafo actual (524 nodos, 193 edges, todos `calls`):

| # | Query | Target esperado | Relación | Tipo |
|---|-------|-----------------|----------|------|
| 1 | "who calls normalize_token" | normalize_token | callers | relacional |
| 2 | "quién llama a extract_imports" | extract_imports | callers | relacional |
| 3 | "what does compute_projection_fingerprint call" | compute_projection_fingerprint | callees | relacional |
| 4 | "callers of build_context_pack" | build_context_pack | callers | relacional |
| 5 | "qué llaman al search" | search | callees | relacional |
| 6 | "who calls nonexistent_xyz" | nonexistent_xyz | callers | target_not_found |
| 7 | "how to configure the daemon" | — | no_predicate | control negativo |
| 8 | "what is context_pack.json" | — | no_predicate | control negativo |
| 9 | "context service" | — | no_predicate | control negativo |
| 10 | "explain the oracle architecture" | — | no_predicate | control negativo |

### Métricas

| Métrica | Cómo se mide | Fórmula |
|---------|-------------|---------|
| **Information gain** | % de queries relacionales (1-5) donde graph_data agrega nodos correctos que PRIME+AST no tiene | `queries_con_gain / queries_relacionales` |
| **Corrección** | % de nodos en graph_data que son callers/callees verificados | `nodos_correctos / nodos_totales` |
| **Routing precision** | % de queries negativas (7-10) que NO activan graph | `negativos_correctos / negativos_totales` |
| **Latencia overhead** | Diferencia p95 entre Oracle+graph y Oracle sin graph | `p95_con - p95_sin` |

### Criterios de evaluación

- **Information gain ≥70%**: Al menos 3 de 5 queries relacionales muestran info nueva correcta y útil.
- **Corrección = 100%**: Todos los nodos retornados son callers/callees reales (graph indexado es determinístico).
- **Routing precision = 100%**: Ningún query negativo activa el graph.
- **Latencia overhead <15ms**: Graph signal no degrada perceptiblemente.

## 7. Acceptance Criteria

1. `SearchOracleUseCase` acepta `GraphService` opcional sin breaking changes
2. Queries con predicado relacional retornan `graph_data` con callers/callees
3. Queries sin predicado NO consultan el grafo (`graph_signal = "no_predicate"`)
4. Latencia p95 Oracle+graph <65ms
5. Fallback correcto en los 5 estados de degradación (unavailable, stale, timeout, target_not_found, no_predicate)
6. Zero regresiones en tests existentes
7. Zero nuevas dependencias
8. **Information gain ≥70%** en benchmark de valor
9. **Routing precision 100%** para queries no-relacionales
10. **Corrección 100%** de nodos retornados por el graph

## 8. Kill Criteria

| Condición | Acción |
|-----------|--------|
| Information gain <50% | Cerrar WO-0043. El wiring funciona pero no aporta valor suficiente. Cleanup: eliminar `graph_service` del Oracle y `graph_data` del result. |
| Routing precision <95% | Reevaluar classifier. Si no se puede alcanzar 95% con patterns estrechos → cerrar. |
| Latencia p95 Oracle+graph >80ms | El overhead no es justificable. Rediseñar budget o cerrar. |
| PRIME+AST ya resuelve ≥80% de queries relacionales evaluadas | El grafo es redundante. Cerrar. |

En todos los casos, cleanup es trivial: eliminar `graph_service` del constructor Oracle y `graph_data` del resultado. Zero estado residual.

## 9. Recomendación Go/No-Go para Siguiente Batch

**GO** para ejecutar el benchmark de valor definido en la sección 6.

El wiring mecánico está completo y verificado. Lo que falta es **evidencia de valor**: ejecutar las 10 queries del benchmark contra el Oracle con y sin graph, medir information gain, corrección, routing precision y latencia overhead.

Si el benchmark pasa los thresholds → WO-0043 se declara aprobado formalmente.
Si no pasa → se ejecuta cleanup (remover wiring) y se cierra el WO.

**No se amplía scope**. No se agrega enrichment. No se toca el schema del graph. El siguiente batch es exclusivamente medir y decidir.
