# Análisis Profundo del Sistema de Cache de AST

**Fecha**: 2026-01-05  
**Fuente**: Código fuente de src/application/ast_parser.py, src/application/telemetry_pr2.py, src/application/pr2_context_searcher.py, src/infrastructure/cli_ast.py

---

## Resumen Ejecutivo

El sistema de cache de AST tiene **problemas críticos** que explican la alta tasa de cache misses (57.5%) observada en las métricas:

1. **Cache no compartido entre componentes**: Cada componente crea su propia instancia de SkeletonMapBuilder
2. **Telemetría de cache rota**: Siempre reporta cache_hit=False independientemente del resultado real
3. **Instancias efímeras**: El comando ast symbols crea una nueva instancia cada vez, invalidando el cache

---

## Arquitectura del Sistema de Cache

### 1. SkeletonMapBuilder - El Componente de Cache

**Archivo**: src/application/ast_parser.py:22

Clave de Cache: SHA256 del contenido del archivo, truncado a 8 caracteres
Almacenamiento en memoria: self._cache es un diccionario en memoria
Política de invalidación: Basada en contenido (si el contenido cambia, el hash cambia)
Alcance: Solo top-level (funciones y clases, no anidados)

---

## Problemas Críticos Identificados

### Problema 1: Cache No Compartido Entre Componentes 🔴

**Descripción**: Cada componente crea su propia instancia de SkeletonMapBuilder, lo que significa que el cache NO se comparte entre componentes.

**Evidencia**:

1. PR2ContextSearcher (src/application/pr2_context_searcher.py:56): self.ast_builder = SkeletonMapBuilder()
2. ASTTelemetry (src/application/telemetry_pr2.py:30): self.ast_counter = SkeletonMapBuilder()
3. CLI AST (src/infrastructure/cli_ast.py:64): builder = SkeletonMapBuilder()

**Impacto**:
- Cada componente tiene su propio cache independiente
- Si un componente parsea un archivo, otros componentes NO se benefician de ese cache
- El cache es ineficiente porque no se comparte

---

### Problema 2: Telemetría de Cache Rota 🔴

**Descripción**: El método track_parse() de ASTTelemetry siempre recibe cache_hit=False, independientemente de si fue un cache hit o miss real.

**Evidencia**:

**Archivo**: src/application/pr2_context_searcher.py:184

```python
def _extract_skeleton(self, file_path: Path) -> None:
    try:
        content = file_path.read_text()
        symbols = self.ast_builder.build(file_path, content)  # ← Puede ser cache hit o miss
        
        # Emit telemetry
        self.ast_tel.track_parse(file_path, content, symbols, cache_hit=False)  # ← SIEMPRE False!
```

**Problema**:
- Línea 175: self.ast_builder.build(file_path, content) puede retornar desde cache o parsear el archivo
- Línea 184: self.ast_tel.track_parse(..., cache_hit=False) SIEMPRE pasa False

**Resultado**:
- La telemetría SIEMPRE reporta cache_hit=False
- Los contadores ast_cache_hit_count y ast_cache_miss_count son incorrectos
- La tasa de cache hits reportada (42.5%) es **falsa**

**Análisis de Código de SkeletonMapBuilder**:

El método build() NO retorna información sobre si fue un cache hit o miss. Solo retorna los símbolos.

---

### Problema 3: Instancias Efímeras en CLI 🔴

**Descripción**: El comando ast symbols crea una nueva instancia de SkeletonMapBuilder cada vez que se ejecuta, lo que significa que el cache se pierde entre ejecuciones.

**Evidencia**:

**Archivo**: src/infrastructure/cli_ast.py:64

```python
@ast_app.command("symbols")
def symbols(...):
    builder = SkeletonMapBuilder()  # ← NUEVA instancia cada vez
    symbols = builder.build(file_path)  # ← Cache siempre vacío
```

**Impacto**:
- Cada ejecución de ast symbols crea una nueva instancia de SkeletonMapBuilder
- El cache está vacío en cada ejecución
- El cache es inútil en este contexto

---

## Análisis de Métricas Reales vs Reportadas

### Métricas Reportadas (Incorrectas)

Según _ctx/telemetry/metrics.json:
- parse_count: 40
- cache_hit_count: 17
- cache_miss_count: 23

**Interpretación anterior**:
- 42.5% de cache hits (17/40)
- 57.5% de cache misses (23/40)

**Problema**: Estas métricas son **incorrectas** porque track_parse() siempre pasa cache_hit=False.

### Métricas Reales (Estimadas)

Basado en el análisis del código:

**Escenario 1: CLI ast symbols (3 ejecuciones en el historial)**
- Cada ejecución crea una nueva instancia de SkeletonMapBuilder
- Cache siempre vacío → 100% de cache misses
- 3 parseos reales

**Escenario 2: PR2ContextSearcher (resto de las operaciones)**
- Usa una sola instancia de SkeletonMapBuilder
- Cache puede ser efectivo SI el mismo archivo se parsea múltiples veces
- Sin embargo, la telemetría no reporta correctamente

**Conclusión**: No es posible determinar la tasa real de cache hits con la telemetría actual.

---

## Recomendaciones de Solución

### Solución 1: Compartir Cache Entre Componentes

**Prioridad**: ALTA

**Implementación**:

1. Crear un singleton de SkeletonMapBuilder con _global_cache
2. Usar el singleton en todos los componentes

**Beneficios**:
- Cache compartido entre componentes
- Reducción de parseos redundantes
- Mejora de rendimiento

---

### Solución 2: Corregir Telemetría de Cache

**Prioridad**: ALTA

**Implementación**:

1. Modificar SkeletonMapBuilder.build() para retornar tuple[List[SymbolInfo], bool]
2. Actualizar PR2ContextSearcher para usar el valor de cache_hit

**Beneficios**:
- Telemetría correcta de cache hits/misses
- Métricas confiables
- Capacidad de diagnosticar problemas de rendimiento

---

### Solución 3: Persistir Cache Entre Ejecuciones de CLI

**Prioridad**: MEDIA

**Implementación**:

1. Usar un cache persistente en disco con pickle
2. Llamar a save_cache() al final del comando

**Beneficios**:
- Cache persistente entre ejecuciones de CLI
- Reducción de parseos redundantes
- Mejora de rendimiento en uso interactivo

---

## Conclusión

### Estado Actual

El sistema de cache de AST tiene **problemas críticos**:

1. 🔴 **Cache no compartido**: Cada componente tiene su propio cache independiente
2. 🔴 **Telemetría rota**: Siempre reporta cache_hit=False
3. 🔴 **Instancias efímeras**: El CLI crea una nueva instancia cada vez

### Impacto en Métricas

- La tasa de cache hits reportada (42.5%) es **falsa**
- La tasa real de cache hits es **desconocida**
- Las métricas de telemetría no son confiables

### Prioridades de Solución

1. **ALTA**: Corregir telemetría de cache (Solución 2)
2. **ALTA**: Compartir cache entre componentes (Solución 1)
3. **MEDIA**: Persistir cache entre ejecuciones de CLI (Solución 3)

### Próximos Pasos

1. Implementar Solución 2 para corregir la telemetría
2. Implementar Solución 1 para compartir el cache
3. Implementar Solución 3 para persistir el cache
4. Validar que las métricas son correctas después de las implementaciones

---

**Generado**: 2026-01-05 04:44 UTC  
**Fuente**: Análisis de código fuente
