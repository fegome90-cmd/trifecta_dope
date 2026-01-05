# Plan: Correcciones del Sistema de Cache de AST (v2)

**Fecha**: 2026-01-05
**Prioridad**: ALTA
**Estado**: Planificación
**Versión**: 2.0 (incorporando Clean Architecture y mejores prácticas)

---

## Resumen Ejecutivo

Este plan aborda los **3 problemas críticos** identificados en el análisis profundo del sistema de cache de AST:

1. **Cache no compartido entre componentes** 🔴
2. **Telemetría de cache rota** 🔴
3. **Instancias efímeras en CLI** 🔴

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

## Problemas Identificados

### Problema 1: Cache No Compartido Entre Componentes

**Descripción**: Cada componente crea su propia instancia de `SkeletonMapBuilder`, lo que significa que el cache NO se comparte entre componentes.

**Evidencia**:
- [`PR2ContextSearcher`](src/application/pr2_context_searcher.py:56): `self.ast_builder = SkeletonMapBuilder()`
- [`ASTTelemetry`](src/application/telemetry_pr2.py:30): `self.ast_counter = SkeletonMapBuilder()`
- [`CLI AST`](src/infrastructure/cli_ast.py:64): `builder = SkeletonMapBuilder()`

**Impacto**: El mismo archivo se parsea múltiples veces, una por cada componente.

---

### Problema 2: Telemetría de Cache Rota

**Descripción**: El método `track_parse()` de `ASTTelemetry` siempre recibe `cache_hit=False`, independientemente del resultado real.

**Evidencia**:
- [`pr2_context_searcher.py:184`](src/application/pr2_context_searcher.py:184): `self.ast_tel.track_parse(..., cache_hit=False)` SIEMPRE pasa `False`
- [`SkeletonMapBuilder.build()`](src/application/ast_parser.py:28): NO retorna información sobre si fue cache hit o miss

**Impacto**: 
- La telemetría SIEMPRE reporta `cache_hit=False`
- Los contadores `ast_cache_hit_count` y `ast_cache_miss_count` son incorrectos
- La tasa de cache hits reportada (42.5%) es **falsa**

---

### Problema 3: Instancias Efímeras en CLI

**Descripción**: El comando `ast symbols` crea una nueva instancia de `SkeletonMapBuilder` cada vez que se ejecuta.

**Evidencia**:
- [`cli_ast.py:64`](src/infrastructure/cli_ast.py:64): `builder = SkeletonMapBuilder()` crea NUEVA instancia cada vez

**Impacto**: El cache está vacío en cada ejecución, haciendo el cache inútil.

---

## Soluciones Propuestas

### Solución 1: Compartir Cache Entre Componentes (ALTA)

**Objetivo**: Implementar un cache global compartido entre todos los componentes.

**Archivos a Modificar**:
- [`src/application/ast_parser.py`](src/application/ast_parser.py:1)

**Cambios Específicos**:

1. **Agregar cache global al módulo**:
   ```python
   # src/application/ast_parser.py
   
   # Cache global compartido entre todas las instancias
   _global_cache: dict[str, List[SymbolInfo]] = {}
   _global_cache_lock = threading.Lock()
   ```

2. **Modificar constructor de SkeletonMapBuilder**:
   ```python
   class SkeletonMapBuilder:
       """Build skeleton maps from AST parsing."""
       
       def __init__(self, use_global_cache: bool = True):
           """
           Initialize SkeletonMapBuilder.
           
           Args:
               use_global_cache: If True, use global shared cache. If False, use local cache.
           """
           if use_global_cache:
               self._cache = _global_cache
               self._cache_lock = _global_cache_lock
           else:
               self._cache: dict[str, List[SymbolInfo]] = {}
               self._cache_lock = threading.Lock()
   ```

