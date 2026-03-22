# Síntesis Final - Lanzamiento MVP Trifecta Graph

Fecha: 2026-03-13
Objetivo: Identificar bloqueos y orden de ataque para implementación MVP

---

## A. Top 5 Bloqueos Reales

### Bloqueo 1: SSOT SegmentRef Doble

| Aspecto | Detalle |
|----------|---------|
| **Evidencia** | `src/domain/segment_resolver.py` (V1, 16 call sites) vs `src/trifecta/domain/segment_ref.py` (V2, 1 call site) |
| **Severidad** | 🔴 CRÍTICO |
| **Bloquea MVP** | SÍ - identidad del grafo por segmento |
| **Toca** | SegmentRef |
| **Acción** | Confirmar V1 como SSOT, migrar `repo_ref.py`, deprecate V2 |

### Bloqueo 2: No Existe Symbol↔Chunk Linking

| Aspecto | Detalle |
|----------|---------|
| **Evidencia** | context_models.py no tiene line ranges, chunk_ids son `sha1(content)` efímeros |
| **Severidad** | 🟡 MEDIO |
| **Bloquea MVP** | NO - Graph opera en capa de señales, no precisa link |
| **Toca** | Context Pack |
| **Acción** | NO intentarlo ahora - operar como ranking hints para ctx search |

### Bloqueo 3: AST Solo Extrae Top-Level Symbols

| Aspecto | Detalle |
|----------|---------|
| **Evidencia** | `SkeletonMapBuilder` solo parsea `tree.body` (línea 130 ast_parser.py) |
| **Severidad** | 🟡 MEDIO |
| **Bloquea MVP** | PARCIAL - usable para nodos, limitante para relaciones profundas |
| **Toca** | AST Parser |
| **Acción** | Aceptar limitación, grafo inicial con solo top-level |

### Bloqueo 4: LSP Estado "RELAXED READY"

| Aspecto | Detalle |
|----------|---------|
| **Evidencia** | agent_trifecta_dope.md línea 190: "RELAXED READY", fallback obligatorio |
| **Severidad** | 🟢 BAJO |
| **Bloquea MVP** | NO - LSP es enrichment opcional, no requerido |
| **Toca** | LSP Daemon |
| **Acción** | NO poner en centro del MVP, usar solo si disponible |

### Bloqueo 5: Falta Schema de Graph Store

| Aspecto | Detalle |
|----------|---------|
| **Evidencia** | No existe SQLite table para nodes/edges de grafo |
| **Severidad** | 🔴 CRÍTICO |
| **Bloquea MVP** | SÍ - sin persistencia no hay grafo |
| **Toca** | Storage |
| **Acción** | Implementar schema mínimo: nodes + edges + segment_id |

---

## B. Qué Quedó Validado

### Por Evidencia del Repo

| Afirmación | Estado |
|------------|--------|
| CLI usa Typer | ✅ Confirmado |
| AST es usable como base | ✅ Confirmado - parser estable con cache |
| Segment resolver existe | ✅ Confirmado - V1 operativa |
| Context Pack tiene chunks | ✅ Confirmado - whole_file chunks |
| Fallback LSP→AST existe | ✅ Confirmado - código en lsp_client.py |

### Por Auditorías Anteriores

| Hallazgo | Estado |
|----------|--------|
| SegmentRef V1 = SSOT real | ✅ Validado - 16 call sites |
| SegmentRef V2 = no adoptada | ✅ Validado - 1 call site |
| AST M1 = usable con limitaciones | ✅ Validado - top-level only |
| LSP = RELAXED READY | ✅ Validado - fallback obligatorio |
| Graph↔PCC link = no existe | ✅ Validado - no hay contrato |

---

## C. Qué Quedó Obsoleto

### Afirmaciones que la Evidencia Invalida

| Afirmación Previa | Por Qué |
|-------------------|---------|
| "AST/LSP son prototipos/debug scripts" | ❌ INVALIDADO - 51 tests activos, CLI operativo |
| "No hay cache para AST" | ❌ INVALIDADO - SQLite + LRU implementados |
| "No hay fallback LSP" | ❌ INVALIDADO - fallback integrado y telemetrizado |
| "LSP es Production Ready" | ❌ INVALIDADO - es RELAXED READY |
| "chunk_ids son estables" | ❌ INVALIDADO - son sha1(content) efímeros |
| "context pack tiene symbol mapping" | ❌ INVALIDADO - son whole_file chunks |

