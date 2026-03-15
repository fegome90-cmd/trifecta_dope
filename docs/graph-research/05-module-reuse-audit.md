# Auditoría Quirúrgica - Módulos para Graph

Fecha: 2026-03-13
Objetivo: Evaluar reutilización directa de 4 módulos para Trifecta Graph

---

## A. Resumen Ejecutivo

| Módulo | Veredicto | Razón |
|--------|-----------|-------|
| `ast_models.py` | ✅ Reutilizable sin cambios | Tipos pydantic básicos, genéricos |
| `symbol_selector.py` | ⚠️ Reutilizable con adaptación | Acoplado a resolución de archivos, no a relaciones |
| `context_models.py` | ❌ No reutilizable | Paradigma diferente, whole-file chunks |
| `cli_ast.py` | ✅ Reutilizable sin cambios | Patrón Typer複製, contratos JSON |

---

## B. ast_models.py

### Responsabilidad Real

Definir tipos Pydantic para salida de parser AST.

### Tipos/Modelos Clave

```python
class Range(BaseModel):
    start_line: int
    end_line: int

class ChildSymbol(BaseModel):
    name: str
    kind: str          # "function", "class"
    range: Range
    signature_stub: Optional[str]

class ASTData(BaseModel):
    uri: str
    range: Optional[Range]
    content: Optional[str]
    children: List[ChildSymbol]

class ASTResponse(BaseModel):
    status: str
    kind: str          # "skeleton" | "snippet"
    data: Optional[ASTData]
    refs: List[ASTRef]
    errors: List[ASTError]
    next_actions: List[str]

class ASTErrorCode:
    INTERNAL_ERROR = "INTERNAL_ERROR"
    AMBIGUOUS_SYMBOL = "AMBIGUOUS_SYMBOL"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    SYMBOL_NOT_FOUND = "SYMBOL_NOT_FOUND"
    INVALID_URI = "INVALID_URI"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
```

### Evaluación para Graph

| Aspecto | Evaluación |
|---------|-----------|
| Semantic IR | ✅ Aporta `Range`, `ChildSymbol` - base para nodos |
| Graph nodes | ⚠️ Solo nombre/kind, sin relaciones |
| Symbol resolution | ❌ No tiene lógica de resolución |
| CLI namespace | ❌ No aplicable |

### Veredicto

**✅ REUTILIZABLE SIN CAMBIOS**

- `Range` es genérico y útil
- `ChildSymbol` es buen punto de partida para nodos
- `ASTErrorCode` es útil para contratos de error

---

## C. symbol_selector.py

### Responsabilidad Real

Resolver URIs `sym://python/{kind}/{path}` a archivos concretos y parsear símbolos.

### Tipos/Modelos Clave

```python
@dataclass
class SymbolResolveResult:
    resolved: bool
    ambiguous: bool
    file: Optional[str]
    start_line: Optional[int]
    end_line: Optional[int]
    matches: int
    candidates: List[Any]

class SymbolQuery:
    kind: str          # "mod" | "type"
    path: str
    member: Optional[str]

    @classmethod
    def parse(cls, uri: str) -> Result[SymbolQuery, ASTError]

@dataclass
class Candidate:
    file_rel: str
    kind: str
    start_line: Optional[int]
    end_line: Optional[int]

class SymbolResolver:
    def resolve(self, query: SymbolQuery) -> Result[Candidate, ASTError]
```

### Evaluación para Graph

| Aspecto | Evaluación |
|---------|-----------|
| Semantic IR | ⚠️ Solo resolución de archivo, no relaciones |
| Graph nodes | ❌ No genera nodos/edges |
| Symbol resolution | ⚠️ Solo exacta a archivo, no callers/callees |
| CLI namespace | ❌ No aplicable |

### Problema

El `SymbolResolver.resolve()` solo busca archivos exactos:

- No sigue imports
- No resolve symbol a línea específica
- No genera relaciones (callers/callees)

### Veredicto

**⚠️ REUTILIZABLE CON ADAPTACIÓN**

- `SymbolQuery.parse()` es útil como parser de URIs
- `SymbolResolveResult` es buen shape para resultados
- NO reusable: la lógica de resolución es muy limitada (solo exact file match)