3. **Hacer thread-safe el acceso al cache**:
   ```python
   def build(self, file_path: Path, content: Optional[str] = None) -> List[SymbolInfo]:
       """Build skeleton from file content using stdlib ast.parse."""
       if content is None:
           try:
               content = file_path.read_text(errors="replace")
           except FileNotFoundError as e:
               raise FileNotFoundError(f"File not found: {file_path}") from e

       # Content hash for cache
       content_hash = hashlib.sha256(content.encode()).hexdigest()[:8]

       # Check cache (thread-safe)
       with self._cache_lock:
           if content_hash in self._cache:
               return self._cache[content_hash]

       # Parse with stdlib ast
       try:
           tree = ast_module.parse(content, filename=str(file_path))
       except SyntaxError:
           # Fail-closed: syntax errors return empty (could be logged)
           symbols: List[SymbolInfo] = []
           with self._cache_lock:
               self._cache[content_hash] = symbols
           return symbols

       # Extract top-level symbols (only top-level, not nested)
       symbols: List[SymbolInfo] = []

       for node in tree.body:  # tree.body gives only top-level nodes
           if isinstance(node, (ast_module.FunctionDef, ast_module.AsyncFunctionDef)):
               symbols.append(
                   SymbolInfo(
                       kind="function",
                       name=node.name,
                       qualified_name=node.name,
                       start_line=node.lineno,
                       end_line=node.end_lineno or node.lineno,
                       signature_stub=f"def {node.name}(...)",
                   )
               )
           elif isinstance(node, (ast_module.ClassDef)):
               symbols.append(
                   SymbolInfo(
                       kind="class",
                       name=node.name,
                       qualified_name=node.name,
                       start_line=node.lineno,
                       end_line=node.end_lineno or node.lineno,
                       signature_stub=f"class {node.name}:",
                   )
               )

       # Sort by line number
       symbols.sort(key=lambda s: s.start_line)

       # Cache and return (thread-safe)
       with self._cache_lock:
           self._cache[content_hash] = symbols
       return symbols
   ```

4. **Agregar método para limpiar cache global**:
   ```python
   @classmethod
   def clear_global_cache(cls) -> None:
       """Clear the global cache."""
       with _global_cache_lock:
           _global_cache.clear()
   ```

5. **Agregar método para obtener estadísticas del cache global**:
   ```python
   @classmethod
   def get_global_cache_stats(cls) -> dict[str, int]:
       """Get statistics about the global cache."""
       with _global_cache_lock:
           return {
               "entries": len(_global_cache),
               "total_symbols": sum(len(symbols) for symbols in _global_cache.values()),
           }
   ```

**Archivos a Actualizar (usar cache global)**:
- [`src/application/pr2_context_searcher.py`](src/application/pr2_context_searcher.py:56): `self.ast_builder = SkeletonMapBuilder(use_global_cache=True)`
- [`src/application/telemetry_pr2.py`](src/application/telemetry_pr2.py:30): `self.ast_counter = SkeletonMapBuilder(use_global_cache=True)`
- [`src/infrastructure/cli_ast.py`](src/infrastructure/cli_ast.py:64): `builder = SkeletonMapBuilder(use_global_cache=True)`

**Pruebas**:
- Verificar que el cache se comparte entre componentes
- Verificar que el cache es thread-safe
- Verificar que las estadísticas del cache son correctas

---

### Solución 2: Corregir Telemetría de Cache (ALTA)

**Objetivo**: Modificar `SkeletonMapBuilder.build()` para retornar información sobre cache hit/miss y actualizar `PR2ContextSearcher` para usar esa información.

**Archivos a Modificar**:
- [`src/application/ast_parser.py`](src/application/ast_parser.py:1)
- [`src/application/pr2_context_searcher.py`](src/application/pr2_context_searcher.py:1)
- [`src/infrastructure/cli_ast.py`](src/infrastructure/cli_ast.py:1)

**Cambios Específicos**:

#### Paso 1: Modificar SkeletonMapBuilder.build()

