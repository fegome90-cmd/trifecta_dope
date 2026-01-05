# Instrucciones para Validar el Sistema de Cache de AST

## Objetivo

Validar que el sistema de cache de AST v1 funciona correctamente mediante la ejecución de comandos CLI y captura de métricas.

## Preparación

1. **Asegurar que el entorno está instalado:**
   ```bash
   cd /workspaces/trifecta_dope/
   make install
   ```

2. **Activar telemetría (opcional pero recomendado):**
   ```bash
   export TRIFECTA_TELEMETRY_LEVEL=lite
   ```

## Ejecución de Validación

### Paso 1: Ejecutar comandos AST sin cache persistente

```bash
# Ejecutar 3 veces el mismo comando (debería ver cache hits)
uv run trifecta ast symbols "sym://python/mod/mymodule" --segment . --telemetry lite
uv run trifecta ast symbols "sym://python/mod/mymodule" --segment . --telemetry lite
uv run trifecta ast symbols "sym://python/mod/mymodule" --segment . --telemetry lite
```

**Esperado:**
- Primera ejecución: `cache_status: "miss"`
- Segunda ejecución: `cache_status: "hit"`
- Tercera ejecución: `cache_status: "hit"`

### Paso 2: Ejecutar con cache persistente

```bash
# Limpiar cache anterior si existe
uv run trifecta ast clear-cache --segment .

# Ejecutar con cache persistente
uv run trifecta ast symbols "sym://python/mod/mymodule" --segment . --persist-cache --telemetry lite
uv run trifecta ast symbols "sym://python/mod/mymodule" --segment . --persist-cache --telemetry lite
```

**Esperado:**
- Primera ejecución: `cache_status: "miss"`
- Segunda ejecución: `cache_status: "hit"` (desde SQLite persistente)

### Paso 3: Verificar estadísticas de cache

```bash
# Ver estadísticas de cache persistente
uv run trifecta ast cache-stats --segment .
```

**Esperado:**
```json
{
  "status": "ok",
  "segment": ".",
  "cache_path": ".trifecta/cache/ast_cache_....db",
  "stats": {
    "entries": 1,
    "bytes": 1234,
    "hits": 1,
    "misses": 1,
    "hit_rate": "50.00%"
  }
}
```

### Paso 4: Analizar telemetría

```bash
# Ver reporte de telemetría
uv run trifecta telemetry report -s . --last 10
```

**Esperado:**
- Eventos `ast.symbols` con `cache_status: "hit"` y `cache_status: "miss"`
- Eventos `ast.parse` con `cache_key` y `cache_status`

## Métricas a Capturar

### Métricas de Cache

| Métrica | Valor Esperado | Cómo Capturar |
|----------|----------------|----------------|
| **Cache Hit Rate** | > 30% con cache compartido | `trifecta ast cache-stats` → `hit_rate` |
| **Cache Hit Rate (persistente)** | > 80% en segunda ejecución | Ejecutar mismo comando 2 veces → contar hits |
| **Cache Size** | < 100MB | `trifecta ast cache-stats` → `bytes` |
| **Cache Entries** | < 10,000 | `trifecta ast cache-stats` → `entries` |

### Métricas de Telemetría

| Métrica | Valor Esperado | Cómo Capturar |
|----------|----------------|----------------|
| **cache_status en eventos** | "hit" o "miss" | `trifecta telemetry report -s . --last 10` → buscar `cache_status` |
| **cache_key en eventos** | Formato: `{segment}:{file}:{hash}:{version}` | `trifecta telemetry report -s . --last 10` → buscar `cache_key` |
| **symbols_count** | Número de símbolos extraídos | `trifecta telemetry report -s . --last 10` → buscar `symbols_count` |

## Validación de Funcionalidad

### Test 1: Cache Compartido Entre Componentes

**Objetivo:** Verificar que `SkeletonMapBuilder` usa la misma instancia de `AstCache` entre componentes.

**Instrucciones:**
1. Ejecutar `trifecta ctx search` para buscar símbolos
2. Ejecutar `trifecta ast symbols` para extraer símbolos
3. Verificar que ambos usan el mismo cache (mismo `cache_key`)

