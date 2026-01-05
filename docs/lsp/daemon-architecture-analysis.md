# Análisis de Arquitectura del Daemon LSP

**Fecha**: 2026-01-05  
**Versión**: 1.0  
**Estado**: Análisis Completo

---

## Resumen Ejecutivo

Este documento presenta un análisis completo de la arquitectura del daemon LSP de Trifecta, identificando **5 problemas** y proponiendo **5 optimizaciones** priorizadas.

**Componentes Analizados**:
- `LSPDaemonServer` / `LSPDaemonClient` (IPC UNIX socket)
- `LSPClient` (Proceso pyright/pylsp)
- `LSPManager` (posible código muerto)
- `daemon_paths` (gestión de paths AF_UNIX)

**Hallazgos Clave**:
- 🔴 Duplicación de lógica LSP entre `LSPClient` y `LSPManager`
- 🟡 Race condition mitigada pero con leak de streams en edge cases
- 🟡 TTL de daemon no renovable (180s fijo)
- 🟢 Telemetría con sanitización parcial de paths
- 🟡 Falta de observabilidad del daemon

---

## 1. Arquitectura Actual

### 1.1 Componentes Principales

#### **LSPDaemonServer** ([lsp_daemon.py:24](../src/infrastructure/lsp_daemon.py#L24))

**Responsabilidad**: Servidor UNIX socket para IPC con clientes

**Características**:
- Socket: `/tmp/trifecta_lsp_{segment_id}.sock`
- Lock singleton: `/tmp/trifecta_lsp_{segment_id}.lock`
- PID tracking: `/tmp/trifecta_lsp_{segment_id}.pid`
- TTL: 180s (configurable vía env `LSP_DAEMON_TTL_SEC`)
- Protocolo: JSON-RPC line-based sobre UNIX socket

**Métodos Soportados**:
```json
{
  "status": "Retorna estado del daemon (pid, state)",
  "did_open": "Notifica apertura de archivo",
  "request": "Proxy request a LSP server (hover, definition, etc)"
}
```

**Event Loop**:
```python
while self.running:
    # Check TTL cada 1s
    if time.time() - self.last_activity > self.ttl:
        break  # Shutdown por timeout
    
    conn, _ = server.accept()
    self._handle_client(conn)
```

---

#### **LSPDaemonClient** ([lsp_daemon.py:186](../src/infrastructure/lsp_daemon.py#L186))

**Responsabilidad**: Cliente para conectar/spawn daemon

**Flujo**:
```python
client = LSPDaemonClient(root)
client.connect_or_spawn()  # Conecta o inicia daemon

# Send request
resp = client.send({"method": "status"})

# Check ready
if client.is_ready():
    result = client.request("textDocument/definition", params)
```

**Spawn Strategy**:
- Detecta si daemon ya existe (`_try_connect()`)
- Si no: `subprocess.Popen([sys.executable, "-m", "src.infrastructure.lsp_daemon", "start"])`
- Detached process con `start_new_session=True`
- No espera por READY (spawn es asíncrono)

---

#### **LSPClient** ([lsp_client.py:19](../src/infrastructure/lsp_client.py#L19))

**Responsabilidad**: Maneja proceso pyright/pylsp real

**Máquina de Estados**:
```
COLD → WARMING → READY → CLOSED/FAILED
```

**Lifecycle**:
1. `start()`: Spawn subprocess + handshake thread
2. `_run_loop()`: Initialize → Read responses → Transition READY
3. `request()`: Envía request + espera response con timeout
4. `stop()`: Cleanup estricto (terminate → join thread → close streams)

**Thread-Safety**:
- `lock` para cambios de estado
- `_stop_lock` para idempotencia de shutdown
- `_request_events` con `threading.Event` por request

---

#### **daemon_paths** ([daemon_paths.py](../src/infrastructure/daemon_paths.py))

**Responsabilidad**: Genera paths cortos para evitar límite AF_UNIX (108 chars)

**Funciones**:
- `get_daemon_socket_path(segment_id)`: `/tmp/trifecta_lsp_{seg}.sock`
- `get_daemon_lock_path(segment_id)`: `/tmp/trifecta_lsp_{seg}.lock`
- `get_daemon_pid_path(segment_id)`: `/tmp/trifecta_lsp_{seg}.pid`

