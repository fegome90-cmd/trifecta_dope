# Problema 1: Duplicación de Lógica LSP Client

**Prioridad**: 🔴 ALTA  
**Estado**: Investigación Completa  
**Fecha**: 2026-01-05

---

## Resumen Ejecutivo

Existen **dos implementaciones paralelas** de clientes LSP en el codebase:
1. `LSPClient` en [lsp_client.py](../../src/infrastructure/lsp_client.py) - Usado por daemon
2. `LSPManager` en [lsp_manager.py](../../src/application/lsp_manager.py) - Usado por PR2ContextSearcher

**Impacto**: Duplicación de lógica, mantenimiento doble, confusión arquitectónica, riesgo de divergencia.

---

## Phase 1: Root Cause Investigation

### 1.1 Evidencia de Duplicación

#### **LSPClient** ([lsp_client.py:19](../../src/infrastructure/lsp_client.py#L19))

**Ubicación**: `src/infrastructure/lsp_client.py`

**Código Relevante**:
```python
class LSPState(Enum):
    COLD = "COLD"
    WARMING = "WARMING"
    READY = "READY"
    FAILED = "FAILED"
    CLOSED = "CLOSED"

class LSPClient:
    def __init__(self, root_path: Path, telemetry: Any = None):
        self.root_path = root_path
        self.telemetry = telemetry
        self.state = LSPState.COLD
        self.process: Optional[subprocess.Popen[bytes]] = None
        self.lock = threading.Lock()
        self._stop_lock = threading.Lock()
        self.stopping = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._capabilities: Dict[str, Any] = {}
        self._warmup_file: Optional[Path] = None

        # Request handling
        self._next_id = 1000
        self._pending_requests: Dict[int, Any] = {}
        self._request_events: Dict[int, threading.Event] = {}
```

**Características**:
- ✅ Thread-safe con múltiples locks
- ✅ Request/Response tracking con eventos
- ✅ Handshake automático + Read Loop
- ✅ Graceful shutdown con orden estricto
- ✅ Telemetría integrada

---

#### **LSPManager** ([lsp_manager.py:61](../../src/application/lsp_manager.py#L61))

**Ubicación**: `src/application/lsp_manager.py`

**Código Relevante**:
```python
class LSPState(Enum):  # ⚠️ Duplicado
    COLD = "cold"
    WARMING = "warming"
    READY = "ready"
    FAILED = "failed"

class LSPManager:
    def __init__(self, workspace_root: Path, enabled: bool = False) -> None:
        self.workspace_root = workspace_root
        self.enabled = enabled
        self.state = LSPState.COLD
        self._process: Optional[subprocess.Popen[str]] = None
        self._request_id = 0
        self._lock = threading.Lock()
        self._diagnostics_received: set[str] = set()
        self._stderr_thread: Optional[threading.Thread] = None

    def spawn_async(self, best_file_uri: Optional[str] = None) -> None:
        """Spawn Pyright LSP in background (non-blocking)."""
        if not self.enabled or self.state != LSPState.COLD:
            return

        def _spawn_task() -> None:
            try:
                self.state = LSPState.WARMING
                self._process = subprocess.Popen(
                    ["pyright", "--outputjson"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    cwd=str(self.workspace_root),
                )
                self._send_initialize()
                if best_file_uri:
                    self._send_did_open(best_file_uri)
            except Exception:
                self.state = LSPState.FAILED

        t = threading.Thread(target=_spawn_task, daemon=True)
        t.start()
```

**Características**:
- ✅ Spawn asíncrono con best_file_uri
- ✅ Thread-safe con lock
- ✅ Transición a READY basada en diagnostics
- ⚠️ Menos robusto que LSPClient (sin stop_lock, sin request tracking completo)

---

### 1.2 Comparación Detallada