### Documentos a Archivar/Revisar

| Documento | Acción |
|-----------|--------|
| `docs/lsp/*.md` | Archivar - narrativas de frustración obsoletas |
| `docs/ast-lsp-connect/*.md` | Archivar - análisis antiguos |
| `docs/cli/AST_LSP_DAEMON_USAGE_REPORT.md` | Archivar - docs de debug |

---

## D. Orden de Trabajo Recomendado

### Fase 1: foundation (SEMANA 1) 🔴

| Orden | Tarea | Por Qué | Bloqueo |
|-------|-------|----------|---------|
| 1.1 | Confirmar SSOT SegmentRef (V1) | Identidad base | #1 |
| 1.2 | Definir schema SQLite graph (nodes, edges) | Persistencia mínima | #5 |
| 1.3 | Crear `cli_graph.py` con patrón Typer | CLI entrypoint | #5 |

### Fase 2: core (SEMANA 2) 🟡

| Orden | Tarea | Por Qué | Bloqueo |
|-------|-------|----------|---------|
| 2.1 | Consumir AST symbols como nodos | Base del grafo | #3 |
| 2.2 | Implementar relaciones (callers/callees) top-level | Feature core | #3 |
| 2.3 | Persistir en SQLite graph store | Storage | #5 |

### Fase 3: integration (SEMANA 3) 🟢

| Orden | Tarea | Por Qué | Bloqueo |
|-------|-------|----------|---------|
| 3.1 | Integrar con ctx search (ranking hints) | PCC boundary | #2 |
| 3.2 | Agregar LSP como enrichment opcional | Feature extra | #4 |
| 3.3 | CLI commands: index, status, search | Interfaz usuario | - |

### Lo que NO Tocar

| Tema | Razón |
|------|-------|
| MCP | Protocolo de exposición, no núcleo |
| Neo4j/Kuzu | Store externo, no en scope MVP |
| Symbol↔Chunk linking | No existe contrato, no intentar |
| Multi-lenguaje | Solo Python en MVP |
| Visualizadores complejos | UI no es scope |

---

## E. Criterio de Entrada a Implementación MVP

### Requirements Mínimos para Iniciar

| Requisito | Verificación |
|-----------|-------------|
| ✅ SSOT SegmentRef confirmado | `src/domain/segment_resolver.py` usado |
| ✅ Schema SQLite definido | nodes + edges tables |
| ✅ CLI graph namespace creado | `trifecta graph --help` funciona |
| ✅ AST consumption operativo | Symbols extraídos del parser |
| ✅ Storage implementación | SQLite escribir/leer |

### Requirements Óptimos (pueden esperar)

| Requisito | Puede Esperar |
|-----------|--------------|
| Relaciones profundas | Top-level suficiente para v1 |
| LSP enrichment | Solo si disponible |
| Multi-segment sync | Un segmento a la vez |
| Visualización | CLI es suficiente |

### Definition of Done - MVP

```
✓ Graph CLI: trifecta graph index / status / search / callers / callees
✓ Storage: SQLite con nodes + edges por segment_id
✓ AST integration: Symbols como nodos top-level
✓ PCC integration: Ranking hints para ctx search
✓ Tests: Unit + Integration covering core operations
✓ Telemetry: Events para graph operations
```

---

## F. Resumen Ejecutivo

### 5 Bloqueos vsMVP

| # | Bloqueo | Severidad | Acción |
|---|---------|-----------|--------|
| 1 | SSOT SegmentRef doble | 🔴 CRÍTICO | Confirmar V1, migrar V2 |
| 2 | No hay symbol↔chunk link | 🟡 MEDIO | NO intentar - operar como señales |
| 3 | AST solo top-level | 🟡 MEDIO | Aceptar limitación |
| 4 | LSP RELAXED READY | 🟢 BAJO | Enriquecimiento opcional |
| 5 | Falta graph store | 🔴 CRÍTICO | Implementar schema SQLite |

### Lo que Quedó Obsoleto

- Docs que dicen "prototipo/debug" → Archivar
- Afirmaciones de "Production Ready" para LSP → Corregir a "RELAXED READY"
- Expectativas de symbol↔chunk linking → Eliminar

### Entrada aMVP

**Iniciar cuando**: Schema SQLite definido + CLI namespace creado + SegmentRef confirmado
**MVP entrega**: Graph indexing + search + callers/callees top-level + SQLite storage
