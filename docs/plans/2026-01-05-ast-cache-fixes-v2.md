# Plan: Correcciones del Sistema de Cache de AST (v2)

**Fecha**: 2026-01-05  
**Prioridad**: ALTA  
**Estado**: Planificación  
**Versión**: 2.0 (incorporando Clean Architecture y mejores prácticas)

---

## Resumen Ejecutivo

Este plan aborda los **5 problemas críticos** identificados en el análisis profundo del sistema de cache de AST:

1. **Cache no compartido entre componentes** 🔴
2. **Telemetría de cache rota** 🔴
3. **Instancias efímeras en CLI** 🔴
4. **Falta de evicción LRU** 🔴 (nuevo)
5. **Uso de pickle para persistencia** 🔴 (nuevo)

**Impacto Esperado**:
- Métricas de cache correctas y confiables
- Reducción de parseos redundantes
- Mejora de rendimiento del sistema AST
- Arquitectura limpia con dependencias explícitas
- Cache observable, determinista, versionable y sin estado mágico

**Principios de Diseño**:
- ✅ Clean Architecture: Dependencias explícitas (DI), no estado oculto
- ✅ Abstracción de cache: Protocolo `AstCache` con implementaciones intercambiables
- ✅ Evicción LRU: Límites de tamaño para evitar bombas de RAM
- ✅ Telemetría segura: Solo metadatos, sin contenido crudo
- ✅ Persistencia robusta: SQLite segmentado por repo, no pickle
- ✅ Versionable: Claves de cache incluyen versión del formato

---

## Cambios Principales vs Plan v1

### 1. Abstracción de Cache (Clean Architecture) 🆕

**Cambio**: En lugar de usar `_global_cache` como variable global, definir un protocolo `AstCache` y pasar el cache como dependencia.

**Beneficios**:
- No hay estado oculto
- Tests más fáciles (se puede inyectar `NullCache`)
- Implementaciones intercambiables (`InMemoryLRUCache`, `SQLiteCache`, `NullCache`)
- Comportamiento = función + dependencia explícita

**Protocolo AstCache**:
```python
class AstCache(Protocol):
    def get(self, key: str) -> Optional[Any]: ...
    def set(self, key: str, value: Any) -> None: ...
    def delete(self, key: str) -> bool: ...
    def clear(self) -> None: ...
    def stats(self) -> CacheStats: ...
```

### 2. Evicción LRU 🆕

**Cambio**: Implementar límites de tamaño (`max_entries`, `max_bytes`) con evicción LRU.

**Beneficios**:
- Cache no crece sin límite
- No hay bombas de RAM en CI o daemons
- Uso de memoria acotado

**Implementación**:
```python
class InMemoryLRUCache:
    def __init__(self, max_entries: int = 10000, max_bytes: int = 100 * 1024 * 1024):
        self.max_entries = max_entries
        self.max_bytes = max_bytes
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        # ...
```

### 3. Telemetría Segura 🆕

**Cambio**: No incluir `content` crudo en la telemetría, solo metadatos.

**Beneficios**:
- No infla los eventos
- No genera ruido
- No hay riesgo de datos sensibles

**Metadatos seguros**:
```python
{
    "file": str(file_path),
    "cache_key": cache_key,
    "cache_status": cache_status,  # "hit" | "miss" | "error"
    "symbols_count": len(symbols),
    "skeleton_bytes": skeleton_bytes,
}
```

### 4. Persistencia SQLite 🆕

**Cambio**: Usar SQLite en lugar de pickle para persistencia.

**Beneficios**:
- Más robusto que pickle
- No ejecuta código arbitrario
- Legible por humanos (JSON)
- Fácil de migrar entre versiones
- Segmentado por repo

**Implementación**:
```python
class SQLiteCache:
    def __init__(self, db_path: Path, max_entries: int = 10000, max_bytes: int = 100 * 1024 * 1024):
        self.db_path = db_path
        # ...
```

### 5. Claves de Cache Versionables 🆕

**Cambio**: Usar formato de clave: `{segment_id}:{file_rel}:{content_sha256_16}:{cache_version}`

**Beneficios**:
- Fácil de migrar entre versiones
- Cache se invalida automáticamente cuando cambia el formato
- Más robusto que usar solo 8 caracteres del hash

**Implementación**:
```python
def _make_cache_key(self, file_rel: str, content: str) -> str:
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]  # 16 chars
    return f"{self.segment_id}:{file_rel}:{content_hash}:{self.CACHE_VERSION}"
```

---

## Problemas Identificados

### Problema 1: Cache No Compartido Entre Componentes 🔴