```python
def build(self, file_path: Path, content: Optional[str] = None) -> tuple[List[SymbolInfo], bool]:
    """
    Build skeleton from file content using stdlib ast.parse.
    
    Returns:
        (symbols, cache_hit) where cache_hit is True if from cache
    """
    if content is None:
        try:
            content = file_path.read_text(errors="replace")
        except FileNotFoundError as e:
            raise FileNotFoundError(f"File not found: {file_path}") from e

    # Content hash for cache
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:8]

    # Check cache (thread-safe)
    with self._cache_lock:
        if content_hash in self._cache:
            return self._cache[content_hash], True  # ← Cache hit

    # Parse with stdlib ast
    try:
        tree = ast_module.parse(content, filename=str(file_path))
    except SyntaxError:
        # Fail-closed: syntax errors return empty (could be logged)
        symbols: List[SymbolInfo] = []
        with self._cache_lock:
            self._cache[content_hash] = symbols
        return symbols, False  # ← Cache miss

    # Extract top-level symbols (only top-level, not nested)
    symbols: List[SymbolInfo] = []

    for node in tree.body:  # tree.body gives only top-level nodes
        if isinstance(node, (ast_module.FunctionDef, ast_module.AsyncFunctionDef)):
            symbols.append(
                SymbolInfo(
                    kind="function",
                    name=node.name,
                    qualified_name=node.name,
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    signature_stub=f"def {node.name}(...)",
                )
            )
        elif isinstance(node, (ast_module.ClassDef)):
            symbols.append(
                SymbolInfo(
                    kind="class",
                    name=node.name,
                    qualified_name=node.name,
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    signature_stub=f"class {node.name}:",
                )
            )

    # Sort by line number
    symbols.sort(key=lambda s: s.start_line)

    # Cache and return (thread-safe)
    with self._cache_lock:
        self._cache[content_hash] = symbols
    return symbols, False  # ← Cache miss
```

#### Paso 2: Actualizar PR2ContextSearcher._extract_skeleton()

```python
def _extract_skeleton(self, file_path: Path) -> None:
    """Extract AST skeleton from file and register with selector."""
    if not file_path.exists():
        return

    t_start = perf_counter_ns()

    try:
        content = file_path.read_text()
        symbols, cache_hit = self.ast_builder.build(file_path, content)  # ← Obtener cache_hit

        # Register with selector
        self.selector.add_skeleton(str(file_path), symbols)

        # Emit telemetry
        t_end = perf_counter_ns()
        timing_ms = (t_end - t_start) // 1_000_000

        self.ast_tel.track_parse(file_path, content, symbols, cache_hit=cache_hit)  # ← Usar valor real
        self.tel.observe("ast.parse", timing_ms)

    except Exception:
        pass
```

#### Paso 3: Actualizar CLI AST

```python
@ast_app.command("symbols")
def symbols(
    uri: str = typer.Argument(..., help="sym://python/mod|type/..."),
    segment: str = typer.Option(".", "--segment"),
    telemetry_level: str = typer.Option("off", "--telemetry"),
):
    """Return symbols from Python modules using AST parsing (M1)."""
    root = Path(segment).resolve()
    telemetry = _get_telemetry(telemetry_level)

    try:
        # 1. Parse URI
        match SymbolQuery.parse(uri):
            case Err(e):
                _json_output({"status": "error", "error_code": e.code, "message": e.message})
                raise typer.Exit(1)
            case Ok(query):
                pass

        # 2. Resolve file_path (lean, fail-closed)
        path_as_dir = query.path.replace(".", "/")
        candidate_file = root / f"{path_as_dir}.py"
        candidate_init = root / path_as_dir / "__init__.py"

        if candidate_file.exists() and candidate_file.is_file():
            file_path = candidate_file
        elif candidate_init.exists() and candidate_init.is_file():
            file_path = candidate_init
        else:
            _json_output(
                {
                    "status": "error",
                    "error_code": "FILE_NOT_FOUND",
                    "message": f"Could not find module for {query.path}",
                }
            )
            raise typer.Exit(1)

        # 3. Invoke SkeletonMapBuilder (M1 REAL)
        t0 = time.perf_counter_ns()
        builder = SkeletonMapBuilder(use_global_cache=True)
        symbols, cache_hit = builder.build(file_path)  # ← Obtener cache_hit
        duration_ms = max(1, (time.perf_counter_ns() - t0) // 1_000_000)

        # 4. Return JSON (M1 Contract)
        output = {
            "status": "ok",
            "segment_root": str(root),
            "file_rel": str(file_path.relative_to(root)),
            "symbols": [{"kind": s.kind, "name": s.name, "line": s.start_line} for s in symbols],
            "cache_hit": cache_hit,  # ← Incluir en output
        }

        if telemetry:
            telemetry.event(
                "ast.symbols",
                {},
                {"status": "ok"},
                duration_ms,
                file=str(file_path.relative_to(root)),
                symbols_count=len(symbols),
                cache_hit=cache_hit,  # ← Incluir en telemetría
            )
            telemetry.flush()

        _json_output(output)

    except typer.Exit:
        raise
    except Exception as e:
        _json_output({"status": "error", "error_code": "INTERNAL_ERROR", "message": str(e)})
        raise typer.Exit(1)
```