**Validaciones**:
- Path length < 100 chars
- `/tmp` debe existir y ser writable
- `RuntimeError` si límites excedidos

---

### 1.2 Símbolos AST Extraídos

```bash
# lsp_daemon.py
uv run trifecta ast symbols sym://python/mod/src.infrastructure.lsp_daemon
{
  "symbols": [
    {"kind": "class", "name": "LSPDaemonServer", "line": 24},
    {"kind": "class", "name": "LSPDaemonClient", "line": 186}
  ]
}

# lsp_client.py
uv run trifecta ast symbols sym://python/mod/src.infrastructure.lsp_client
{
  "symbols": [
    {"kind": "class", "name": "LSPState", "line": 11},
    {"kind": "class", "name": "LSPClient", "line": 19}
  ]
}

# daemon_paths.py
uv run trifecta ast symbols sym://python/mod/src.infrastructure.daemon_paths
{
  "symbols": [
    {"kind": "function", "name": "_validate_daemon_base_dir", "line": 16},
    {"kind": "function", "name": "_validate_path_length", "line": 36},
    {"kind": "function", "name": "get_daemon_socket_path", "line": 55},
    {"kind": "function", "name": "get_daemon_lock_path", "line": 74},
    {"kind": "function", "name": "get_daemon_pid_path", "line": 90}
  ]
}
```

---

## 2. Problemas Identificados

### 2.1 🔴 Duplicación de Lógica LSP Client (ALTA)

**Descripción**: Existen **2 implementaciones** de LSP client con responsabilidades solapadas.

**Evidencia**:
- [lsp_client.py](../src/infrastructure/lsp_client.py): `LSPClient` (usado por daemon)
- [lsp_manager.py](../src/application/lsp_manager.py): `LSPManager` (uso incierto)

**Comparación**:
| Característica | LSPClient | LSPManager |
|----------------|-----------|------------|
| Estado | `LSPState` enum | `LSPState` enum (mismo) |
| Proceso | `subprocess.Popen` | `subprocess.Popen` |
| Thread-safe | Sí (locks) | Sí (locks) |
| Handshake | Automático | Automático |
| Usado por | Daemon | ??? |

**Impacto**:
- Mantenimiento duplicado
- Confusión arquitectónica
- Riesgo de divergencia

**Acción Requerida**:
```bash
# Investigar uso de LSPManager
rg "LSPManager" src/ tests/ --type py

# Si no se usa: marcar deprecated
# Migrar uso a LSPClient del daemon
# Eliminar en v2.0
```

---

### 2.2 🟡 Race Condition en Shutdown (MEDIA)

**Descripción**: El shutdown tiene un orden estricto pero leak de streams en edge cases.