**Descripción**: Cada componente crea su propia instancia de `SkeletonMapBuilder`, lo que significa que el cache NO se comparte entre componentes.

**Evidencia**:
- [`PR2ContextSearcher`](src/application/pr2_context_searcher.py:56): `self.ast_builder = SkeletonMapBuilder()`
- [`ASTTelemetry`](src/application/telemetry_pr2.py:30): `self.ast_counter = SkeletonMapBuilder()`
- [`CLI AST`](src/infrastructure/cli_ast.py:64): `builder = SkeletonMapBuilder()`

**Impacto**: El mismo archivo se parsea múltiples veces, una por cada componente.

**Raíz del problema**: Estado oculto en cada instancia, sin dependencia explícita de cache.

---

### Problema 2: Telemetría de Cache Rota 🔴

**Descripción**: El método `track_parse()` de `ASTTelemetry` siempre recibe `cache_hit=False`, independientemente del resultado real.

**Evidencia**:
- [`pr2_context_searcher.py:184`](src/application/pr2_context_searcher.py:184): `self.ast_tel.track_parse(..., cache_hit=False)` SIEMPRE pasa `False`
- [`SkeletonMapBuilder.build()`](src/application/ast_parser.py:28): NO retorna información sobre si fue cache hit o miss

**Impacto**: 
- La telemetría SIEMPRE reporta `cache_hit=False`
- Los contadores `ast_cache_hit_count` y `ast_cache_miss_count` son incorrectos
- La tasa de cache hits reportada (42.5%) es **falsa**

**Problema adicional**: La telemetría incluye `content` crudo, lo cual:
- Infla los eventos
- Genera ruido
- Aumenta riesgo de datos sensibles

---

### Problema 3: Instancias Efímeras en CLI 🔴

**Descripción**: El comando `ast symbols` crea una nueva instancia de `SkeletonMapBuilder` cada vez que se ejecuta.

**Evidencia**:
- [`cli_ast.py:64`](src/infrastructure/cli_ast.py:64): `builder = SkeletonMapBuilder()` crea NUEVA instancia cada vez

**Impacto**: El cache está vacío en cada ejecución, haciendo el cache inútil.

**Raíz del problema**: Sin persistencia entre ejecuciones y sin inyección de dependencias.

---

### Problema 4: Falta de Evicción LRU 🔴 (Nuevo)

**Descripción**: El cache crece sin límite cuando se escanean repos completos, lo cual es una bomba de RAM en CI o daemons.

**Impacto**: 
- Uso de memoria ilimitado
- Posibles OOM (Out of Memory) en escenarios de producción
- Degradación de rendimiento con el tiempo

---

### Problema 5: Uso de Pickle para Persistencia 🔴 (Nuevo)

**Descripción**: El plan original usaba pickle para persistencia, lo cual es peligroso y no versionable.

**Impacto**:
- Seguridad: pickle puede ejecutar código arbitrario
- Versioning: Difícil de migrar entre versiones
- Debugging: No es legible por humanos

---

## Orden de Implementación (Revisado)

### Fase 0: Prueba que Reproduce el Bug Real 🆕

**Objetivo**: Crear pruebas que demuestren los problemas antes de cambiar código.

**Archivos a Crear**:
- [`tests/unit/test_ast_cache_bugs.py`](tests/unit/test_ast_cache_bugs.py:1) (nuevo)

**Pruebas**:
1. `test_cache_hit_always_false_before_fix()`: Demuestra que hoy `cache_hit` siempre es false
2. `test_different_builders_dont_share_cache_before_fix()`: Demuestra que distintos builders NO comparten cache

**Resultado Esperado**: Estas pruebas fallarán antes de implementar las soluciones, y pasarán después.

---

### Fase 1: Abstracción de Cache (Clean Architecture) 🆕

**Objetivo**: Crear el protocolo `AstCache` y sus implementaciones.

**Archivos a Crear**:
- [`src/domain/ast_cache.py`](src/domain/ast_cache.py:1) (nuevo)

**Implementaciones**:
1. `InMemoryLRUCache`: Cache en memoria con evicción LRU
2. `SQLiteCache`: Cache persistente en SQLite segmentado por repo
3. `NullCache`: Cache nulo (no-op) para tests y benchmarks

**Duración**: 3-4 horas

---

### Fase 2: Modificar SkeletonMapBuilder para Usar AstCache

**Objetivo**: Modificar `SkeletonMapBuilder` para aceptar un `AstCache` como dependencia.

**Archivos a Modificar**:
- [`src/application/ast_parser.py`](src/application/ast_parser.py:1)

