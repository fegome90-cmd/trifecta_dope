# Auditoría Trifecta - Índice de Contenidos

 Auditoría completa del sistema Trifecta Progressive Disclosure con evidencia reproducible.

## 📋 Índice Rápido por Tema

| Tema | Archivo | Sección |
|------|---------|---------|
| **Dictamen del sistema** | [AUDIT_PHASE2_DICTAMEN_PLAN.md](#audit_phase2_dictamen_planmd) | [Dictamen](#c-dictamen) |
| **Path PII (crítico)** | [AUDIT_PHASE2_DICTAMEN_PLAN.md](#audit_phase2_dictamen_planmd) | [Bloqueador #1](#bloqueador-1-path-hygiene-crítico) |
| **Pytest ImportError** | [AUDIT_PHASE2_DICTAMEN_PLAN.md](#audit_phase2_dictamen_planmd) | [Bloqueador #2](#bloqueador-2-pytest-importerror-alto) |
| **ast symbols roto** | [AUDIT_PHASE2_DICTAMEN_PLAN.md](#audit_phase2_dictamen_planmd) | [Bloqueador #3](#bloqueador-3-ast-symbols-file_not_found-medio) |
| **Capas PD L0/L1/L2** | [TECHNICAL_REPORT_PROGRESSIVE_DISCLOSURE.md](#technical_report_progressive_disclosuremd) | [Capas Implementadas](#2-aráctica-general) |
| **L0 Skeleton** | [SCOPE_PD_L0_REPORT.md](#scope_pd_l0_reportmd) | [L0 Skeleton Definición](#c-l0-skeleton-definición-real) |
| **SSOT e invariantes** | [AUDIT_SCOPE_PHASE1_REPORT.md](#audit_scope_phase1_reportmd) | [Invariantes](#b-invariantes-identificadas) |
| **Evidencia reproducible** | [AUDIT_SCOPE_PHASE1_REPORT.md](#audit_scope_phase1_reportmd) | [Outputs Crudos](#d-evidencia-reproducible-obligatoria) |

---

## 📁 Archivos por Orden de Lectura

### 1. [AUDIT_PHASE2_DICTAMEN_PLAN.md](AUDIT_PHASE2_DICTAMEN_PLAN.md)
**Fecha**: 2026-01-02 | **Tamaño**: 7.6K | **Estado**: DICTAMEN FINAL

#### Contenido Clave:
- **Líneas 7-30**: [Tabla de Hallazgos](#a-hallazgos-evidencia-verificada) - 8 problemas con evidencia archivo:línea
  - PATH HYGIENE VIOLATION (línea 11) - `/Users/...` en context_pack.json
  - pytest ImportError (línea 12) - 3 tests rotos
  - SymbolInfo no existe (línea 13) - Bloquea tests PR2

- **Líneas 49-55**: [Dictamen](#c-dictamen)
  ```
  AUDITABLE-PARTIAL-PASS
  - Sistema core funciona (PD L0, telemetría)
  - 3 BLOCKERS críticos
  - NO hay rotación de datos
  ```

- **Líneas 62-119**: [Plan Mínimo - 3 Bloqueadores](#d-plan-mínimo-patches-must-fix)
  - **Bloqueador #1** (líneas 64-88): Sanitizar rutas absolutas
    - Archivos: `use_cases.py`, `test_path_hygiene.py`
    - DoD: No `/Users/` en pack
    - Test: `grep -E '"/Users/|"/home/' _ctx/context_pack.json`

  - **Bloqueador #2** (líneas 90-107): pytest ImportError
    - Archivos: `stubs.py`, tests
    - DoD: pytest corre sin errors
    - Test: `uv run pytest -q`

  - **Bloqueador #3** (líneas 109-119): ast symbols FILE_NOT_FOUND
    - Archivos: `symbol_selector.py`, `cli_ast.py`
    - DoD: `trifecta ast symbols` funciona
    - Test: `uv run trifecta ast symbols sym://python/mod/context_service`

- **Líneas 123-150**: [Evidencia Requerida](#e-evidencia-requerida-outputs-crudos)
  - Outputs crudos que el usuario debe pegar para cerrar PASS

- **Líneas 155-165**: [3 Preguntas Bloqueantes](#f-preguntas-máx-3)

---

### 2. [AUDIT_SCOPE_PHASE1_REPORT.md](AUDIT_SCOPE_PHASE1_REPORT.md)
**Fecha**: 2026-01-02 | **Tamaño**: 23K | **Fase**: SCOPE (evidencia recolectada)

#### Contenido Clave:
- **Líneas 7-18**: [Scope Map](#a-scope-map) - Features y rutas
  - ctx sync/search/get → `context_service.py`, `cli.py`
  - PD L0 Skeleton → `context_service.py:265-301`
  - PD L1 AST/LSP → `cli_ast.py`, `lsp_daemon.py`

- **Líneas 20-35**: [10 Invariantes](#b-invariantes-identificadas)
  - segment_root SSOT: `segment_utils.py:6-28`
  - segment_id = 8 chars SHA256: `segment_utils.py:31-37`
  - Schema version = 1: `context_models.py:42`
  - timing_ms >= 1: `telemetry.py:66`
  - stop_reason enum: `context_service.py:139-213`

- **Líneas 37-56**: [SSOT / Duplicaciones](#c-ssot--duplicaciones)
  - ⚠️ CORRECCIÓN: ContextPack NO está duplicado (error de reporte original)

- **Líneas 58-260**: [Evidencia Reproducible](#d-evidencia-reproducible)
  - Git SHA, status, pytest errors
  - PD L0: ctx sync/search/get (modes skeleton/excerpt/raw)
  - PD L1: ast hover/symbols outputs
  - Telemetría: 260 líneas de events.jsonl

---

### 3. [TECHNICAL_REPORT_PROGRESSIVE_DISCLOSURE.md](TECHNICAL_REPORT_PROGRESSIVE_DISCLOSURE.md)
**Fecha**: 2026-01-02 | **Tamaño**: 16K | **Focus**: Arquitectura PD

#### Contenido Clave:
- **Líneas 7-26**: [Arquitectura General](#1-aráctica-general)
  - Diagrama de componentes CLI → ContextService → LSP Daemon
  - Flujo de datos PD L0/L1

- **Líneas 28-72**: [Capa L0: Skeleton Mode](#2-capa-l0-skeleton-mode)
  - Definición: `context_service.py:265-301`
  - Ejemplo entrada/salida skeletonización
  - Tabla de modos: raw/excerpt/skeleton

- **Líneas 74-115**: [Capa L1: AST y LSP](#3-capa-l1-ast-y-lsp)
  - LSP Daemon: socket IPC, 180s TTL
  - AST Parser: stub implementation
  - Comandos CLI: `ast symbols`, `ast hover`

- **Líneas 117-122**: [Capa L2: Estado Actual](#4-capa-l2-estado-actual)
  - ❌ NO EXISTE como capa arquitectónica
  - `mode="raw"` con budget alto = L2 "de facto"

- **Líneas 134-148**: [Gaps Identificados](#6-gaps-y-recomendaciones)
  - Score-based Auto PD (ALTA)
  - LSP Real Output (MEDIA)
  - Search keyword recall (MEDIA)

---

### 4. [SCOPE_PD_L0_REPORT.md](SCOPE_PD_L0_REPORT.md)
**Fecha**: 2026-01-02 | **Tamaño**: 6.2K | **Focus**: L0 Skeleton Analysis

#### Contenido Clave:
- **Líneas 4-10**: Inventario de componentes
- **Líneas 18-29**: ¿Dónde se decide "leer poco vs leer más"?
  - `context_service.py:86` - `mode` parameter
- **Líneas 31-37**: Noción de niveles L0/L1/L2
- **Líneas 63-72**: L0 Skeleton: Definición real
  - Campos incluidos (headers, code blocks, signatures)
- **Líneas 130-137**: Gaps concretos (tabla tamaño S/L/M)

---

### 5. [SCOPE_READING_BEHAVIOR_REPORT.md](SCOPE_READING_BEHAVIOR_REPORT.md)
**Fecha**: 2026-01-02 | **Tamaño**: 4.1K | **Focus**: Comportamiento lectura chunks

#### Contenido Clave:
- Análisis de cómo el sistema lee y retorna chunks
- Comportamiento de `ctx get` con diferentes modos

---

## 🎯 Por Qué Leer Cada Archivo

| Si quieres... | Lee esto | Sección |
|---------------|---------|---------|
| **Entender el estado actual** | AUDIT_PHASE2_DICTAMEN_PLAN.md | [Dictamen](#c-dictamen) |
| **Ver qué hay que arreglar** | AUDIT_PHASE2_DICTAMEN_PLAN.md | [Hallazgos tabla](#a-hallazgos-evidencia-verificada) |
| **Saber qué patches hacer** | AUDIT_PHASE2_DICTAMEN_PLAN.md | [Plan Mínimo](#d-plan-mínimo-patches-must-fix) |
| **Ver evidencia cruda** | AUDIT_SCOPE_PHASE1_REPORT.md | [Evidencia Reproducible](#d-evidencia-reproducible) |
| **Entender PD L0/L1/L2** | TECHNICAL_REPORT_PROGRESSIVE_DISCLOSURE.md | [Capas](#2-capa-l0-skeleton-mode) |
| **Verificar invariantes** | AUDIT_SCOPE_PHASE1_REPORT.md | [Invariantes](#b-invariantes-identificadas) |
| **Profundizar en L0** | SCOPE_PD_L0_REPORT.md | Completo |

---

## 📊 Resumen de Dictamen

```
AUDIT_SCOPE_PHASE1      → Evidencia recolectada (SCOPE)
AUDIT_PHASE2_DICTAMEN   → Dictamen + Plan Mínimo (ACTIONABLE)
TECHNICAL_REPORT_PD     → Arquitectura de capas (EDUCATIONAL)
```

**Resultado Final**: `AUDITABLE-PARTIAL-PASS`
- Sistema core funciona (PD L0, telemetría, daemon lifecycle)
- 3 BLOCKERS críticos identificados con patches específicos
- Evidencia reproducible para cada claim

---

## 🔍 Búsqueda Rápida en los Archivos

```bash
# Buscar PATH PII
grep -n "repo_root.*Users\|/Users/felipe" docs/auditoria/AUDIT_PHASE2_DICTAMEN_PLAN.md

# Buscar ImportError
grep -n "ImportError\|SymbolInfo" docs/auditoria/AUDIT_PHASE2_DICTAMEN_PLAN.md

# Buscar SSOT
grep -n "SSOT\|segment_utils.py:6\|segment_utils.py:31" docs/auditoria/AUDIT_SCOPE_PHASE1_REPORT.md

# Buscar L0 skeleton
grep -n "skeleton\|_skeletonize" docs/auditoria/TECHNICAL_REPORT_PROGRESSIVE_DISCLOSURE.md
```
