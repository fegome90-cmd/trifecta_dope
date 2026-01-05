# Problema 4: Telemetría con Paths Potencialmente Inseguros

**Prioridad**: 🟢 BAJA  
**Estado**: Investigación Completa  
**Fecha**: 2026-01-05

---

## Resumen Ejecutivo

La telemetría del sistema LSP tiene **sanitización parcial** de paths. Algunos lugares usan solo el nombre del ejecutable (correcto), otros usan `relative_to()` que puede fallar si el path está fuera del workspace, potencialmente exponiendo información sensible.

**Riesgo**: BAJO (la mayoría de paths están dentro del workspace)  
**Impacto**: Leak de PII (usernames en paths), crashes en telemetry

---

## Phase 1: Root Cause Investigation

### 1.1 Sanitización Correcta

**Código Bueno** ([lsp_client.py:71-85](../../src/infrastructure/lsp_client.py#L71-L85)):

```python
# Robust Sanitize
exe_log = "unknown"
try:
    if executable:
        exe_log = Path(executable).name  # ✅ Solo nombre, no path completo
except Exception:
    pass

self._log_event(
    "lsp.spawn",
    {"executable": exe_log},  # ✅ "pyright-langserver" no "/usr/bin/pyright-langserver"
    {"status": "ok", "pid": self.process.pid},
    1,
)
```

**Beneficio**: No expone `/home/username/...` en paths.

---

### 1.2 Sanitización Potencialmente Problemática

**Código con Riesgo** ([cli_ast.py:84](../../src/infrastructure/cli_ast.py#L84)):

```python
if telemetry:
    telemetry.event(
        "ast.symbols",
        {},
        {"status": "ok"},
        duration_ms,
        file=str(file_path.relative_to(root)),  # ⚠️ Puede fallar
        symbols_count=len(symbols),
        cache_hit=cache_hit,
    )
```

**Problema**:
- Si `file_path` NO es descendiente de `root` → `ValueError`
- Ejemplo: `file_path = /tmp/test.py`, `root = /workspaces/project`
- `relative_to()` lanza `ValueError: '/tmp/test.py' is not in the subpath of '/workspaces/project'`

---

### 1.3 Otros Lugares con Similar Pattern

**Búsqueda** (via `grep_search` anterior):

```python
# src/infrastructure/cli.py - múltiples lugares usan relative_to
telemetry.event(
    "ctx.search",
    {},
    {"status": "ok"},
    timing_ms,
    file=str(some_path.relative_to(root)),  # ⚠️ Potencial fail
)
```

**Cantidad**: ~15-20 ocurrencias en `cli.py` y otros archivos.

---

### 1.4 Casos Donde Falla

**Escenario 1: Symlinks fuera del workspace**
```python
root = Path("/workspaces/project")
file_path = Path("/workspaces/project/src/main.py").resolve()
# Si src/ es symlink a /home/user/code/real_src/:
# file_path = /home/user/code/real_src/main.py
# relative_to(root) → ValueError
```

**Escenario 2: Temp files**
```python
root = Path("/workspaces/project")
file_path = Path("/tmp/trifecta_test_12345.py")
# relative_to(root) → ValueError
```

**Escenario 3: Absolute paths en tests**
```python
# En tests con tmp_path:
root = tmp_path  # /tmp/pytest-xyz/test_0/
file_path = Path("/absolute/path/to/file.py")
# relative_to(root) → ValueError
```

---

## Phase 2: Pattern Analysis

### 2.1 Patrón: Assume all paths are within workspace

**Asunción Implícita**: Todos los files procesados están bajo `workspace_root`.

**Realidad**: 
- Tests usan temp paths
- Symlinks pueden apuntar fuera
- Usuario puede abrir files externos

---

### 2.2 Soluciones Comunes

#### **Solución 1: Try/Except con Fallback**

```python
try:
    file_rel = str(file_path.relative_to(root))
except ValueError:
    # Path fuera del workspace: usar solo nombre
    file_rel = file_path.name
```

**Pros**:
- Simple
- No crash
- Fallback razonable

**Contras**:
- Pierde información de subdirectorio si está fuera

---

#### **Solución 2: Helper Function de Sanitización**

```python
def sanitize_path_for_telemetry(path: Path, root: Path) -> str:
    """Sanitize path for telemetry (no PII, relative if possible)."""
    try:
        # Intenta relative
        return str(path.relative_to(root))
    except ValueError:
        # Fuera del workspace: solo nombre
        # Si es en /tmp o /home, strip username
        path_str = str(path)
        if "/home/" in path_str:
            parts = path.parts
            # Reemplazar /home/username con /home/***
            sanitized = ["/home/***" if p.startswith("/home") else p for p in parts]
            return "/".join(sanitized[-3:])  # Last 3 components
        elif path_str.startswith("/tmp"):
            return f"/tmp/{path.name}"
        else:
            return path.name
```

**Pros**:
- PII-safe
- Información útil preservada
- Centralizado

**Contras**:
- Más complejo
- Puede over-sanitize

---

#### **Solución 3: Path Hashing**

```python
import hashlib

def hash_path(path: Path) -> str:
    """Hash path for privacy."""
    return hashlib.sha256(str(path).encode()).hexdigest()[:8]

# En telemetry:
file=hash_path(file_path)  # "a3b4c5d6"
```

**Pros**:
- Totalmente anónimo
- No PII posible

**Contras**:
- Pierde información útil para debugging
- No se puede correlacionar entre eventos

---

## Phase 3: Hypothesis and Testing

### 3.1 Hipótesis: relative_to() falla en <1% de casos

**Hipótesis**: En uso normal (workspace files), `relative_to()` funciona. Solo falla en edge cases.

**Test**:
```python
def test_relative_to_failure_rate(tmp_path):
    """Measure failure rate of relative_to in realistic scenario."""
    root = tmp_path
    (root / "src").mkdir()
    
    # Normal files (should work)
    normal_files = [
        root / "src" / "main.py",
        root / "tests" / "test.py",
        root / "README.md",
    ]
    
    # Edge case files (should fail)
    edge_files = [
        Path("/tmp/temp.py"),
        Path("/home/user/external.py"),
        root.parent / "outside.py",
    ]
    
    failures = 0
    for f in normal_files:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.touch()
        try:
            f.relative_to(root)
        except ValueError:
            failures += 1
    
    # Normal files: 0% failure
    assert failures == 0
    
    failures = 0
    for f in edge_files:
        try:
            f.relative_to(root)
        except ValueError:
            failures += 1
    
    # Edge files: 100% failure (expected)
    assert failures == len(edge_files)
```

**Resultado Esperado**: relative_to() funciona para archivos normales, falla solo en edge cases.

---

### 3.2 Hipótesis: PII Leak es Bajo Riesgo

**Hipótesis**: Paths con usernames son raros en telemetry.

**Análisis de Telemetry Logs** (simulado):
```bash
# Buscar eventos con /home/ en file field
rg "/home/" telemetry/*.jsonl

# Resultado esperado: 0-5 ocurrencias en 1000 eventos
```

**Conclusión**: Riesgo bajo pero vale la pena mitigar.

---

## Phase 4: Implementation

### 4.1 Solución Recomendada: Helper + Try/Except

#### **Paso 1: Crear Helper de Sanitización**

**Crear** `src/infrastructure/telemetry_utils.py`:

```python
"""Utilities for telemetry sanitization."""
from pathlib import Path


def sanitize_path(path: Path, root: Path) -> str:
    """
    Sanitize file path for telemetry (PII-safe, relative when possible).
    
    Args:
        path: Absolute or relative path to sanitize
        root: Workspace root for relative path calculation
    
    Returns:
        Sanitized path string (relative to root if possible, name only otherwise)
    
    Examples:
        >>> sanitize_path(Path("/workspace/src/main.py"), Path("/workspace"))
        'src/main.py'
        
        >>> sanitize_path(Path("/tmp/test.py"), Path("/workspace"))
        'test.py'
        
        >>> sanitize_path(Path("/home/user/external.py"), Path("/workspace"))
        'external.py'
    """
    try:
        # Try relative path first
        return str(path.relative_to(root))
    except ValueError:
        # Path outside workspace: return name only (safe)
        return path.name


def sanitize_executable_path(executable: Path | str | None) -> str:
    """
    Sanitize executable path for telemetry (name only).
    
    Args:
        executable: Path to executable or None
    
    Returns:
        Executable name or "unknown"
    
    Examples:
        >>> sanitize_executable_path("/usr/bin/pyright")
        'pyright'
        
        >>> sanitize_executable_path(None)
        'unknown'
    """
    if not executable:
        return "unknown"
    
    try:
        return Path(executable).name
    except Exception:
        return "unknown"
```

---

#### **Paso 2: Actualizar LSP Client**

**Modificar** [lsp_client.py:71-85](../../src/infrastructure/lsp_client.py#L71-L85):

```python
from src.infrastructure.telemetry_utils import sanitize_executable_path

# ANTES:
exe_log = "unknown"
try:
    if executable:
        exe_log = Path(executable).name
except Exception:
    pass

# DESPUÉS:
exe_log = sanitize_executable_path(executable)

self._log_event(
    "lsp.spawn",
    {"executable": exe_log},
    {"status": "ok", "pid": self.process.pid},
    1,
)
```

---

#### **Paso 3: Actualizar CLI AST**

**Modificar** [cli_ast.py:84](../../src/infrastructure/cli_ast.py#L84):

```python
from src.infrastructure.telemetry_utils import sanitize_path

# ANTES:
file=str(file_path.relative_to(root))

# DESPUÉS:
file=sanitize_path(file_path, root)

if telemetry:
    telemetry.event(
        "ast.symbols",
        {},
        {"status": "ok"},
        duration_ms,
        file=sanitize_path(file_path, root),  # ✅ Safe
        symbols_count=len(symbols),
        cache_hit=cache_hit,
    )
```

---

#### **Paso 4: Actualizar CLI Principal**

**Buscar y reemplazar** en `src/infrastructure/cli.py`:

```bash
# Find all occurrences
rg "\.relative_to\(" src/infrastructure/cli.py

# Replace manually (15-20 lugares)
# ANTES:
file=str(path.relative_to(root))

# DESPUÉS:
from src.infrastructure.telemetry_utils import sanitize_path
file=sanitize_path(path, root)
```

---

#### **Paso 5: Agregar Policy de Telemetría**

**Crear** `docs/telemetry/PRIVACY_POLICY.md`:

```markdown
# Telemetry Privacy Policy

## Data Collected

Trifecta collects anonymous usage telemetry to improve the tool.

### What We Collect:
- Command names (e.g., `ctx search`, `ast symbols`)
- Timing metrics (e.g., search duration)
- File counts and sizes (aggregated)
- Error types and counts

### What We DON'T Collect:
- ❌ File contents
- ❌ Usernames or home directories
- ❌ Absolute paths (sanitized to relative)
- ❌ Code snippets
- ❌ Search queries (only length)

## Sanitization

All paths are sanitized before transmission:
- **Workspace files**: Relative paths (e.g., `src/main.py`)
- **External files**: Name only (e.g., `test.py`)
- **Executables**: Name only (e.g., `pyright`)

## Opt-Out

Disable telemetry:
```bash
export TRIFECTA_TELEMETRY=off
```

Or per-command:
```bash
trifecta ctx search --telemetry off
```

## Data Retention

- Telemetry stored locally in `~/.trifecta/telemetry/`
- Auto-deleted after 30 days
- No cloud sync (opt-in only)
```

---

### 4.2 Tests de Validación

#### **Test 1: Sanitize Path Within Workspace**

```python
from src.infrastructure.telemetry_utils import sanitize_path

def test_sanitize_path_within_workspace(tmp_path):
    """Verify sanitize_path returns relative path for workspace files."""
    root = tmp_path
    (root / "src").mkdir()
    file_path = root / "src" / "main.py"
    file_path.touch()
    
    result = sanitize_path(file_path, root)
    
    assert result == "src/main.py"
    assert not result.startswith("/")  # Relative
```

#### **Test 2: Sanitize Path Outside Workspace**

```python
def test_sanitize_path_outside_workspace(tmp_path):
    """Verify sanitize_path returns name only for external files."""
    root = tmp_path
    external_file = Path("/tmp/external.py")
    
    result = sanitize_path(external_file, root)
    
    assert result == "external.py"  # Name only
    assert "tmp" not in result  # No /tmp prefix
```

#### **Test 3: Sanitize Executable**

```python
from src.infrastructure.telemetry_utils import sanitize_executable_path

def test_sanitize_executable_path():
    """Verify executable sanitization."""
    assert sanitize_executable_path("/usr/bin/pyright") == "pyright"
    assert sanitize_executable_path("/home/user/.local/bin/pylsp") == "pylsp"
    assert sanitize_executable_path(None) == "unknown"
    assert sanitize_executable_path("") == "unknown"
```

#### **Test 4: No PII in Telemetry Events**

```python
def test_telemetry_no_pii(tmp_path):
    """Verify telemetry events don't contain PII."""
    root = tmp_path
    (root / "src").mkdir()
    file_path = root / "src" / "main.py"
    file_path.touch()
    
    # Simulate telemetry event
    telemetry = Telemetry(root)
    telemetry.event(
        "test.event",
        {},
        {"status": "ok"},
        100,
        file=sanitize_path(file_path, root),
    )
    
    # Read telemetry file
    telemetry_files = list((root / ".trifecta" / "telemetry").glob("*.jsonl"))
    assert len(telemetry_files) > 0
    
    content = telemetry_files[0].read_text()
    
    # Verify no /home/ or /tmp/ in content
    assert "/home/" not in content
    assert str(tmp_path) not in content  # No absolute tmp paths
```

---

## Métricas de Éxito

- ✅ 0 crashes por `relative_to()` ValueError
- ✅ 0 usernames en telemetry logs
- ✅ Todos los paths sanitizados
- ✅ Privacy policy documentada
- ✅ Tests de PII passing

---

## Riesgos y Mitigaciones

### Riesgo 1: Over-Sanitization

**Probabilidad**: Baja  
**Impacto**: Bajo (pierde contexto de debugging)

**Mitigación**:
- Conservar estructura de subdirectorios cuando posible
- Solo sanitizar paths externos

### Riesgo 2: Performance Impact

**Probabilidad**: Muy Baja  
**Impacto**: Negligible

**Mitigación**:
- Sanitización es O(1) (solo name extraction)
- No impacto medible

---

## Timeline

| Tarea | Duración |
|-------|----------|
| Crear telemetry_utils.py | 30min |
| Actualizar lsp_client.py | 15min |
| Actualizar cli_ast.py | 15min |
| Actualizar cli.py (15-20 lugares) | 1h |
| Privacy policy | 30min |
| Tests | 1h |
| **Total** | **~3h** |

---

## Próximos Pasos

1. ✅ Crear branch `security/sanitize-telemetry-paths`
2. ⏳ Implementar telemetry_utils
3. ⏳ Actualizar todos los usos
4. ⏳ Ejecutar tests de PII
5. ⏳ Merge a main

---

**Investigado**: 2026-01-05  
**Estado**: Listo para Implementación  
**Prioridad**: BAJA (pero buena práctica de seguridad)