**Cambios**:
1. Modificar constructor para aceptar `cache: Optional[AstCache]`
2. Agregar método `_make_cache_key()` con formato: `{segment_id}:{file_rel}:{content_sha256_16}:{cache_version}`
3. Modificar `build()` para retornar `ParseResult` en lugar de `List[SymbolInfo]`
4. Usar `cache.get()` y `cache.set()` en lugar de `self._cache`

**Duración**: 2-3 horas

---

### Fase 3: Corregir Telemetría de Cache

**Objetivo**: Modificar `track_parse()` para no incluir `content` crudo y usar `CacheStatus`.

**Archivos a Modificar**:
- [`src/application/telemetry_pr2.py`](src/application/telemetry_pr2.py:1)
- [`src/application/pr2_context_searcher.py`](src/application/pr2_context_searcher.py:1)

**Cambios**:
1. Modificar `ASTTelemetry.track_parse()` para aceptar `ParseResult` en lugar de `content`
2. Remover `content` de la telemetría
3. Agregar metadatos seguros: `cache_key`, `cache_status`, `symbols_count`, `skeleton_bytes`
4. Actualizar `PR2ContextSearcher._extract_skeleton()` para usar `ParseResult`

**Duración**: 2-3 horas

---

### Fase 4: Inyectar Cache en Componentes (Dependency Injection)

**Objetivo**: Inyectar `AstCache` en todos los componentes para compartir el cache.

**Archivos a Modificar**:
- [`src/application/pr2_context_searcher.py`](src/application/pr2_context_searcher.py:1)
- [`src/infrastructure/cli_ast.py`](src/infrastructure/cli_ast.py:1)

**Cambios**:
1. Modificar `PR2ContextSearcher` para aceptar `cache: Optional[AstCache]`
2. Crear función `_get_cache()` en `cli_ast.py`
3. Modificar `ast symbols` para usar `_get_cache()`
4. Agregar comando `ast clear-cache`
5. Agregar comando `ast cache-stats`

**Duración**: 3-4 horas

---

## Timeline Estimado

| Fase | Duración | Estado |
|------|----------|--------|
| Fase 0: Prueba que Reproduce el Bug Real | 1-2 horas | Pendiente |
| Fase 1: Abstracción de Cache (Clean Architecture) | 3-4 horas | Pendiente |
| Fase 2: Modificar SkeletonMapBuilder para Usar AstCache | 2-3 horas | Pendiente |
| Fase 3: Corregir Telemetría de Cache | 2-3 horas | Pendiente |
| Fase 4: Inyectar Cache en Componentes (DI) | 3-4 horas | Pendiente |
| Pruebas Unitarias | 3-4 horas | Pendiente |
| Pruebas de Integración | 2-3 horas | Pendiente |
| Documentación | 2-3 horas | Pendiente |
| **Total** | **18-26 horas** | **Pendiente** |

---

## Criterios de Éxito (Más Honestos)

### Telemetría Correcta
- `ast_cache_hit_count` > 0 y `ast_cache_miss_count` > 0 en un run que parsea N archivos
- Telemetría NO incluye contenido crudo
- Telemetría incluye metadatos seguros

### Cache Compartido
- En un mismo proceso largo (ej ctx sync), hit_rate sube claramente en re-reads
- Reducción de parseos redundantes > 50%
- Tasa de cache hits > 30%

### Persistencia de Cache
- `ast symbols` 2 ejecuciones seguidas → 2da es hit solo si persistencia está ON
- Tasa de cache hits en segunda ejecución > 80%
- SQLite segmentado por repo funciona correctamente

### Evicción LRU
- Cache no crece sin límite
- Evicciones LRU funcionan correctamente
- Uso de memoria está acotado

### Clean Architecture
- No hay estado oculto global
- Cache se inyecta como dependencia
- Protocolo `AstCache` es respetado

---

## Próximos Pasos

1. **Revisar y aprobar este plan v2**
2. **Implementar Fase 0**: Crear pruebas que reproducen los bugs
3. **Implementar Fase 1**: Abstracción de Cache (Clean Architecture)
4. **Implementar Fase 2**: Modificar SkeletonMapBuilder para Usar AstCache
5. **Implementar Fase 3**: Corregir Telemetría de Cache
6. **Implementar Fase 4**: Inyectar Cache en Componentes (DI)
7. **Ejecutar pruebas unitarias y de integración**
8. **Actualizar documentación**
9. **Validar métricas y rendimiento**

---

**Generado**: 2026-01-05 04:59 UTC  
**Estado**: Planificación v2 (incorporando Clean Architecture y mejores prácticas)
