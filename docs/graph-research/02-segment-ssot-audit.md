# Auditoría de SegmentRef/Segment SSOT

Fecha: 2026-03-13
Objetivo: Determinar la única fuente de verdad para segment identity

---

## A. Resumen Ejecutivo

| Hallazgo | Evidencia |
|----------|-----------|
| **SSOT real actual** | `src/domain/segment_resolver.py` con 16 call sites activos |
| **SSOT paralelo sin uso** | `src/trifecta/domain/segment_ref.py` con 1 call site (`src/trifecta/domain/repo_ref.py`) |
| **Wrapper deprecated activo** | `src/infrastructure/segment_utils.py` con 1 call site (`src/application/search_get_usecases.py:182`) |
| **Inconsistencia crítica** | V1 usa `root_abs`, V2 usa `segment_root`; V2 incluye paths derivados, V1 no |

**VEREDICTO**: `src/domain/segment_resolver.py` es el SSOT real. La implementación en `src/trifecta/domain/segment_ref.py` nunca fue adoptada y debe descartarse. `segment_utils.py` debe migrarse.

---

## B. Comparativa de Implementaciones

### 1. src/domain/segment_resolver.py (V1 - ACTIVA)

**Clase expuesta**: `SegmentRef` (custom class con `__slots__`)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `root_abs` | Path | Absolute canonical path to segment root |
| `slug` | str | Human-readable normalized name |
| `fingerprint` | str | Hash-based unique identifier (8 chars) |
| `id` | str | Combined (slug_fingerprint) |

**Funciones públicas**:

- `resolve_segment_ref(segment_input, hash_length) -> SegmentRef`
- `get_segment_root(segment_input) -> Path`
- `get_segment_slug(segment_input) -> str`
- `get_segment_fingerprint(segment_input) -> str`
- `get_segment_id(segment_input) -> str`
- `_canonicalize_path(path) -> Path` (private)
- `_compute_fingerprint(root_abs, hash_length) -> str` (private)

**Invariantes**:

- Solo resolved segment root, NO repository root
- NO paths derivados (runtime, telemetry, config, cache)
- Hash computado del path absoluto canonical

---

### 2. src/trifecta/domain/segment_ref.py (V2 - NO ADOPTADA)

**Clase expuesta**: `@dataclass(frozen=True) SegmentRef`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `repo_root` | Path | Repository root (busca .git o pyproject.toml) |
| `repo_id` | str | Hash del repo_root |
| `segment_root` | Path | Segment root (equivalente a root_abs de V1) |
| `segment_id` | str | Combined (name_hash) |
| `runtime_dir` | Path | Platform data dir |
| `registry_key` | str | Same as segment_id |
| `telemetry_dir` | Path | platform/telemetry/{segment_id} |
| `config_dir` | Path | platform/config |
| `cache_dir` | Path | platform/cache/{segment_id} |

**Funciones públicas**:

- `resolve_segment_ref(segment_input, hash_length) -> SegmentRef`
- `_get_platform_data_dir() -> Path` (private)
- `_canonicalize_path(path) -> Path` (private)
- `_compute_hash(path, length) -> str` (private)
- `_normalize_segment_id(name) -> str` (private)
- `_find_repo_root(start) -> Path` (private)

**Invariantes**:

- SÍ incluye repository root (derivado)
- SÍ incluye paths derivados (runtime, telemetry, config, cache)
- Platform-aware (darwin/win32/linux)
- Tiene `_find_repo_root()` para caminar directorios

**Fecha**: 2026-03-06 (más reciente que V1: 2026-02-15)

---

### 3. src/infrastructure/segment_utils.py (DEPRECATED - ACTIVA)

**Funciones**:

- `resolve_segment_root(start_path) -> Path` → deprecated wrapper
- `compute_segment_id(segment_root) -> str` → deprecated wrapper

**Nota**: Ambas funciones EMITEN DeprecationWarning pero siguen activas.

---

### 4. src/infrastructure/segment_state.py (COMPLEMENTARIA)

**Clase expuesta**: `@dataclass(frozen=True) SegmentState`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `segment_input` | str | Raw input |
| `segment_input_normalized` | str | Resolved path |
| `segment_root_resolved` | Path | Canonical path |
| `segment_id` | str | Slug from V1 |
| `source_of_truth` | str | "config" o "dirname" |
| `config_path_used` | Path | _ctx/trifecta_config.json si existe |
| `expected_files` | tuple | Expected agent/prime/session files |

**Import**: USA `resolve_segment_ref` de V1 (línea 9 y 56)

---

## C. Call Sites Reales

### V1 (src/domain/segment_resolver.py) - 16 call sites

| Archivo | Línea | Función importada |
|---------|-------|------------------|
| `src/infrastructure/segment_state.py` | 9 | `resolve_segment_ref` |
| `src/infrastructure/telemetry.py` | 10 | `resolve_segment_ref, get_segment_fingerprint` |
| `src/infrastructure/lsp_daemon.py` | 13 | `resolve_segment_ref, get_segment_fingerprint` |
| `src/infrastructure/cli.py` | 1790 | `get_segment_slug` |
| `src/infrastructure/cli.py` | 2481,2504,2550,2571,2589,2612 | `resolve_segment_ref` (6 veces) |
| `src/application/doctor_use_case.py` | 6 | `SegmentRef, resolve_segment_ref` |
| `src/application/status_use_case.py` | 6 | `SegmentRef, resolve_segment_ref` |
| `src/application/use_cases.py` | 291 | `get_segment_slug` |
| `src/application/hookify_extractor.py` | 153 | `get_segment_fingerprint` |
| `src/application/repo_use_case.py` | 9 | `resolve_segment_ref` |
| `src/domain/models.py` | 27 | `get_segment_slug` |