| Característica | LSPClient | LSPManager | Diferencia |
|----------------|-----------|------------|------------|
| **Estados** | COLD/WARMING/READY/FAILED/CLOSED | COLD/WARMING/READY/FAILED | LSPClient tiene CLOSED |
| **Thread Safety** | 2 locks (_lock, _stop_lock) | 1 lock | LSPClient más robusto |
| **Request Tracking** | Dict + Events por request | ID sequence | LSPClient tiene tracking completo |
| **Shutdown** | Orden estricto + timeout escalado | Simple terminate | LSPClient previene race conditions |
| **Telemetría** | Integrada y sanitizada | No tiene | LSPClient observable |
| **Handshake** | Automático en _run_loop | Manual en _send_initialize | LSPClient automático |
| **Warming** | Via did_open en start() | Via best_file_uri en spawn_async | Ambos similares |
| **READY Trigger** | publishDiagnostics received | publishDiagnostics received | Similar |
| **Executable** | pylsp o pyright-langserver | pyright --outputjson | Diferente |
| **Process Type** | bytes (binary) | str (text) | LSPClient más correcto |

---

### 1.3 Uso Actual en el Codebase

#### **LSPClient usado por**:
- [lsp_daemon.py:35](../../src/infrastructure/lsp_daemon.py#L35):
```python
self.lsp_client = LSPClient(self.root, self.telemetry)
```

#### **LSPManager usado por**:

1. [pr2_context_searcher.py:70](../../src/application/pr2_context_searcher.py#L70):
```python
self.lsp_manager = LSPManager(workspace_root, enabled=lsp_enabled)
```

2. [telemetry_pr2.py:14](../../src/application/telemetry_pr2.py#L14):
```python
from src.application.lsp_manager import LSPState  # Solo el enum
```

3. [test_ast_lsp_pr2.py](../../tests/unit/test_ast_lsp_pr2.py): **6 tests**
```python
# Line 162
manager = LSPManager(Path("/workspace"), enabled=True)

# Line 167
manager = LSPManager(Path("/workspace"), enabled=False)

# Line 173, 179, 185, 191: Más instanciaciones en tests
```

**Total de Referencias**:
- `LSPClient`: **1 uso** (daemon)
- `LSPManager`: **2 usos** (PR2ContextSearcher, tests) + **1 import** (enum)

---

### 1.4 Análisis de Dependencias

```
┌─────────────────────────────────────┐
│   PR2ContextSearcher                │
│   (application layer)               │
└──────────┬──────────────────────────┘
           │ uses
           ▼
┌─────────────────────────────────────┐
│   LSPManager                        │
│   (application/lsp_manager.py)     │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│   LSPDaemonServer                   │
│   (infrastructure layer)            │
└──────────┬──────────────────────────┘
           │ uses
           ▼
┌─────────────────────────────────────┐
│   LSPClient                         │
│   (infrastructure/lsp_client.py)   │
└─────────────────────────────────────┘
```

**Problema Arquitectónico**:
- `LSPManager` está en `application/` pero hace trabajo de `infrastructure/`
- `LSPClient` está correctamente en `infrastructure/`
- Violación de Clean Architecture: application layer no debería gestionar procesos LSP

---

## Phase 2: Pattern Analysis

### 2.1 Patrón Encontrado: Feature Parity Drift

**Patrón**: Dos implementaciones empiezan similares pero divergen con el tiempo.

**Evidencia Histórica** (inferida):
1. Ambos manejan estado LSP (COLD → WARMING → READY)
2. Ambos spawnan subproceso pyright/pylsp
3. Ambos hacen handshake JSON-RPC
4. **PERO**: LSPClient evolucionó con fixes (shutdown race condition, telemetry)
5. **PERO**: LSPManager no recibió los mismos fixes

**Git History** (sugerido para investigar):
```bash
git log --oneline --all -- src/infrastructure/lsp_client.py src/application/lsp_manager.py
```

---

### 2.2 Análisis de Features Únicas

#### **LSPManager tiene que LSPClient no**:

1. **Spawn con best_file_uri**:
```python
def spawn_async(self, best_file_uri: Optional[str] = None) -> None:
    # ... spawn ...
    if best_file_uri:
        self._send_did_open(best_file_uri)
```

**Valor**: Permite warming inmediato de un archivo específico.

2. **READY basado en diagnostics received**:
```python
def mark_diagnostics_received(self, uri: str) -> None:
    with self._lock:
        self._diagnostics_received.add(uri)
        if self.state == LSPState.WARMING and self._diagnostics_received:
            self.state = LSPState.READY
```

**Valor**: Transición explícita cuando LSP está caliente.

#### **LSPClient tiene que LSPManager no**:

1. **Shutdown robusto con race condition prevention**
2. **Telemetría sanitizada**
3. **Request tracking con eventos**
4. **Stop lock para idempotencia**

---

## Phase 3: Hypothesis and Testing

### 3.1 Hipótesis: LSPManager es Legacy Code

**Hipótesis**: `LSPManager` fue la implementación original, `LSPClient` es el refactor mejorado.

**Evidencia que soporta**:
- ✅ LSPClient tiene más features de producción (telemetry, locks)
- ✅ LSPClient está en infrastructure/ (mejor arquitectura)
- ✅ LSPManager solo tiene 2 usos reales (PR2ContextSearcher, tests)
- ✅ Daemon usa LSPClient (más reciente)

**Test de Hipótesis**:
```bash
# Ver fechas de commits
git log --format="%ai %s" -- src/infrastructure/lsp_client.py | head -5
git log --format="%ai %s" -- src/application/lsp_manager.py | head -5
```

---

### 3.2 Hipótesis: Features de LSPManager son Necesarias

**Hipótesis**: `best_file_uri` y `mark_diagnostics_received` son críticos para PR2ContextSearcher.

**Test**: ¿Qué pasa si PR2ContextSearcher usa LSPClient sin esas features?

**Experimento**:
```python
# En pr2_context_searcher.py, cambiar:
# self.lsp_manager = LSPManager(workspace_root, enabled=lsp_enabled)

# Por:
self.lsp_client = LSPClient(workspace_root, telemetry=None)
if lsp_enabled:
    self.lsp_client.start()
    # Warming manual si es necesario
    if best_file:
        self.lsp_client.did_open(best_file, content)
```

**Resultado Esperado**: Funciona igual o mejor (porque LSPClient es más robusto).

---

## Phase 4: Implementation

### 4.1 Solución Propuesta: Migración Incremental

#### **Paso 1: Portar Features Únicas de LSPManager a LSPClient** (2h)

**Modificar** [lsp_client.py](../../src/infrastructure/lsp_client.py):

```python
class LSPClient:
    def __init__(self, root_path: Path, telemetry: Any = None):
        # ... existing code ...
        self._diagnostics_received: set[str] = set()  # ← Agregar

    def start(self, warm_up_file: Optional[Path] = None) -> None:
        """Start LSP server and optionally warm up with file."""
        with self.lock:
            if self.state != LSPState.COLD:
                return

            executable = shutil.which("pylsp") or shutil.which("pyright-langserver")
            if not executable:
                self._transition(LSPState.FAILED)
                return

            try:
                self._transition(LSPState.WARMING)
                cmd = [executable]
                if "pyright" in executable:
                    cmd.append("--stdio")

                self.process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=False,
                )

                # Start handshake + Read Loop
                self._thread = threading.Thread(target=self._run_loop, daemon=True)
                self._thread.start()

                # ← Warm up with file if provided
                if warm_up_file and warm_up_file.exists():
                    content = warm_up_file.read_text(errors="replace")
                    self.did_open(warm_up_file, content)

            except Exception as e:
                self._transition(LSPState.FAILED)

    def mark_diagnostics_received(self, uri: str) -> None:
        """Mark that diagnostics were received for URI."""
        with self.lock:
            self._diagnostics_received.add(uri)
            # Transition to READY if we have diagnostics
            if self.state == LSPState.WARMING and self._diagnostics_received:
                self._transition(LSPState.READY)
                if self.telemetry:
                    self.telemetry.incr("lsp_ready_count")
```

---

#### **Paso 2: Migrar PR2ContextSearcher a LSPClient** (1h)

**Modificar** [pr2_context_searcher.py:15,70](../../src/application/pr2_context_searcher.py):

```python
# ANTES:
from src.application.lsp_manager import LSPManager

# DESPUÉS:
from src.infrastructure.lsp_client import LSPClient

# ---

# ANTES:
self.lsp_manager = LSPManager(workspace_root, enabled=lsp_enabled)

# DESPUÉS:
self.lsp_client = LSPClient(workspace_root, telemetry=self.tel)
if lsp_enabled:
    # Determinar best file para warming (opcional)
    best_file = self._find_best_warm_up_file()
    self.lsp_client.start(warm_up_file=best_file)

def _find_best_warm_up_file(self) -> Optional[Path]:
    """Find best file to warm up LSP (e.g., main module)."""
    candidates = [
        self.root / "src" / "__init__.py",
        self.root / "main.py",
        self.root / "app.py",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None
```

**Actualizar todos los usos de** `self.lsp_manager` → `self.lsp_client`:
```bash
rg "self\.lsp_manager" src/application/pr2_context_searcher.py
# Reemplazar manualmente cada ocurrencia
```

---

#### **Paso 3: Actualizar telemetry_pr2.py** (5min)

**Modificar** [telemetry_pr2.py:14](../../src/application/telemetry_pr2.py):

```python
# ANTES:
from src.application.lsp_manager import LSPState

# DESPUÉS:
from src.infrastructure.lsp_client import LSPState
```

---

#### **Paso 4: Migrar Tests** (1h)

**Modificar** [test_ast_lsp_pr2.py](../../tests/unit/test_ast_lsp_pr2.py):

```python
# ANTES:
from src.application.lsp_manager import LSPManager, LSPState

# DESPUÉS:
from src.infrastructure.lsp_client import LSPClient as LSPManager, LSPState

# Nota: Alias LSPClient as LSPManager para minimizar cambios en tests
# O refactorizar todos los tests para usar LSPClient directamente

# Ejemplo:
def test_lsp_enabled():
    manager = LSPClient(Path("/workspace"), telemetry=None)  # ← Cambiar constructor
    manager.start()  # ← start() en lugar de spawn_async()
    assert manager.state == LSPState.WARMING
```

---

#### **Paso 5: Deprecar LSPManager** (15min)

**Modificar** [lsp_manager.py](../../src/application/lsp_manager.py):

```python
import warnings
from src.infrastructure.lsp_client import LSPClient as _LSPClient, LSPState

__all__ = ["LSPManager", "LSPState"]

class LSPManager(_LSPClient):
    """
    DEPRECATED: Use LSPClient from lsp_client.py instead.

    This class will be removed in v2.0.
    """

    def __init__(self, workspace_root, enabled: bool = False):
        warnings.warn(
            "LSPManager is deprecated and will be removed in v2.0. "
            "Use LSPClient from src.infrastructure.lsp_client instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(workspace_root, telemetry=None)
        if enabled:
            self.start()

    def spawn_async(self, best_file_uri: Optional[str] = None) -> None:
        """DEPRECATED: Use start(warm_up_file=...) instead."""
        warnings.warn(
            "spawn_async() is deprecated. Use start(warm_up_file=...) instead.",
            DeprecationWarning,
            stacklevel=2
        )
        if best_file_uri:
            from pathlib import Path
            from urllib.parse import urlparse
            parsed = urlparse(best_file_uri)
            path = Path(parsed.path) if parsed.path else None
            self.start(warm_up_file=path)
        else:
            self.start()
```

---

#### **Paso 6: Eliminar LSPManager en v2.0** (5min)

**Crear ticket/issue**:
```markdown
# TODO v2.0: Remove LSPManager

- [ ] Delete `src/application/lsp_manager.py`
- [ ] Remove deprecation warnings in tests
- [ ] Update CHANGELOG with breaking change
- [ ] Verify no external dependencies
```

---

### 4.2 Tests de Validación

#### **Test 1: PR2ContextSearcher con LSPClient**

```python
# tests/integration/test_pr2_with_lsp_client.py
def test_pr2_context_searcher_uses_lsp_client(tmp_path):
    """Verify PR2ContextSearcher works with LSPClient."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def foo(): pass")

    searcher = PR2ContextSearcher(
        root=tmp_path,
        lsp_enabled=True,
        # ... other params ...
    )

    # Should have LSPClient instance
    assert isinstance(searcher.lsp_client, LSPClient)

    # Should start LSP
    assert searcher.lsp_client.state in [LSPState.WARMING, LSPState.READY]
```

#### **Test 2: Deprecation Warning**

```python
def test_lsp_manager_shows_deprecation_warning():
    """LSPManager should emit deprecation warning."""
    with pytest.warns(DeprecationWarning, match="LSPManager is deprecated"):
        manager = LSPManager(Path("/tmp"), enabled=False)
```

#### **Test 3: Feature Parity**

```python
def test_lsp_client_has_warm_up_feature():
    """LSPClient should support warm_up_file parameter."""
    tmp_file = Path("/tmp/test.py")
    tmp_file.write_text("def test(): pass")

    client = LSPClient(Path("/tmp"))
    client.start(warm_up_file=tmp_file)

    # Should have called did_open
    assert client._warmup_file == tmp_file
```

---

### 4.3 Rollback Plan

**Si la migración falla**:

1. **Revertir cambios en PR2ContextSearcher**:
```bash
git checkout src/application/pr2_context_searcher.py
```

2. **Remover cambios en LSPClient** (si causan problemas):
```bash
git checkout src/infrastructure/lsp_client.py
```

3. **Mantener LSPManager sin deprecation**:
```bash
git checkout src/application/lsp_manager.py
```

4. **Investigar failure root cause** con systematic debugging

---

## Métricas de Éxito

- ✅ PR2ContextSearcher usa LSPClient
- ✅ Todos los tests pasan
- ✅ LSPManager deprecado (warnings visibles)
- ✅ Cero duplicación de lógica LSP
- ✅ Código más limpio y mantenible
- ✅ CI verde

---

## Riesgos y Mitigaciones

### Riesgo 1: Breaking Changes en PR2ContextSearcher

**Probabilidad**: Media  
**Impacto**: Alto

**Mitigación**:
- Tests exhaustivos antes de merge
- Feature flag para rollback rápido
- Canary deployment en staging

### Riesgo 2: Performance Regression

**Probabilidad**: Baja  
**Impacto**: Medio

**Mitigación**:
- Benchmarks de warming time
- Comparar métricas antes/después
- Telemetría de latencia

---

## Timeline

| Fase | Duración | Responsable |
|------|----------|-------------|
| Paso 1: Portar features | 2h | Agente |
| Paso 2: Migrar PR2ContextSearcher | 1h | Agente |
| Paso 3: Actualizar telemetry | 5min | Agente |
| Paso 4: Migrar tests | 1h | Agente |
| Paso 5: Deprecar LSPManager | 15min | Agente |
| Tests de validación | 1h | Agente |
| **Total** | **~5-6h** | |

---

## Próximos Pasos

1. ✅ Crear branch `fix/unify-lsp-clients`
2. ⏳ Implementar Paso 1 (portar features)
3. ⏳ Implementar Paso 2 (migrar PR2)
4. ⏳ Ejecutar tests
5. ⏳ Code review
6. ⏳ Merge a main
7. ⏳ Monitorear métricas

---

**Investigado**: 2026-01-05  
**Estado**: Listo para Implementación