**Pruebas**:
- Verificar que `build()` retorna `(symbols, cache_hit)`
- Verificar que `track_parse()` recibe el valor correcto de `cache_hit`
- Verificar que las métricas de telemetría son correctas
- Verificar que el output del CLI incluye `cache_hit`

---

### Solución 3: Persistir Cache Entre Ejecuciones de CLI (MEDIA)

**Objetivo**: Implementar un cache persistente en disco para que el cache se mantenga entre ejecuciones del CLI.

**Archivos a Modificar**:
- [`src/application/ast_parser.py`](src/application/ast_parser.py:1)
- [`src/infrastructure/cli_ast.py`](src/infrastructure/cli_ast.py:1)

**Cambios Específicos**:

#### Paso 1: Agregar persistencia de cache a SkeletonMapBuilder

```python
import pickle
from pathlib import Path

# Cache global compartido entre todas las instancias
_global_cache: dict[str, List[SymbolInfo]] = {}
_global_cache_lock = threading.Lock()

# Configuración de cache persistente
CACHE_DIR = Path.home() / ".trifecta"
CACHE_FILE = CACHE_DIR / "ast_cache.pkl"
CACHE_VERSION = 1  # Versión del formato de cache

def _load_persistent_cache() -> dict[str, List[SymbolInfo]]:
    """Load cache from disk if available."""
    if not CACHE_FILE.exists():
        return {}
    
    try:
        with open(CACHE_FILE, "rb") as f:
            data = pickle.load(f)
            # Verificar versión del cache
            if data.get("version") != CACHE_VERSION:
                return {}
            return data.get("cache", {})
    except Exception:
        # Si hay error al cargar, retornar cache vacío
        return {}

def _save_persistent_cache(cache: dict[str, List[SymbolInfo]]) -> None:
    """Save cache to disk."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "version": CACHE_VERSION,
            "cache": cache,
        }
        with open(CACHE_FILE, "wb") as f:
            pickle.dump(data, f)
    except Exception:
        # Si hay error al guardar, silenciosamente fallar
        pass

# Cargar cache persistente al inicio del módulo
_global_cache = _load_persistent_cache()
```

#### Paso 2: Modificar constructor de SkeletonMapBuilder

```python
class SkeletonMapBuilder:
    """Build skeleton maps from AST parsing."""
    
    def __init__(self, use_global_cache: bool = True, auto_save: bool = False):
        """
        Initialize SkeletonMapBuilder.
        
        Args:
            use_global_cache: If True, use global shared cache. If False, use local cache.
            auto_save: If True, automatically save cache to disk after each build.
        """
        if use_global_cache:
            self._cache = _global_cache
            self._cache_lock = _global_cache_lock
        else:
            self._cache: dict[str, List[SymbolInfo]] = {}
            self._cache_lock = threading.Lock()
        self.auto_save = auto_save
```

#### Paso 3: Modificar build() para guardar cache automáticamente