### V2 (src/trifecta/domain/segment_ref.py) - 1 call site

| Archivo | Línea | Función importada |
|---------|-------|------------------|
| `src/trifecta/domain/repo_ref.py` | 11 | `resolve_segment_ref` |

### segment_utils.py (DEPRECATED) - 1 call site

| Archivo | Línea | Función importada |
|---------|-------|------------------|
| `src/application/search_get_usecases.py` | 182 | `resolve_segment_root` |

---

## D. Drift Concreto Detectado

### Diferencias de Naming

| Concepto | V1 (`segment_resolver.py`) | V2 (`segment_ref.py`) |
|----------|---------------------------|----------------------|
| Segment root path | `root_abs` | `segment_root` |
| Hash identifier | `fingerprint` | No existe (solo en segmento) |
| Combined ID | `id` | `segment_id` |
| Repo root | ❌ No tiene | `repo_root` |
| Repo ID | ❌ No tiene | `repo_id` |
| Runtime dir | ❌ No tiene | `runtime_dir` |
| Telemetry dir | ❌ No tiene | `telemetry_dir` |
| Config dir | ❌ No tiene | `config_dir` |
| Cache dir | ❌ No tiene | `cache_dir` |

### Diferencias de Responsabilidad

| Aspecto | V1 | V2 |
|---------|----|----|
| Resolve segment solo | ✅ | ✅ |
| Resolve repo root | ❌ | ✅ |
| Platform paths | ❌ | ✅ |
| Walk directory tree | ❌ | ✅ (via _find_repo_root) |

### Diferencias de Implementación

| Aspecto | V1 | V2 |
|---------|----|----|
| Tipo | Custom class (`__slots__`) | `@dataclass(frozen=True)` |
| Fecha | 2026-02-15 | 2026-03-06 |
| Dependencias externas | Solo `src.domain.naming` | Platform-aware (sys.platform) |
| Tests existentes | ✅ Múltiples | ❌ No encontrados |

---

## E. Veredicto de SSOT

### SSOT ELEGIDO: `src/domain/segment_resolver.py`

**Justificación**:

1. **16 call sites activos** vs 1 call site en V2
2. **Producción validada**: Usada en telemetry, LSP daemon, CLI, use cases
3. **Contrato estable**: Mismos campos desde 2026-02-15
4. **V2 nunca fue adoptada**: Solo usada en `repo_ref.py` (posiblemente código nuevo no integrado)

### Alternativa Descartada: `src/trifecta/domain/segment_ref.py`

**Razón**: Código más completo pero sin adopción. Es un "design document"implícito más que SSOT operativo.

---

## F. Lista de Migración Mínima

### 1. Migrar `src/application/search_get_usecases.py:182`

```python
# Antes (deprecated):
from src.infrastructure.segment_utils import resolve_segment_root

# Después:
from src.domain.segment_resolver import get_segment_root
```

### 2. Migrar `src/trifecta/domain/repo_ref.py`

```python
# Antes (V2 no adoptada):
from src.trifecta.domain.segment_ref import resolve_segment_ref

# Después (V1):
from src.domain.segment_resolver import resolve_segment_ref
```

### 3. Eliminar o dejar de importar `segment_utils.py`

Opcional: Los warnings de deprecated están emitidos, pero el call site en search_get_usecases.py debe migrarse.

---

## G. Riesgo de No Corregir Esto Antes de Graph

| Riesgo | Impacto | Probabilidad |
|--------|---------|--------------|
| **Graph usa V2** por error | Inconsistencia con resto del sistema (16 módulos) | Media |
| **Graph implementa sus propios paths** | Duplicación de lógica de resolución | Alta |
| **call sites mixtos** | Comportamiento no determinista | Baja |
| **DRIFT de telemetry** | Métricas de Graph no correlacionables | Media |

### Acciones Requeridas Antes de Graph

1. ✅ **Confirmar SSOT**: V1 (segment_resolver.py) es el activo
2. 🔲 **Migrar search_get_usecases.py**: 1 call site deprecated
3. 🔲 **Migrar repo_ref.py**: Migrar a V1 o eliminar si no usado
4. 🔲 **Decidir destino de V2**: ¿Eliminar o mantener como "reference design"?
5. 🔲 **Documentar en ADR**: Incluir veredicto de SSOT en documentación

---

## H. Recomendación

**Para Graph**:

- Usar EXCLUSIVAMENTE `src.domain.segment_resolver` como SSOT
- NO usar `src.trifecta.domain.segment_ref` aunque parezca más completa
- Si se necesitan paths derivados (runtime, telemetry, cache), derivarlos EN Graph desde `root_abs` de V1, NO importar de V2
- Consultar `src/platform/contracts.py` para paths de runtime (ya tiene lógica para ~/.local/share/trifecta/)

**Veredicto final**: El SSOT es `src/domain/segment_resolver.py`. V2 debe descartarse para Graph.