---

## D. context_models.py

### Responsabilidad Real

Modelos Pydantic para Context Pack (chunks de documentación).

### Tipos/Modelos Clave

```python
class ContextChunk(BaseModel):
    id: str                    # "doc:sha1(content)[:10]" - EFÍMERO
    doc: str                   # "skill", "agent", "prime", "repo:path"
    title_path: List[str]
    text: str                  # Contenido completo
    char_count: int
    token_est: int
    source_path: str           # Relative path
    chunking_method: str       # "whole_file"

class ContextIndexEntry(BaseModel):
    id: str
    title_path_norm: str
    preview: str               # Primeros 200 chars
    token_est: int

class SourceFile(BaseModel):
    path: str
    sha256: str
    mtime: float
    chars: int

class ContextPack(BaseModel):
    schema_version: int = 1
    segment: str
    created_at: str
    digest: str = ""            # VACÍO en código
    source_files: List[SourceFile]
    chunks: List[ContextChunk]
    index: List[ContextIndexEntry]

class SearchResult(BaseModel):
    hits: List[SearchHit]

class GetResult(BaseModel):
    chunks: List[ContextChunk]
    total_tokens: int
    stop_reason: str            # "complete", "budget", "max_chunks"
    chunks_requested: int
    chunks_returned: int
    chars_returned_total: int
```

### Evaluación para Graph

| Aspecto | Evaluación |
|---------|-----------|
| Semantic IR | ❌ No hay nodos/relaciones - es texto plano |
| Graph nodes | ❌ Chunks son archivos completos, no símbolos |
| Symbol resolution | ❌ No aplica |
| CLI namespace | ❌ No aplicable |
| Linking con Pack | ❌ Chunk IDs son efímeros, no hay line ranges |

### Problema Fundamental

- **Whole-file chunks**: No hay segmentación por símbolos
- **Chunk IDs efímeros**: `sha1(content)` cambia con cualquier edición
- **No hay ranges**: No se puede mapear símbolo a línea específica

### Veredicto

**❌ NO REUTILIZABLE**

- Paradigma diferente (texto vs estructura)
- Acoplado a contexto de documentación
- Peligroso: podría temptar a usar chunks como "nodos" del grafo

---

## E. cli_ast.py

### Responsabilidad Real

CLI commands para AST parsing usando Typer.

### Patrones Clave

```python
# Sub-app Typer
ast_app = typer.Typer(help="AST & Parsing Commands")

# Función helper para output JSON
def _json_output(data: dict):
    typer.echo(json.dumps(data, indent=2))

# Helper para telemetry
def _get_telemetry(level: str = "lite") -> Optional[Telemetry]:
    if level == "off":
        return None
    return Telemetry(Path.cwd(), level=level)

# Comando con options
@ast_app.command("symbols")
def symbols(
    uri: str = typer.Argument(..., help="sym://python/mod|type/..."),
    segment: str = typer.Option(".", "--segment"),
    telemetry_level: str = typer.Option("off", "--telemetry"),
    persist_cache: bool = typer.Option(False, "--persist-cache"),
):
    # ... implementación

# Error handling con Exit
if error:
    _json_output({"status": "error", "error_code": "CODE", "message": "..."})
    raise typer.Exit(1)

# JSON output pattern
output = {
    "status": "ok",
    "segment_root": str(root),
    "file_rel": str(file_path.relative_to(root)),
    "symbols": [...],
    "cache_status": ...,
}
_json_output(output)
```

### Contratos JSON (útiles para Graph)

```json
// symbols output
{
  "status": "ok",
  "segment_root": "/path/to/segment",
  "file_rel": "src/module.py",
  "symbols": [
    {"kind": "class", "name": "MyClass", "line": 10}
  ],
  "cache_status": "hit|miss|error",
  "cache_key": "segment:rel/path:hash:1",
  "miss_reason": "cold_cache|key_miss|ephemeral_cache"
}

// error output
{
  "status": "error",
  "error_code": "FILE_NOT_FOUND",
  "message": "Could not find module for..."
}
```

### Evaluación para Graph