```python
def build(self, file_path: Path, content: Optional[str] = None) -> tuple[List[SymbolInfo], bool]:
    """
    Build skeleton from file content using stdlib ast.parse.
    
    Returns:
        (symbols, cache_hit) where cache_hit is True if from cache
    """
    if content is None:
        try:
            content = file_path.read_text(errors="replace")
        except FileNotFoundError as e:
            raise FileNotFoundError(f"File not found: {file_path}") from e

    # Content hash for cache
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:8]

    # Check cache (thread-safe)
    with self._cache_lock:
        if content_hash in self._cache:
            return self._cache[content_hash], True  # ← Cache hit

    # Parse with stdlib ast
    try:
        tree = ast_module.parse(content, filename=str(file_path))
    except SyntaxError:
        # Fail-closed: syntax errors return empty (could be logged)
        symbols: List[SymbolInfo] = []
        with self._cache_lock:
            self._cache[content_hash] = symbols
        if self.auto_save:
            _save_persistent_cache(self._cache)
        return symbols, False  # ← Cache miss

    # Extract top-level symbols (only top-level, not nested)
    symbols: List[SymbolInfo] = []

    for node in tree.body:  # tree.body gives only top-level nodes
        if isinstance(node, (ast_module.FunctionDef, ast_module.AsyncFunctionDef)):
            symbols.append(
                SymbolInfo(
                    kind="function",
                    name=node.name,
                    qualified_name=node.name,
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    signature_stub=f"def {node.name}(...)",
                )
            )
        elif isinstance(node, (ast_module.ClassDef)):
            symbols.append(
                SymbolInfo(
                    kind="class",
                    name=node.name,
                    qualified_name=node.name,
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    signature_stub=f"class {node.name}:",
                )
            )

    # Sort by line number
    symbols.sort(key=lambda s: s.start_line)

    # Cache and return (thread-safe)
    with self._cache_lock:
        self._cache[content_hash] = symbols
    
    # Guardar cache automáticamente si está habilitado
    if self.auto_save:
        _save_persistent_cache(self._cache)
    
    return symbols, False  # ← Cache miss
```

#### Paso 4: Agregar método para guardar cache manualmente

```python
def save_cache(self) -> None:
    """Save cache to disk manually."""
    if self._cache is _global_cache:
        _save_persistent_cache(self._cache)
```

#### Paso 5: Actualizar CLI AST para usar cache persistente

```python
@ast_app.command("symbols")
def symbols(
    uri: str = typer.Argument(..., help="sym://python/mod|type/..."),
    segment: str = typer.Option(".", "--segment"),
    telemetry_level: str = typer.Option("off", "--telemetry"),
    persist_cache: bool = typer.Option(True, "--persist-cache/--no-persist-cache", help="Persist cache to disk"),
):
    """Return symbols from Python modules using AST parsing (M1)."""
    root = Path(segment).resolve()
    telemetry = _get_telemetry(telemetry_level)

    try:
        # 1. Parse URI
        match SymbolQuery.parse(uri):
            case Err(e):
                _json_output({"status": "error", "error_code": e.code, "message": e.message})
                raise typer.Exit(1)
            case Ok(query):
                pass

        # 2. Resolve file_path (lean, fail-closed)
        path_as_dir = query.path.replace(".", "/")
        candidate_file = root / f"{path_as_dir}.py"
        candidate_init = root / path_as_dir / "__init__.py"

        if candidate_file.exists() and candidate_file.is_file():
            file_path = candidate_file
        elif candidate_init.exists() and candidate_init.is_file():
            file_path = candidate_init
        else:
            _json_output(
                {
                    "status": "error",
                    "error_code": "FILE_NOT_FOUND",
                    "message": f"Could not find module for {query.path}",
                }
            )
            raise typer.Exit(1)

        # 3. Invoke SkeletonMapBuilder (M1 REAL)
        t0 = time.perf_counter_ns()
        builder = SkeletonMapBuilder(use_global_cache=True, auto_save=persist_cache)
        symbols, cache_hit = builder.build(file_path)
        duration_ms = max(1, (time.perf_counter_ns() - t0) // 1_000_000)

        # 4. Return JSON (M1 Contract)
        output = {
            "status": "ok",
            "segment_root": str(root),
            "file_rel": str(file_path.relative_to(root)),
            "symbols": [{"kind": s.kind, "name": s.name, "line": s.start_line} for s in symbols],
            "cache_hit": cache_hit,
        }

        if telemetry:
            telemetry.event(
                "ast.symbols",
                {},
                {"status": "ok"},
                duration_ms,
                file=str(file_path.relative_to(root)),
                symbols_count=len(symbols),
                cache_hit=cache_hit,
            )
            telemetry.flush()

        _json_output(output)

    except typer.Exit:
        raise
    except Exception as e:
        _json_output({"status": "error", "error_code": "INTERNAL_ERROR", "message": str(e)})
        raise typer.Exit(1)
```