**Código Problemático** ([lsp_client.py:143-148](../src/infrastructure/lsp_client.py#L143-L148)):
```python
# 4. Join background thread BEFORE closing streams
if self._thread and self._thread.is_alive():
    self._thread.join(timeout=1.0)
    
    # CRITICAL: If thread still alive after join, DO NOT close streams
    # This avoids write-to-closed-file race in edge cases (blocked I/O)
    # Better to leak streams in rare shutdown failure than reintroduce bug
    if self._thread.is_alive():
        return  # ⚠️ Stream leak pero previene crash
```

**Análisis**:
- **Problema Original**: Thread escribiendo a stream cerrado → crash
- **Fix Actual**: Leak streams si thread no termina en 1s
- **Trade-off**: Prefiere leak sobre crash (defensivo pero no ideal)

**Casos Edge**:
- Thread bloqueado en I/O (LSP server hung)
- Timeout de 1s insuficiente en CI/sistemas lentos
- Leak acumulado si muchos stop/start

**Impacto**: 
- 🟢 Previene crashes
- 🟡 Leak de file descriptors en edge cases
- 🟡 Timeout podría ser configurable

---

### 2.3 🟡 Daemon TTL No Renovable (MEDIA)

**Descripción**: TTL de 180s no se puede renovar sin hacer request.

**Código** ([lsp_daemon.py:58-61](../src/infrastructure/lsp_daemon.py#L58-L61)):
```python
while self.running:
    # Check TTL
    if time.time() - self.last_activity > self.ttl:
        self.telemetry.event("lsp.daemon_status", {}, {"status": "shutdown_ttl"}, 1)
        break
```

**`last_activity` solo actualiza en** ([lsp_daemon.py:96](../src/infrastructure/lsp_daemon.py#L96)):
```python
def _handle_client(self, conn: socket.socket):
    self.last_activity = time.time()  # ⚠️ Solo aquí
```

**Problemas**:
- No hay método de "keep-alive" explícito
- Si usuario no hace requests durante 180s → daemon muere
- Reiniciar daemon tiene overhead (warming LSP server)
- No hay opción de daemon "persistente"

**Casos de Uso Afectados**:
- Sesiones largas sin actividad (usuario pensando)
- Background warming para siguiente request
- CI/tests con delays entre steps

**Impacto**: Overhead innecesario de restart.

---

### 2.4 🟢 Telemetría Con Paths Potencialmente Inseguros (BAJA)

**Descripción**: Sanitización de paths es parcial.

**Sanitización Correcta** ([lsp_client.py:79-85](../src/infrastructure/lsp_client.py#L79-L85)):
```python
exe_log = "unknown"
try:
    if executable:
        exe_log = Path(executable).name  # ✅ Solo nombre
except Exception:
    pass
```

**Potencial Problema** (otros lugares):
```python
file=str(file_path.relative_to(root))  # ⚠️ Podría fallar si file_path fuera de root
```

**Riesgo**: 
- Muy bajo (paths generalmente dentro de workspace)
- `relative_to()` lanza `ValueError` si no es relativo
- Crash en telemetry no es crítico pero molesto

**Impacto**: Menor, pero mejorable.

---

### 2.5 🟡 No Hay Observabilidad del Daemon (MEDIA)

**Descripción**: El daemon no expone métricas de uso.

**Información Faltante**:
- ¿Cuánto tiempo lleva vivo?
- ¿Cuántos requests ha manejado?
- ¿Cuánto TTL le queda?
- ¿Estado actual del LSP server?
- ¿Warming time promedio?
- ¿Cache hit rate (si existiera)?

**Impacto**:
- Difícil de debuggear
- No se pueden optimizar tiempos
- No hay métricas para dashboards

**Workaround Actual**: Ver PID file + ps, pero no suficiente.

---

## 3. Optimizaciones Propuestas

### 3.1 🔥 Unificar LSP Clients (ALTA PRIORIDAD)

**Objetivo**: Eliminar duplicación entre `LSPClient` y `LSPManager`.

**Plan**:

#### Fase 1: Auditoría (1-2h)
```bash
# 1. Buscar todos los usos de LSPManager
rg "from.*lsp_manager import|LSPManager" src/ tests/ --type py

# 2. Buscar instanciaciones
rg "LSPManager\(" src/ tests/ --type py

# 3. Verificar tests
rg "test.*lsp_manager" tests/ --type py
```

#### Fase 2: Migración (2-3h)
```python
# Si LSPManager tiene features únicas, portarlas a LSPClient
# Ejemplo: spawn_async con best_file_uri

class LSPClient:
    def start(self, warm_up_file: Optional[Path] = None) -> None:
        """Start LSP server and optionally warm up with file."""
        # ... existing code ...
        if warm_up_file and warm_up_file.exists():
            content = warm_up_file.read_text()
            self.did_open(warm_up_file, content)
```

#### Fase 3: Deprecación (1h)
```python
# lsp_manager.py
import warnings
from src.infrastructure.lsp_client import LSPClient as _LSPClient

class LSPManager(_LSPClient):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "LSPManager is deprecated. Use LSPClient from lsp_client.py",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)
```

#### Fase 4: Eliminación (v2.0)
- Remover `lsp_manager.py`
- Actualizar imports
- Actualizar tests

**Beneficios**:
- ✅ Código más limpio
- ✅ Mantenimiento simplificado
- ✅ Menos confusión

---

### 3.2 🔥 Daemon Observability (ALTA PRIORIDAD)

**Objetivo**: Exponer métricas del daemon vía comando CLI.

**Implementación**:

#### Paso 1: Agregar método `stats` al daemon ([lsp_daemon.py](../src/infrastructure/lsp_daemon.py))

```python
class LSPDaemonServer:
    def __init__(self, segment_root: Path, ttl_sec: int = DEFAULT_TTL):
        # ... existing code ...
        self.start_time = time.time()
        self.request_count = 0
    
    def _handle_client(self, conn: socket.socket):
        self.last_activity = time.time()
        self.request_count += 1  # ← Track requests
        # ... rest of existing code ...
    
    def _process_request(self, req: Dict) -> Dict:
        method = req.get("method")
        
        if method == "stats":
            uptime = time.time() - self.start_time
            ttl_remaining = self.ttl - (time.time() - self.last_activity)
            
            return {
                "status": "ok",
                "data": {
                    "uptime_sec": round(uptime, 2),
                    "ttl_remaining_sec": round(ttl_remaining, 2),
                    "requests_handled": self.request_count,
                    "lsp_state": self.lsp_client.state.value,
                    "pid": os.getpid(),
                    "segment_root": str(self.root),
                }
            }
        
        # ... existing methods (status, did_open, request) ...
```

#### Paso 2: Agregar comando CLI ([cli.py](../src/infrastructure/cli.py) o nuevo subcommand)

```python
@app.command("daemon-stats")
def daemon_stats(
    segment: str = typer.Option(".", "--segment"),
):
    """Get daemon statistics."""
    root = Path(segment).resolve()
    client = LSPDaemonClient(root)
    
    if not client._try_connect():
        typer.echo("Daemon not running")
        raise typer.Exit(1)
    
    resp = client.send({"method": "stats"})
    
    if resp.get("status") != "ok":
        typer.echo(f"Error: {resp.get('message')}")
        raise typer.Exit(1)
    
    data = resp["data"]
    
    # Pretty print
    print(f"""
Daemon Statistics
=================
PID:              {data['pid']}
Uptime:           {data['uptime_sec']:.1f}s
TTL Remaining:    {data['ttl_remaining_sec']:.1f}s
Requests Handled: {data['requests_handled']}
LSP State:        {data['lsp_state']}
Segment Root:     {data['segment_root']}
    """)
```

#### Paso 3: Agregar al Makefile

```makefile
daemon-stats:
	$(UV) trifecta daemon-stats --segment $(SEGMENT)
```

**Uso**:
```bash
make daemon-stats SEGMENT=.
# o
trifecta daemon-stats --segment .
```

**Beneficios**:
- ✅ Debugging más fácil
- ✅ Monitoreo de salud del daemon
- ✅ Métricas para optimización

---

### 3.3 🔶 TTL Renovable + Keep-Alive (MEDIA PRIORIDAD)

**Objetivo**: Permitir daemon de larga duración sin reinicio.

**Implementación**:

#### Paso 1: Agregar método `ping`

```python
def _process_request(self, req: Dict) -> Dict:
    method = req.get("method")
    
    if method == "ping":
        self.last_activity = time.time()  # ← Renovar TTL
        ttl_remaining = self.ttl - (time.time() - self.last_activity)
        return {
            "status": "ok",
            "ttl_remaining": ttl_remaining,
            "renewed_at": time.time(),
        }
```

#### Paso 2: CLI con loop automático

```python
@app.command("daemon-ping")
def daemon_ping(
    segment: str = typer.Option(".", "--segment"),
    loop: Optional[int] = typer.Option(None, "--loop", help="Ping every N seconds"),
):
    """Ping daemon to renew TTL."""
    root = Path(segment).resolve()
    client = LSPDaemonClient(root)
    
    def do_ping():
        resp = client.send({"method": "ping"})
        if resp.get("status") == "ok":
            ttl = resp.get("ttl_remaining", 0)
            print(f"✓ Daemon pinged. TTL: {ttl:.1f}s")
        else:
            print(f"✗ Ping failed: {resp.get('message')}")
    
    if loop:
        import time
        print(f"Keep-alive loop: pinging every {loop}s (Ctrl+C to stop)")
        try:
            while True:
                do_ping()
                time.sleep(loop)
        except KeyboardInterrupt:
            print("\nStopped")
    else:
        do_ping()
```

**Uso**:
```bash
# Single ping
trifecta daemon-ping --segment .

# Keep-alive automático cada 60s
trifecta daemon-ping --segment . --loop 60 &
```

**Beneficios**:
- ✅ Daemon persistente para sesiones largas
- ✅ Reduce overhead de restarts
- ✅ Mejor experiencia en dev/CI

---

### 3.4 🔶 Graceful Shutdown con Timeout Escalado (MEDIA PRIORIDAD)

**Objetivo**: Mejorar shutdown sin leak de streams.

**Problema Actual**:
- Timeout fijo de 1s
- Si thread no termina → leak streams
- No hay retry ni escalación

**Propuesta**:

```python
def stop(self) -> None:
    """Strict cleanup with escalating timeouts."""
    with self._stop_lock:
        if not self.stopping.is_set():
            self.stopping.set()
        
        with self.lock:
            if self.state == LSPState.CLOSED:
                return
            self.state = LSPState.CLOSED
        
        # Terminate process
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=0.2)
            except Exception:
                pass
        
        # Escalating timeouts for thread join
        TIMEOUTS = [0.5, 1.0, 2.0]  # Total: 3.5s
        thread_exited = False
        
        for i, timeout in enumerate(TIMEOUTS):
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=timeout)
                if not self._thread.is_alive():
                    thread_exited = True
                    break
                else:
                    # Still alive, try more aggressive termination
                    if i == len(TIMEOUTS) - 1:
                        # Last resort: kill process again
                        if self.process:
                            try:
                                self.process.kill()
                            except Exception:
                                pass
        
        # Only close streams if thread exited cleanly
        if thread_exited or not (self._thread and self._thread.is_alive()):
            self._close_streams()
        else:
            # Log warning but don't crash
            if self.telemetry:
                self.telemetry.event(
                    "lsp.shutdown",
                    {},
                    {"status": "warning", "reason": "thread_leak"},
                    0
                )

def _close_streams(self):
    """Close all process streams."""
    if self.process:
        try:
            if self.process.stdin:
                self.process.stdin.close()
            if self.process.stdout:
                self.process.stdout.close()
            if self.process.stderr:
                self.process.stderr.close()
        except Exception:
            pass
```

**Beneficios**:
- ✅ Menos leaks (3 intentos con timeouts crecientes)
- ✅ Más robusto en CI/sistemas lentos
- ✅ Telemetría de casos anómalos

---

### 3.5 🔵 Daemon Cache de Resultados LSP (BAJA PRIORIDAD)

**Objetivo**: Cachear responses para reducir latencia.

**Motivación**:
- Requests repetidos a mismo symbol → misma response
- Hover sobre función → cacheable mientras no cambie
- Definition lookup → cacheable con TTL corto

**Implementación**:

```python
from collections import OrderedDict
from dataclasses import dataclass
import time

@dataclass
class CacheEntry:
    result: Dict
    timestamp: float
    hits: int = 0

class LSPResponseCache:
    def __init__(self, max_size: int = 100, ttl_sec: float = 60.0):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl_sec
        self._hits = 0
        self._misses = 0
    
    def _make_key(self, method: str, params: Dict) -> str:
        """Create cache key from method + params."""
        uri = params.get("textDocument", {}).get("uri", "")
        pos = params.get("position", {})
        line = pos.get("line", -1)
        char = pos.get("character", -1)
        return f"{method}:{uri}:{line}:{char}"
    
    def get(self, method: str, params: Dict) -> Optional[Dict]:
        """Get cached result if exists and not expired."""
        key = self._make_key(method, params)
        
        if key in self._cache:
            entry = self._cache[key]
            
            # Check TTL
            if time.time() - entry.timestamp > self._ttl:
                del self._cache[key]
                self._misses += 1
                return None
            
            # LRU: move to end
            self._cache.move_to_end(key)
            entry.hits += 1
            self._hits += 1
            return entry.result
        
        self._misses += 1
        return None
    
    def set(self, method: str, params: Dict, result: Dict) -> None:
        """Store result in cache."""
        key = self._make_key(method, params)
        
        # Evict oldest if at capacity
        if len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)
        
        self._cache[key] = CacheEntry(
            result=result,
            timestamp=time.time()
        )
    
    def stats(self) -> Dict:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / (self._hits + self._misses) if (self._hits + self._misses) > 0 else 0.0,
        }
```

**Integración en Daemon**:

```python
class LSPDaemonServer:
    def __init__(self, segment_root: Path, ttl_sec: int = DEFAULT_TTL):
        # ... existing code ...
        self.response_cache = LSPResponseCache(max_size=100, ttl_sec=60.0)
    
    def _process_request(self, req: Dict) -> Dict:
        method = req.get("method")
        
        if method == "request":
            lsp_method = params.get("method")
            lsp_params = params.get("params")
            
            # Check cache for cacheable methods
            if lsp_method in ["textDocument/definition", "textDocument/hover"]:
                cached = self.response_cache.get(lsp_method, lsp_params)
                if cached:
                    return {"status": "ok", "data": cached, "cached": True}
            
            # Normal request
            result = self.lsp_client.request(lsp_method, lsp_params)
            
            # Cache result
            if result and lsp_method in ["textDocument/definition", "textDocument/hover"]:
                self.response_cache.set(lsp_method, lsp_params, result)
            
            return {"status": "ok", "data": result, "cached": False}
        
        if method == "stats":
            # Include cache stats
            cache_stats = self.response_cache.stats()
            return {
                "status": "ok",
                "data": {
                    # ... existing stats ...
                    "cache": cache_stats,
                }
            }
```

**Beneficios**:
- ✅ Latencia reducida para requests repetidos
- ✅ Menos carga en LSP server
- ✅ Estadísticas observables

**Trade-offs**:
- 🟡 Cache puede estar stale si archivo cambia
- 🟡 Más memoria usada
- 🟡 Complejidad adicional

**Mitigación**:
- Invalidar cache en `did_open` / `did_change`
- TTL corto (60s)
- Cache pequeño (100 entradas)

---

## 4. Plan de Implementación

### Fase 1: Optimizaciones ALTA (1-2 días)

#### Día 1 AM: Unificar LSP Clients
- [ ] Auditar uso de `LSPManager`
- [ ] Identificar features únicas
- [ ] Portar a `LSPClient` si necesario
- [ ] Marcar `LSPManager` como deprecated

#### Día 1 PM: Daemon Observability
- [ ] Agregar `stats` method a daemon
- [ ] Agregar `daemon-stats` CLI command
- [ ] Agregar tests de stats
- [ ] Actualizar Makefile

**Entregables**:
- `LSPManager` deprecated
- Comando `trifecta daemon-stats` funcional
- Tests pasando

---

### Fase 2: Optimizaciones MEDIA (2-3 días)

#### Día 2 AM: TTL Renovable
- [ ] Agregar `ping` method a daemon
- [ ] Agregar `daemon-ping` CLI command
- [ ] Agregar opción `--loop` para keep-alive
- [ ] Tests de renovación de TTL

#### Día 2 PM: Graceful Shutdown
- [ ] Implementar timeouts escalados
- [ ] Extraer `_close_streams()` method
- [ ] Agregar telemetría de leaks
- [ ] Tests de shutdown edge cases

**Entregables**:
- Comando `trifecta daemon-ping` funcional
- Shutdown más robusto
- Tests de edge cases

---

### Fase 3: Optimizaciones BAJA (1-2 días, opcional)

#### Día 3: Cache de Responses
- [ ] Implementar `LSPResponseCache`
- [ ] Integrar en daemon
- [ ] Invalidación en `did_change`
- [ ] Tests de cache hit/miss
- [ ] Agregar cache stats a `daemon-stats`

**Entregables**:
- Cache funcional con LRU + TTL
- Métricas de hit rate

---

## 5. Validación y Tests

### Tests Existentes a Actualizar

#### [test_lsp_daemon.py](../tests/integration/test_lsp_daemon.py)
- ✅ `test_daemon_spawn_and_connect`
- ✅ `test_daemon_singleton_lock`
- ✅ `test_ttl_shutdown_cleans_files`
- ✅ `test_no_blocking_on_cold_start`

#### Nuevos Tests a Crear

```python
# test_daemon_observability.py
def test_daemon_stats_includes_uptime():
    client = LSPDaemonClient(root)
    client.connect_or_spawn()
    
    time.sleep(1)
    resp = client.send({"method": "stats"})
    
    assert resp["status"] == "ok"
    assert resp["data"]["uptime_sec"] >= 1.0
    assert "ttl_remaining_sec" in resp["data"]

def test_daemon_stats_tracks_requests():
    client = LSPDaemonClient(root)
    client.connect_or_spawn()
    
    # Make 3 requests
    for _ in range(3):
        client.send({"method": "status"})
    
    resp = client.send({"method": "stats"})
    assert resp["data"]["requests_handled"] >= 3

# test_daemon_keep_alive.py
def test_ping_renews_ttl():
    client = LSPDaemonClient(root)
    client.connect_or_spawn()
    
    # Get initial TTL
    stats1 = client.send({"method": "stats"})
    ttl1 = stats1["data"]["ttl_remaining_sec"]
    
    time.sleep(2)
    
    # Ping to renew
    client.send({"method": "ping"})
    
    stats2 = client.send({"method": "stats"})
    ttl2 = stats2["data"]["ttl_remaining_sec"]
    
    # TTL should be renewed (close to original)
    assert ttl2 > ttl1

# test_lsp_response_cache.py
def test_cache_hit_for_repeated_request():
    cache = LSPResponseCache()
    method = "textDocument/definition"
    params = {"textDocument": {"uri": "file.py"}, "position": {"line": 10, "character": 5}}
    result = {"range": {...}}
    
    # First: miss
    assert cache.get(method, params) is None
    
    # Set
    cache.set(method, params, result)
    
    # Second: hit
    cached = cache.get(method, params)
    assert cached == result
    
    # Stats
    stats = cache.stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["hit_rate"] == 0.5
```

---

## 6. Métricas de Éxito

### Optimización 1: Unificar LSP Clients
- ✅ `LSPManager` marcado como deprecated
- ✅ Cero referencias a `LSPManager` en código nuevo
- ✅ Tests migrads a `LSPClient`

### Optimización 2: Daemon Observability
- ✅ Comando `daemon-stats` funcional
- ✅ Métricas expuestas: uptime, TTL, requests, state
- ✅ Facilita debugging en <30s

### Optimización 3: TTL Renovable
- ✅ Daemon puede vivir indefinidamente con ping
- ✅ Comando `daemon-ping --loop 60` funcional
- ✅ Reduce restarts en sesiones largas (>50%)

### Optimización 4: Graceful Shutdown
- ✅ Stream leaks reducidos (tests de 100 shutdowns sin leaks)
- ✅ Telemetría de leaks anómalos
- ✅ CI más estable

### Optimización 5: Cache de Responses (opcional)
- ✅ Cache hit rate > 30% en uso típico
- ✅ Latencia reducida en 50% para cache hits
- ✅ Invalidación correcta en file changes

---

## 7. Riesgos y Mitigaciones

### Riesgo 1: Eliminar `LSPManager` rompe código existente

**Probabilidad**: Media  
**Impacto**: Alto  

**Mitigación**:
- Auditar TODO el codebase antes de eliminar
- Deprecar primero, eliminar en v2.0
- Tests de regresión exhaustivos

---

### Riesgo 2: Cache stale data

**Probabilidad**: Media  
**Impacto**: Medio (definiciones incorrectas)

**Mitigación**:
- TTL corto (60s)
- Invalidar en `did_change` / `did_open`
- Cachear solo métodos idempotentes
- Logs de cache invalidations

---

### Riesgo 3: Daemon con bugs persiste más tiempo

**Probabilidad**: Baja  
**Impacto**: Alto (experiencia degradada)

**Mitigación**:
- TTL renovable pero no infinito (max 30min?)
- Health checks periódicos
- Restart automático si state=FAILED

---

## 8. Referencias

### Archivos Clave
- [lsp_daemon.py](../src/infrastructure/lsp_daemon.py)
- [lsp_client.py](../src/infrastructure/lsp_client.py)
- [lsp_manager.py](../src/application/lsp_manager.py)
- [daemon_paths.py](../src/infrastructure/daemon_paths.py)
- [test_lsp_daemon.py](../tests/integration/test_lsp_daemon.py)

### Tests
- [test_daemon_paths_constraints.py](../tests/integration/test_daemon_paths_constraints.py)

### Documentación Relacionada
- [CLI Workflow](../CLI_WORKFLOW.md)
- [Agent Context](../_ctx/agent_trifecta_dope.md)

---

**Generado**: 2026-01-05  
**Autor**: GitHub Copilot (Claude Sonnet 4.5)  
**Próxima Revisión**: Después de implementar Fase 1
