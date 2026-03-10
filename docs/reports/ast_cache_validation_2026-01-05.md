# Reporte de Validación del Sistema de Cache de AST

## Fecha
2026-01-05 06:17 UTC

## Entorno
- **Workspace**: `/workspaces/trifecta_dope`
- **Branch**: main
- **Python**: 3.14.2
- **Telemetría**: lite
- **Comando base**: `uv run trifecta ast symbols`

## Resumen Ejecutivo

**Estado**: ❌ Sistema NO funciona correctamente  
**Cache Hit Rate Obtenido**: 0% (Esperado: > 30%)  
**Problemas Críticos Encontrados**: 3  
**Funcionalidades Validadas**: 2/5

---

## Ejecuciones Realizadas

### Test 1: Cache Sin Persistencia (3 ejecuciones)

**Comando ejecutado:**
```bash
uv run trifecta ast symbols "sym://python/mod/src.domain.result" --segment . --telemetry lite
```

**Resultados:**

| Ejecución | Cache Status | Cache Key | Symbols Count | Latencia |
|-----------|--------------|-----------|---------------|----------|
| 1 | miss | `.:/workspaces/.../src/domain/result.py:2731f352c3eecd48:1` | 2 | ~1ms |
| 2 | miss | `.:/workspaces/.../src/domain/result.py:2731f352c3eecd48:1` | 2 | ~1ms |
| 3 | miss | `.:/workspaces/.../src/domain/result.py:2731f352c3eecd48:1` | 2 | ~1ms |

**Cache Hit Rate**: 0% ❌ (Esperado: > 30% en ejecuciones 2 y 3)

**Observaciones:**
- ✅ Símbolos extraídos correctamente (2 clases: `Ok`, `Err`)
- ✅ Cache key generado con formato correcto
- ❌ Cache NO persiste entre invocaciones del CLI
- ❌ Cada `uv run` inicia proceso nuevo → cache en memoria se pierde

---

### Test 2: Cache Persistente (SQLite)

**Comando ejecutado:**
```bash
# Limpieza
uv run trifecta ast clear-cache --segment .

# Ejecución con --persist-cache
uv run trifecta ast symbols "sym://python/mod/src.domain.result" --segment . --persist-cache --telemetry lite
```

**Resultados:**

| Ejecución | Resultado | Error |
|-----------|-----------|-------|
| Clear Cache | ✅ OK | No cache found (esperado) |
| 1ª con --persist-cache | ❌ ERROR | `Object of type SymbolInfo is not JSON serializable` |
| 2ª con --persist-cache | ⏭️ No ejecutada | Bloqueado por error anterior |

**Observaciones:**
- ❌ **Bug crítico**: `SymbolInfo` no se puede serializar para SQLite
- ❌ Cache persistente completamente no funcional
- 📍 Ubicación del error: `src/domain/ast_cache.py` (método de serialización)

---

### Test 3: Estadísticas de Cache

**Comando ejecutado:**
```bash
uv run trifecta ast cache-stats --segment .
```

**Resultado:**
```
TypeError: unsupported operand type(s) for +: 'NoneType' and 'NoneType'
```

**Observaciones:**
- ❌ **Bug crítico**: Estadísticas fallan con `TypeError`
- 📍 Línea 312 en `src/domain/ast_cache.py`: `total = hits + misses`
- 🔍 Causa: Columnas `hits` y `misses` retornan `None` cuando no hay datos
- 💡 Fix sugerido: Usar `COALESCE(hits, 0)` en query SQL o verificar `None` antes de sumar

---

## Métricas de Telemetría

### Eventos Capturados

**Total de eventos ast.symbols**: 4

**Sample de evento:**
```json
{
  "timestamp": "2026-01-05T06:17:23.456Z",
  "command": "ast.symbols",
  "cache_status": "miss",
  "cache_key": "/workspaces/trifecta_dope:/workspaces/trifecta_dope/src/domain/result.py:2731f352c3eecd48:1",
  "symbols_count": 2,
  "latency_ms": 1.2
}
```

### Validación de Métricas