**Esperado:**
- Ambos comandos usan el mismo `cache_key` para el mismo archivo
- Cache hit rate aumenta con múltiples ejecuciones

### Test 2: Evicción LRU

**Objetivo:** Verificar que el cache no crece sin límites.

**Instrucciones:**
1. Ejecutar `trifecta ast symbols` para 100 archivos diferentes
2. Verificar estadísticas de cache
3. Ejecutar para 1 archivo más veces
4. Verificar que entradas antiguas fueron evictadas

**Esperado:**
- `entries` ≤ `max_entries` (10,000 por defecto)
- `bytes` ≤ `max_bytes` (100MB por defecto)
- Entradas antiguas son evictadas cuando se alcanza el límite

### Test 3: Persistencia SQLite

**Objetivo:** Verificar que el cache persiste entre ejecuciones.

**Instrucciones:**
1. Ejecutar `trifecta ast symbols --persist-cache` para un archivo
2. Terminar la sesión (cerrar terminal)
3. Iniciar nueva sesión
4. Ejecutar `trifecta ast symbols --persist-cache` para el mismo archivo
5. Verificar que fue cache hit

**Esperado:**
- Segunda ejecución muestra `cache_status: "hit"`
- `trifecta ast cache-stats` muestra `hits > 0`

## Reporte de Resultados

### Formato de Reporte

```markdown
# Reporte de Validación del Sistema de Cache de AST

## Fecha
2026-01-05

## Ejecuciones Realizadas

### Test 1: Cache Compartido
- **Comandos ejecutados:** [lista de comandos]
- **Cache Hit Rate:** [porcentaje]
- **Observaciones:** [notas]

### Test 2: Evicción LRU
- **Archivos procesados:** [número]
- **Cache Entries:** [número]
- **Cache Bytes:** [bytes]
- **Observaciones:** [notas]

### Test 3: Persistencia SQLite
- **Primera ejecución:** [miss/hit]
- **Segunda ejecución:** [miss/hit]
- **Observaciones:** [notas]

## Métricas de Telemetría

### Eventos de Cache
- **Total de eventos:** [número]
- **Hits:** [número]
- **Misses:** [número]
- **Hit Rate:** [porcentaje]

### Cache Keys
- **Formato correcto:** [sí/no]
- **Ejemplo:** [ejemplo de cache_key]

## Conclusión

- **Sistema funciona correctamente:** [sí/no]
- **Problemas encontrados:** [lista de problemas]
- **Recomendaciones:** [lista de recomendaciones]
```

## Comandos Útiles

```bash
# Ver estadísticas de cache
uv run trifecta ast cache-stats --segment .

# Limpiar cache
uv run trifecta ast clear-cache --segment .

# Ver telemetría reciente
uv run trifecta telemetry report -s . --last 10

# Ver telemetría de AST
uv run trifecta telemetry report -s . --last 10 | grep ast

# Exportar telemetría para análisis
uv run trifecta telemetry export -s . --last 10 > telemetry.json
```

## Troubleshooting

### Problema: Cache no funciona

**Síntomas:**
- Siempre muestra `cache_status: "miss"`
- `trifecta ast cache-stats` muestra 0 hits

**Soluciones:**
1. Verificar que `SkeletonMapBuilder` recibe `AstCache` como parámetro
2. Verificar que `ParseResult` incluye `cache_status` y `cache_key`
3. Verificar que `track_parse()` usa `ParseResult` en lugar de booleano

### Problema: Cache crece sin límite

**Síntomas:**
- `entries` > 10,000
- `bytes` > 100MB

**Soluciones:**
1. Verificar que `InMemoryLRUCache` tiene `max_entries` y `max_bytes`
2. Verificar que `SQLiteCache` tiene evicción LRU en `_evict_if_needed()`
3. Verificar que `CacheStats` muestra límites correctos

### Problema: Telemetría no muestra cache_status

**Síntomas:**
- Eventos no tienen `cache_status`
- Eventos no tienen `cache_key`

**Soluciones:**
1. Verificar que `track_parse()` acepta `ParseResult`
2. Verificar que `ParseResult` tiene `status` y `cache_key`
3. Verificar que telemetría está activada (`TRIFECTA_TELEMETRY_LEVEL=lite`)