| Aspecto | Evaluación |
|---------|-----------|
| Semantic IR | ❌ No aplicable |
| Graph nodes | ❌ No aplicable |
| Symbol resolution | ❌ No aplicable |
| CLI namespace | ✅ Patrón exacto para replicar |

### Veredicto

**✅ REUTILIZABLE SIN CAMBIOS**

- Patrón Typer sub-app copiar directamente
- `_json_output()` helper es útil
- Contratos JSON son modelos a seguir
- Mismo nivel de telemetría y error handling

---

## F. Reutilización Recomendada

### Lo que SÍ Usar

| Módulo | Qué usar | Cómo |
|--------|---------|------|
| `ast_models.py` | `Range`, `ChildSymbol`, `ASTErrorCode` | Directamente como tipos base |
| `cli_ast.py` | Patrón Typer sub-app | Copiar estructura |
| `cli_ast.py` | `_json_output()` helper | Reutilizar |
| `cli_ast.py` | Contratos JSON | Mantener mismo formato |

### Lo que ADAPTAR

| Módulo | Qué adaptar | Cómo |
|--------|-------------|------|
| `symbol_selector.py` | `SymbolQuery.parse()` | Usar para parsing de URIs |
| `symbol_selector.py` | `SymbolResolveResult` | Extender para relaciones |

### Lo que NO Usar

| Módulo | Por qué |
|--------|---------|
| `context_models.py` | Paradigma incompatible |
| `symbol_selector.py` (lógica) | Solo exact file match, no relaciones |

---

## G. Qué NO Copiar desde Estos Módulos

### Errores a Evitar

1. **No usar `ContextChunk` como nodos de grafo**
   - Son whole-file, no symbol-level
   - IDs son efímeros

2. **No asumir que `ChildSymbol` tiene relaciones**
   - Solo tiene: name, kind, range, signature_stub
   - No tiene: callers, callees, imports

3. **No copiar la lógica de `SymbolResolver.resolve()`**
   - Solo hace exact file match
   - No es suficiente para graph relations

4. **No esperar que `context_pack.json` tenga symbol mapping**
   - No existe link símbolo→chunk

---

## H. Orden Exacto de Aprovechamiento

### Prioridad 1: CLI Template

1. Copiar `cli_ast.py` estructura completa
2. Renombrar `ast_app` → `graph_app`
3. Cambiar comandos de symbols → graph operations

### Prioridad 2: Tipos Base

1. Importar `Range`, `ChildSymbol` de ast_models
2. Extender con nuevos tipos para relations

### Prioridad 3: URI Parsing

1. Adaptar `SymbolQuery.parse()` para graph URIs
2. Nuevo formato: `graph://python/{operation}/{query}`

### Prioridad 4: NO USAR

- context_models.py para nada relacionado con Graph
- symbol_selector.py lógica de resolución

---

## I. Resumen Visual

```
┌─────────────────────────────────────────────────────────────┐
│                     REUTILIZABLE                            │
├─────────────────────────────────────────────────────────────┤
│ ast_models.py                                               │
│   ✅ Range (líneas)                                        │
│   ✅ ChildSymbol (nombre, kind, range)                      │
│   ✅ ASTErrorCode                                          │
├─────────────────────────────────────────────────────────────┤
│ cli_ast.py                                                  │
│   ✅ Patrón Typer sub-app                                   │
│   ✅ _json_output() helper                                  │
│   ✅ Contratos JSON                                          │
│   ✅ Error handling pattern                                  │
├─────────────────────────────────────────────────────────────┤
│ symbol_selector.py (adaptar)                               │
│   ⚠️ SymbolQuery.parse() → URI parsing                      │
│   ⚠️ SymbolResolveResult → result shape                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   NO REUTILIZABLE                            │
├─────────────────────────────────────────────────────────────┤
│ context_models.py                                           │
│   ❌ Whole-file chunks no son símbolos                      │
│   ❌ Chunk IDs efímeros                                     │
│   ❌ No hay line ranges                                     │
├─────────────────────────────────────────────────────────────┤
│ symbol_selector.py (lógica)                                │
│   ❌ Solo exact file match                                  │
│   ❌ No resolution de relaciones                            │
└─────────────────────────────────────────────────────────────┘
```