| Métrica | Esperado | Obtenido | Estado |
|---------|----------|----------|--------|
| `cache_status` presente | ✅ Sí | ✅ Sí ("miss") | ✅ PASS |
| `cache_key` formato correcto | `{seg}:{file}:{hash}:{ver}` | `/workspaces/trifecta_dope:/workspaces/.../result.py:2731f352c3eecd48:1` | ✅ PASS |
| `symbols_count` presente | ✅ Sí | ✅ Sí (2) | ✅ PASS |
| Cache hits registrados | > 0 | 0 | ❌ FAIL |

---

## Análisis de Problemas

### 🔴 Problema 1: Cache No Persiste Entre Invocaciones CLI

**Severidad**: Crítica  
**Impacto**: Cache hit rate = 0% en lugar de > 30%

**Causa Raíz:**
- Cada comando `uv run trifecta ast symbols` inicia un proceso Python nuevo
- El cache en memoria (`LRUCache`) se destruye al terminar el proceso
- No hay mecanismo de cache compartido entre procesos sin `--persist-cache`

**Evidencia:**
- 3 ejecuciones consecutivas → 3 misses (cache_key idéntico)
- Sin `--persist-cache`: cache solo vive durante la ejecución del comando

**Soluciones Propuestas:**

1. **Opción A**: Hacer `--persist-cache` obligatorio por defecto
   - Cambiar default de `persist_cache=False` a `True`
   - Pros: Solución simple, cache funciona inmediatamente
   - Cons: Requiere arreglar Problema 2 primero

2. **Opción B**: Implementar cache compartido en memoria (daemon)
   - Levantar proceso daemon que mantiene cache en memoria
   - CLI se conecta al daemon vía IPC/socket
   - Pros: Mejor performance que SQLite
   - Cons: Más complejo, requiere gestión de daemon

3. **Opción C**: Cache en filesystem (pickle/json)
   - Serializar cache a archivo entre ejecuciones
   - Pros: Simple, sin daemon
   - Cons: Latencia de I/O en cada comando

**Recomendación**: Arreglar Problema 2 y aplicar Opción A (--persist-cache por defecto)

---

### 🔴 Problema 2: Cache Persistente No Serializa `SymbolInfo`

**Severidad**: Crítica (bloqueante para Problema 1)  
**Impacto**: `--persist-cache` completamente no funcional

**Error:**
```
TypeError: Object of type SymbolInfo is not JSON serializable
```

**Causa Raíz:**
- `SymbolInfo` es un objeto custom (probablemente dataclass/pydantic)
- SQLite cache intenta serializar a JSON pero no hay encoder custom

**Ubicación:**
- `src/domain/ast_cache.py` - método que serializa valores para SQLite

**Soluciones Propuestas:**

1. **Opción A**: Implementar `to_dict()` / `from_dict()` en `SymbolInfo`
   ```python
   # En SymbolInfo
   def to_dict(self) -> dict:
       return {"kind": self.kind, "name": self.name, "line": self.line}

   @classmethod
   def from_dict(cls, data: dict):
       return cls(**data)

   # En SQLiteCache
   value_json = json.dumps([s.to_dict() for s in symbols])
   symbols = [SymbolInfo.from_dict(d) for d in json.loads(value_json)]
   ```

2. **Opción B**: Usar `pickle` en lugar de JSON
   ```python
   import pickle
   value_blob = pickle.dumps(symbols)  # bytes, no JSON
   symbols = pickle.loads(value_blob)
   ```
   - Pros: Funciona con cualquier objeto Python
   - Cons: No portable, inseguro para datos untrusted

3. **Opción C**: Registrar custom JSON encoder
   ```python
   class SymbolInfoEncoder(json.JSONEncoder):
       def default(self, obj):
           if isinstance(obj, SymbolInfo):
               return obj.__dict__
           return super().default(obj)
   ```

**Recomendación**: Opción A (más limpio y testeable) o Opción B (más rápido de implementar)

---

### 🔴 Problema 3: Stats de Cache Fallan con TypeError

**Severidad**: Media  
**Impacto**: No se pueden ver métricas de cache (observabilidad cero)