#### Paso 6: Agregar comando para limpiar cache

```python
@ast_app.command("clear-cache")
def clear_cache(
    persist: bool = typer.Option(True, "--persist/--no-persist", help="Also clear persistent cache"),
):
    """Clear AST cache."""
    from src.application.ast_parser import SkeletonMapBuilder
    
    SkeletonMapBuilder.clear_global_cache()
    
    if persist:
        # Eliminar archivo de cache persistente
        try:
            CACHE_FILE.unlink(missing_ok=True)
        except Exception:
            pass
    
    _json_output({
        "status": "ok",
        "message": "Cache cleared",
        "persistent_cleared": persist,
    })
```

**Pruebas**:
- Verificar que el cache se guarda en disco
- Verificar que el cache se carga al iniciar
- Verificar que el cache persiste entre ejecuciones
- Verificar que el comando `clear-cache` funciona correctamente

---

## Orden de Implementación

### Fase 1: Solución 2 (Corregir Telemetría de Cache) - ALTA

**Razón**: Es la base para las otras soluciones. Necesitamos que `build()` retorne `cache_hit` antes de poder implementar las otras soluciones.

**Pasos**:
1. Modificar `SkeletonMapBuilder.build()` para retornar `tuple[List[SymbolInfo], bool]`
2. Actualizar `PR2ContextSearcher._extract_skeleton()` para usar el valor de `cache_hit`
3. Actualizar `CLI AST` para usar el valor de `cache_hit`
4. Agregar pruebas unitarias para verificar que `build()` retorna el valor correcto
5. Verificar que las métricas de telemetría son correctas

**Archivos Modificados**:
- [`src/application/ast_parser.py`](src/application/ast_parser.py:1)
- [`src/application/pr2_context_searcher.py`](src/application/pr2_context_searcher.py:1)
- [`src/infrastructure/cli_ast.py`](src/infrastructure/cli_ast.py:1)

---

### Fase 2: Solución 1 (Compartir Cache Entre Componentes) - ALTA

**Razón**: Una vez que la telemetría es correcta, podemos compartir el cache entre componentes para reducir parseos redundantes.

**Pasos**:
1. Agregar cache global `_global_cache` al módulo `ast_parser.py`
2. Agregar lock `_global_cache_lock` para thread-safety
3. Modificar constructor de `SkeletonMapBuilder` para aceptar `use_global_cache`
4. Hacer thread-safe el acceso al cache en `build()`
5. Actualizar todos los componentes para usar `use_global_cache=True`
6. Agregar métodos `clear_global_cache()` y `get_global_cache_stats()`
7. Agregar pruebas unitarias para verificar que el cache se comparte
8. Verificar que el cache es thread-safe

**Archivos Modificados**:
- [`src/application/ast_parser.py`](src/application/ast_parser.py:1)
- [`src/application/pr2_context_searcher.py`](src/application/pr2_context_searcher.py:1)
- [`src/application/telemetry_pr2.py`](src/application/telemetry_pr2.py:1)
- [`src/infrastructure/cli_ast.py`](src/infrastructure/cli_ast.py:1)

---

### Fase 3: Solución 3 (Persistir Cache Entre Ejecuciones de CLI) - MEDIA