**Error:**
```
TypeError: unsupported operand type(s) for +: 'NoneType' and 'NoneType'
Línea 312: total = hits + misses
```

**Causa Raíz:**
- Query SQL retorna `(entries=0, hits=None, misses=None, bytes=None)` cuando DB vacío
- Código asume valores numéricos sin verificar `None`

**Código Problemático:**
```python
# src/domain/ast_cache.py:312
entries, hits, misses, current_bytes = row or (0, 0, 0, 0)
total = hits + misses  # ❌ hits=None, misses=None
```

**Soluciones Propuestas:**

1. **Fix en Python** (defensive coding):
   ```python
   entries, hits, misses, current_bytes = row or (0, 0, 0, 0)
   hits = hits or 0
   misses = misses or 0
   current_bytes = current_bytes or 0
   total = hits + misses
   ```

2. **Fix en SQL** (COALESCE):
   ```sql
   SELECT
     COUNT(*) as entries,
     COALESCE(SUM(CASE WHEN hit=1 THEN 1 ELSE 0 END), 0) as hits,
     COALESCE(SUM(CASE WHEN hit=0 THEN 1 ELSE 0 END), 0) as misses,
     COALESCE(SUM(LENGTH(value)), 0) as current_bytes
   FROM cache
   ```

**Recomendación**: Aplicar ambos fixes (defense in depth)

---

## Validación de Funcionalidad

### ❌ Test 1: Cache Compartido Entre Componentes

**Estado**: NO VALIDADO (bloqueado por Problema 1)

**Planeado:**
- Ejecutar `trifecta ctx search` (usa SkeletonMapBuilder)
- Ejecutar `trifecta ast symbols` (mismo componente)
- Verificar que ambos usan mismo cache_key

**Resultado**: No ejecutado (cache no persiste entre comandos)

---

### ❌ Test 2: Evicción LRU

**Estado**: NO VALIDADO (bloqueado por Problema 1)

**Planeado:**
- Ejecutar para 100+ archivos
- Verificar `entries ≤ max_entries` (10,000)
- Verificar `bytes ≤ max_bytes` (100MB)

**Resultado**: No ejecutado (stats fallan, cache no persiste)

---

### ❌ Test 3: Persistencia SQLite

**Estado**: NO VALIDADO (bloqueado por Problema 2)

**Planeado:**
- Ejecutar con `--persist-cache`
- Cerrar terminal
- Nueva sesión → verificar cache hit

**Resultado**: No ejecutado (serialización falla)

---

## Métricas Finales vs Esperadas

| Métrica | Esperado | Obtenido | Gap |
|---------|----------|----------|-----|
| **Cache Hit Rate (memoria)** | > 30% | 0% | -30% ❌ |
| **Cache Hit Rate (persistente)** | > 80% | N/A (error) | N/A ❌ |
| **Cache Size** | < 100MB | N/A (error) | N/A ❌ |
| **Cache Entries** | < 10,000 | N/A (error) | N/A ❌ |
| **Telemetry: cache_status** | ✅ presente | ✅ presente | ✅ PASS |
| **Telemetry: cache_key** | ✅ formato correcto | ✅ formato correcto | ✅ PASS |
| **Telemetry: symbols_count** | ✅ presente | ✅ presente | ✅ PASS |

---

## Conclusión

### ❌ Sistema NO Funciona Correctamente

**Resumen:**
- ✅ **Extracción de símbolos**: Funciona perfectamente (AST parsing OK)
- ✅ **Telemetría**: Captura correctamente cache_status, cache_key, symbols_count
- ❌ **Cache en memoria**: NO persiste entre invocaciones CLI (0% hit rate)
- ❌ **Cache persistente**: Error de serialización (completamente roto)
- ❌ **Observabilidad**: Stats fallan con TypeError (no se pueden ver métricas)

**Valoración de Optimización:**
- **Objetivo**: Reducir latencia vía cache compartido
- **Resultado**: Latencia es baja (~1ms) pero NO hay cache hits
- **Impacto Real**: **Sin beneficio** (cada llamada re-parsea AST)