**Razón**: Una vez que el cache se comparte entre componentes, podemos persistirlo en disco para que se mantenga entre ejecuciones del CLI.

**Pasos**:
1. Agregar funciones `_load_persistent_cache()` y `_save_persistent_cache()`
2. Cargar cache persistente al inicio del módulo
3. Modificar constructor de `SkeletonMapBuilder` para aceptar `auto_save`
4. Modificar `build()` para guardar cache automáticamente
5. Agregar método `save_cache()` para guardar manualmente
6. Actualizar `CLI AST` para usar `auto_save=True`
7. Agregar comando `ast clear-cache`
8. Agregar pruebas unitarias para verificar persistencia de cache
9. Verificar que el cache persiste entre ejecuciones

**Archivos Modificados**:
- [`src/application/ast_parser.py`](src/application/ast_parser.py:1)
- [`src/infrastructure/cli_ast.py`](src/infrastructure/cli_ast.py:1)

---

## Pruebas

### Pruebas Unitarias

1. **Prueba de retorno de cache_hit**:
   ```python
   def test_build_returns_cache_hit():
       builder = SkeletonMapBuilder()
       file_path = Path("test.py")
       content = "def test(): pass"
       
       # Primer parseo (cache miss)
       symbols1, cache_hit1 = builder.build(file_path, content)
       assert cache_hit1 is False
       
       # Segundo parseo (cache hit)
       symbols2, cache_hit2 = builder.build(file_path, content)
       assert cache_hit2 is True
       assert symbols1 == symbols2
   ```

2. **Prueba de cache global compartido**:
   ```python
   def test_global_cache_shared():
       builder1 = SkeletonMapBuilder(use_global_cache=True)
       builder2 = SkeletonMapBuilder(use_global_cache=True)
       file_path = Path("test.py")
       content = "def test(): pass"
       
       # Primer parseo con builder1 (cache miss)
       symbols1, cache_hit1 = builder1.build(file_path, content)
       assert cache_hit1 is False
       
       # Segundo parseo con builder2 (cache hit)
       symbols2, cache_hit2 = builder2.build(file_path, content)
       assert cache_hit2 is True
       assert symbols1 == symbols2
   ```

3. **Prueba de persistencia de cache**:
   ```python
   def test_cache_persistence():
       file_path = Path("test.py")
       content = "def test(): pass"
       
       # Primera ejecución
       builder1 = SkeletonMapBuilder(use_global_cache=True, auto_save=True)
       symbols1, cache_hit1 = builder1.build(file_path, content)
       assert cache_hit1 is False
       
       # Simular nueva ejecución (nuevo builder)
       builder2 = SkeletonMapBuilder(use_global_cache=True, auto_save=True)
       symbols2, cache_hit2 = builder2.build(file_path, content)
       assert cache_hit2 is True
       assert symbols1 == symbols2
   ```

### Pruebas de Integración

1. **Prueba de telemetría correcta**:
   - Ejecutar `ast symbols` múltiples veces
   - Verificar que las métricas de telemetría son correctas
   - Verificar que `ast_cache_hit_count` y `ast_cache_miss_count` son correctos

2. **Prueba de cache compartido**:
   - Ejecutar `ctx search` y `ast symbols` en el mismo archivo
   - Verificar que el cache se comparte entre comandos
   - Verificar que el número de parseos se reduce

3. **Prueba de persistencia de cache**:
   - Ejecutar `ast symbols` en un archivo
   - Terminar el proceso
   - Ejecutar `ast symbols` nuevamente en el mismo archivo
   - Verificar que es un cache hit

---

## Validación

### Métricas a Verificar

1. **Métricas de Telemetría**:
   - `ast_parse_count`: Total de parseos
   - `ast_cache_hit_count`: Total de cache hits
   - `ast_cache_miss_count`: Total de cache misses
   - Tasa de cache hits: `ast_cache_hit_count / ast_parse_count`

2. **Métricas de Rendimiento**:
   - Tiempo de respuesta de `ast symbols`
   - Tiempo de respuesta de `ctx search`
   - Reducción de parseos redundantes

3. **Métricas de Cache**:
   - Número de entradas en el cache
   - Tamaño total del cache
   - Tasa de cache hits por archivo

### Criterios de Éxito

1. **Telemetría Correcta**:
   - `ast_cache_hit_count` > 0
   - `ast_cache_miss_count` > 0
   - Tasa de cache hits > 0%

2. **Cache Compartido**:
   - Reducción de parseos redundantes > 50%
   - Tasa de cache hits > 30%

3. **Persistencia de Cache**:
   - Cache persiste entre ejecuciones
   - Tasa de cache hits en segunda ejecución > 80%

---

## Riesgos y Mitigaciones

### Riesgo 1: Thread-Safety

**Descripción**: El cache global compartido puede causar condiciones de carrera si no se implementa correctamente.

**Mitigación**:
- Usar `threading.Lock()` para proteger el acceso al cache
- Hacer todas las operaciones de cache thread-safe
- Agregar pruebas de concurrencia

### Riesgo 2: Persistencia de Cache Corrupto

**Descripción**: El cache persistente puede corromperse si hay errores al guardar/cargar.

**Mitigación**:
- Agregar versión del formato de cache
- Validar el cache al cargar
- Silenciosamente fallar si el cache está corrupto

### Riesgo 3: Aumento de Uso de Memoria

**Descripción**: El cache global puede aumentar el uso de memoria significativamente.

**Mitigación**:
- Agregar límite de tamaño del cache
- Implementar LRU (Least Recently Used) para evictar entradas antiguas
- Agregar comando para limpiar el cache

### Riesgo 4: Cambios en Archivos No Detectados

**Descripción**: Si un archivo cambia pero el contenido hash es el mismo, el cache no se invalidará.

**Mitigación**:
- Usar SHA256 del contenido como clave de cache
- Agregar timestamp del archivo como parte de la clave
- Implementar invalidación basada en timestamp

---

## Documentación

### Documentación a Actualizar

1. **README.md**:
   - Agregar sección sobre cache de AST
   - Documentar comandos `ast clear-cache`
   - Documentar opciones `--persist-cache` y `--no-persist-cache`

2. **docs/CLI_WORKFLOW.md**:
   - Agregar sección sobre cache de AST
   - Documentar cómo funciona el cache
   - Documentar cómo limpiar el cache

3. **docs/contracts/AST_SYMBOLS_M1.md**:
   - Actualizar contrato para incluir `cache_hit` en el output
   - Documentar el comportamiento del cache

### Documentación a Crear

1. **docs/ast_cache_architecture.md**:
   - Arquitectura del cache de AST
   - Diseño del cache global
   - Diseño de la persistencia de cache

2. **docs/ast_cache_telemetry.md**:
   - Métricas de telemetría del cache
   - Cómo interpretar las métricas
   - Cómo diagnosticar problemas de cache

---

## Timeline Estimado

| Fase | Duración | Estado |
|------|----------|--------|
| Fase 1: Corregir Telemetría de Cache | 2-3 horas | Pendiente |
| Fase 2: Compartir Cache Entre Componentes | 3-4 horas | Pendiente |
| Fase 3: Persistir Cache Entre Ejecuciones | 2-3 horas | Pendiente |
| Pruebas Unitarias | 2-3 horas | Pendiente |
| Pruebas de Integración | 2-3 horas | Pendiente |
| Documentación | 1-2 horas | Pendiente |
| **Total** | **12-18 horas** | **Pendiente** |

---

## Próximos Pasos

1. **Revisar y aprobar este plan**
2. **Implementar Fase 1**: Corregir Telemetría de Cache
3. **Implementar Fase 2**: Compartir Cache Entre Componentes
4. **Implementar Fase 3**: Persistir Cache Entre Ejecuciones
5. **Ejecutar pruebas unitarias y de integración**
6. **Actualizar documentación**
7. **Validar métricas y rendimiento**

---

**Generado**: 2026-01-05 04:50 UTC  
**Estado**: Planificación