---

## Problemas Encontrados (Prioridad)

1. **🔴 P0 - Cache persistente no serializa SymbolInfo**
   - Bloquea funcionalidad crítica
   - Fix: Implementar `to_dict()`/`from_dict()` o usar pickle

2. **🔴 P0 - Cache en memoria no persiste entre CLI calls**
   - Cache hit rate = 0% (esperado > 30%)
   - Fix: Hacer `--persist-cache` default (después de arreglar #1)

3. **🟡 P1 - Stats de cache fallan con TypeError**
   - Sin observabilidad del cache
   - Fix: Verificar `None` o usar `COALESCE` en SQL

---

## Recomendaciones

### Inmediatas (Sprint Actual)

1. **Fix Serialización** (2-3 horas)
   - Implementar `SymbolInfo.to_dict()` / `from_dict()`
   - Añadir tests unitarios de serialización
   - Verificar round-trip: `obj → dict → obj`

2. **Fix Stats TypeError** (30 minutos)
   - Añadir defensive checks para `None`
   - Usar `COALESCE` en query SQL
   - Test con DB vacío

3. **Enable Persistencia por Default** (15 minutos)
   - Cambiar `persist_cache=False` → `True` en CLI
   - Actualizar docs

### Medio Plazo (Próximo Sprint)

4. **Tests de Integración para Cache**
   - Test: Ejecutar 2x mismo comando → 2º debe ser hit
   - Test: Verificar evicción LRU funciona
   - Test: Stats muestra hits/misses correctamente

5. **Benchmarking Real**
   - Medir latencia con cache hits vs misses
   - Medir impacto en `ctx search` (múltiples archivos)
   - Documentar mejoras de performance

### Largo Plazo (Backlog)

6. **Considerar Cache Daemon** (si performance es crítica)
   - Evaluar si SQLite I/O es bottleneck
   - Implementar daemon con cache en memoria compartido
   - Comparar performance vs SQLite

---

## Comandos Útiles de Debugging

```bash
# Ver estructura del DB de cache
sqlite3 .trifecta/cache/ast_cache__workspaces_trifecta_dope.db ".schema"

# Ver contenido del cache (después de fix serialización)
sqlite3 .trifecta/cache/ast_cache__workspaces_trifecta_dope.db "SELECT key, LENGTH(value) FROM cache LIMIT 10"

# Ver hits/misses (después de fix stats)
uv run trifecta ast cache-stats --segment .

# Limpiar cache para testing
uv run trifecta ast clear-cache --segment .

# Ver telemetría de AST únicamente
grep 'ast.symbols' _ctx/telemetry/events.jsonl | tail -10 | jq .

# Test manual de serialización
python3 -c "
from src.domain.symbol_query import SymbolInfo
import json
s = SymbolInfo(kind='class', name='Test', line=10)
print(json.dumps(s.__dict__))  # Debería funcionar
"
```

---

## Archivos Involucrados

| Archivo | Líneas Críticas | Problema |
|---------|----------------|----------|
| [src/domain/ast_cache.py](src/domain/ast_cache.py#L312) | 312 | TypeError en stats |
| [src/domain/ast_cache.py](src/domain/ast_cache.py) | - | Serialización de SymbolInfo |
| [src/infrastructure/cli_ast.py](src/infrastructure/cli_ast.py#L45) | 45 | Default persist_cache=False |
| [src/domain/symbol_query.py](src/domain/symbol_query.py) | - | SymbolInfo class (falta to_dict) |

---

## Próximos Pasos

1. ✅ **Reporte validación creado** → Este documento
2. ⬜ **Crear issues en GitHub** para los 3 problemas críticos
3. ⬜ **Fix serialización SymbolInfo** (P0)
4. ⬜ **Fix stats TypeError** (P1)
5. ⬜ **Re-ejecutar validación** para confirmar fixes
6. ⬜ **Actualizar RELEASE_NOTES** con hallazgos

---

**Firma**: GitHub Copilot  
**Fecha**: 2026-01-05 06:17 UTC  
**Versión**: AST Cache v1 (pre-fix)
