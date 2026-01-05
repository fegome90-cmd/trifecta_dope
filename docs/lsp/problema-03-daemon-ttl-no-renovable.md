# Problema 3: Daemon TTL No Renovable

**Prioridad**: 🟡 MEDIA  
**Estado**: Investigación Completa  
**Fecha**: 2026-01-05

---

## Resumen Ejecutivo

El daemon LSP tiene un **TTL fijo de 180s** que se resetea solo cuando hay requests. No existe mecanismo de **keep-alive** o **renovación manual**, causando shutdowns innecesarios en sesiones largas sin actividad.

**Código Afectado**: [lsp_daemon.py:58-76, 96](../../src/infrastructure/lsp_daemon.py)

---

## Phase 1: Root Cause Investigation

### 1.1 Código del TTL Check

**Event Loop** ([lsp_daemon.py:70-76](../../src/infrastructure/lsp_daemon.py#L70-L76)):

```python
# 6. Event Loop
while self.running:
    try:
        # Check TTL
        if time.time() - self.last_activity > self.ttl:
            self.telemetry.event("lsp.daemon_status", {}, {"status": "shutdown_ttl"}, 1)
            break  # ← Shutdown por timeout

        try:
            conn, _ = server.accept()
            conn.settimeout(None)
            self._handle_client(conn)
        except socket.timeout:
            continue  # Loop to check activity/TTL
```

**Actualización de `last_activity`** ([lsp_daemon.py:96](../../src/infrastructure/lsp_daemon.py#L96)):

```python
def _handle_client(self, conn: socket.socket):
    self.last_activity = time.time()  # ← SOLO aquí se actualiza
    try:
        # ... handle request ...
```

---

### 1.2 Problema: Solo Requests Renuevan TTL

**Escenarios Problemáticos**:

1. **Usuario pensando** (5 minutos sin escribir código):
   ```
   t=0:   start daemon, TTL=180s
   t=60:  usuario lee código (no requests)
   t=120: usuario piensa en solución (no requests)
   t=180: SHUTDOWN_TTL → daemon muere
   t=181: usuario hace hover → daemon debe restart (overhead)
   ```

2. **CI con delays**:
   ```
   t=0:   daemon start
   t=60:  CI step 1 completes
   t=120: CI waiting for resource
   t=180: SHUTDOWN_TTL → daemon muere
   t=200: CI step 2 needs LSP → daemon restart
   ```

3. **Background warming**:
   ```
   t=0:   daemon start, warm up main.py
   t=180: SHUTDOWN_TTL → daemon muere
   t=300: usuario vuelve de lunch → daemon restart
   ```

**Impacto**:
- Overhead de restart: ~2-5s (spawn + LSP handshake)
- Pérdida de warming state
- Usuario percibe lag

---

### 1.3 Configuración Actual

**TTL Default** ([lsp_daemon.py:22](../../src/infrastructure/lsp_daemon.py#L22)):
```python
DEFAULT_TTL = 180  # seconds
```

**Configuración via Env**:
```python
parser.add_argument(
    "--ttl", 
    type=int, 
    default=int(os.environ.get("LSP_DAEMON_TTL_SEC", DEFAULT_TTL))
)
```

**Limitaciones**:
- Solo configurable al start (no runtime)
- No hay opción de "infinito" o "manual shutdown"
- No hay keep-alive automático

---

## Phase 2: Pattern Analysis

### 2.1 Patrón: Idle Timeout vs Keep-Alive

**Comparación con Otros Sistemas**:

| Sistema | Approach | Renovación |
|---------|----------|------------|
| **Redis** | `timeout 0` = never expire | No automática |
| **Docker** | `--health-cmd` periódico | Automática |
| **SSH** | `ClientAliveInterval` | Keep-alive packets |
| **gRPC** | `keepalive_time_ms` | Keep-alive pings |
| **Trifecta Daemon** | Fixed TTL, no keep-alive | ❌ Solo en requests |

---

### 2.2 Soluciones Comunes

#### **Solución 1: Ping/Heartbeat Method**

**Usado por**: HTTP KeepAlive, gRPC, WebSocket

```python
# Client periódicamente envía ping:
while True:
    daemon.ping()  # ← Renueva TTL
    time.sleep(60)
```

**Pros**:
- Simple de implementar
- Cliente controla lifetime
- No requiere cambios en event loop

**Contras**:
- Cliente debe mantener ping loop
- Overhead de IPC calls

---

#### **Solución 2: TTL Infinito con Shutdown Manual**

**Usado por**: Servers de larga duración (nginx, postgres)

```python
# Configuración:
--ttl 0  # ← 0 = infinito

# Shutdown manual:
daemon.shutdown()
```

**Pros**:
- No shutdowns inesperados
- Útil para dev/debugging

**Contras**:
- Daemon puede quedar zombie si usuario olvida cerrar
- Consume recursos indefinidamente

---

#### **Solución 3: Adaptive TTL**

**Usado por**: Sistemas con ML/heurísticas

```python
# TTL aumenta con uso:
if request_count > 10:
    ttl = 600  # 10min
elif request_count > 100:
    ttl = 3600  # 1h
```

**Pros**:
- Inteligente, se adapta a uso
- Evita shutdowns en sesiones activas

**Contras**:
- Más complejo
- Heurísticas pueden fallar

---

## Phase 3: Hypothesis and Testing

### 3.1 Hipótesis: Ping Method es Suficiente

**Hipótesis**: Un método `ping` simple resuelve el problema sin complejidad.

**Prueba de Concepto**:

```python
# En daemon:
def _process_request(self, req: Dict) -> Dict:
    method = req.get("method")
    
    if method == "ping":
        self.last_activity = time.time()  # ← Renovar TTL
        return {
            "status": "ok",
            "ttl_remaining": self.ttl - (time.time() - self.last_activity),
        }
```

**Test**:
```python
def test_ping_renews_ttl():
    daemon = LSPDaemonServer(root, ttl_sec=10)
    daemon.start()
    
    time.sleep(5)
    
    # Get TTL before ping
    stats1 = daemon.send({"method": "stats"})
    ttl1 = stats1["data"]["ttl_remaining"]
    
    # Wait more
    time.sleep(3)
    
    # Ping to renew
    daemon.send({"method": "ping"})
    
    # Get TTL after ping
    stats2 = daemon.send({"method": "stats"})
    ttl2 = stats2["data"]["ttl_remaining"]
    
    # TTL should be renewed (close to original)
    assert ttl2 > ttl1  # Success!
```

---

## Phase 4: Implementation

### 4.1 Solución: Ping Method + CLI Keep-Alive

#### **Paso 1: Agregar Método Ping al Daemon**

**Modificar** [lsp_daemon.py:119-165](../../src/infrastructure/lsp_daemon.py):

```python
def _process_request(self, req: Dict) -> Dict:
    method = req.get("method")
    params = req.get("params", {})

    if method == "status":
        return {
            "status": "ok",
            "data": {"state": self.lsp_client.state.value, "pid": os.getpid()},
        }

    elif method == "ping":  # ← NUEVO
        """Renew TTL and return remaining time."""
        self.last_activity = time.time()
        ttl_remaining = self.ttl - (time.time() - self.last_activity)
        
        if self.telemetry:
            self.telemetry.event(
                "lsp.ping",
                {},
                {"ttl_remaining": round(ttl_remaining, 2)},
                1
            )
        
        return {
            "status": "ok",
            "ttl_remaining": round(ttl_remaining, 2),
            "renewed_at": round(time.time(), 2),
        }

    elif method == "did_open":
        path_str = params.get("path")
        content = params.get("content")
        if path_str and content:
            self.lsp_client.did_open(Path(path_str), content)
        return {"status": "ok"}

    # ... rest of existing methods ...
```

---

#### **Paso 2: CLI Command para Ping**

**Crear** `src/infrastructure/cli_daemon.py`:

```python
import typer
import time
from pathlib import Path
from src.infrastructure.lsp_daemon import LSPDaemonClient

daemon_app = typer.Typer(help="Daemon management commands")


@daemon_app.command("ping")
def daemon_ping(
    segment: str = typer.Option(".", "--segment", help="Segment root"),
    loop: int = typer.Option(0, "--loop", help="Ping every N seconds (0=once)"),
):
    """Ping daemon to renew TTL."""
    root = Path(segment).resolve()
    client = LSPDaemonClient(root)
    
    if not client._try_connect():
        typer.echo("❌ Daemon not running", err=True)
        raise typer.Exit(1)
    
    def do_ping():
        resp = client.send({"method": "ping"})
        if resp.get("status") == "ok":
            ttl = resp.get("ttl_remaining", 0)
            renewed = resp.get("renewed_at", 0)
            typer.echo(f"✓ Daemon pinged. TTL: {ttl:.1f}s (renewed at {renewed:.0f})")
        else:
            typer.echo(f"✗ Ping failed: {resp.get('message')}", err=True)
    
    if loop > 0:
        typer.echo(f"Keep-alive loop: pinging every {loop}s (Ctrl+C to stop)")
        try:
            while True:
                do_ping()
                time.sleep(loop)
        except KeyboardInterrupt:
            typer.echo("\n✓ Stopped")
    else:
        do_ping()


@daemon_app.command("status")
def daemon_status(
    segment: str = typer.Option(".", "--segment"),
):
    """Get daemon status."""
    root = Path(segment).resolve()
    client = LSPDaemonClient(root)
    
    if not client._try_connect():
        typer.echo("❌ Daemon not running")
        raise typer.Exit(1)
    
    resp = client.send({"method": "status"})
    if resp.get("status") == "ok":
        data = resp["data"]
        typer.echo(f"""
Daemon Status:
  State: {data.get('state')}
  PID:   {data.get('pid')}
""")
    else:
        typer.echo(f"✗ Error: {resp.get('message')}", err=True)
        raise typer.Exit(1)
```

**Integrar en CLI principal** `src/infrastructure/cli.py`:

```python
from src.infrastructure.cli_daemon import daemon_app

app = typer.Typer()
app.add_typer(daemon_app, name="daemon")
```

---

#### **Paso 3: Makefile Shortcuts**

**Agregar a** [Makefile](../../Makefile):

```makefile
# Daemon Management
daemon-ping:
	$(UV) trifecta daemon ping --segment $(SEGMENT)

daemon-keep-alive:
	$(UV) trifecta daemon ping --segment $(SEGMENT) --loop 60 &

daemon-status:
	$(UV) trifecta daemon status --segment $(SEGMENT)
```

---

### 4.2 Uso

#### **Ping Manual**:
```bash
# Single ping
trifecta daemon ping --segment .
# Output: ✓ Daemon pinged. TTL: 175.3s (renewed at 1704484800)

make daemon-ping SEGMENT=.
```

#### **Keep-Alive Automático**:
```bash
# Background process que hace ping cada 60s
trifecta daemon ping --segment . --loop 60 &
# Output: Keep-alive loop: pinging every 60s (Ctrl+C to stop)

# O via Makefile:
make daemon-keep-alive SEGMENT=.
```

#### **Detener Keep-Alive**:
```bash
# Find PID
ps aux | grep "trifecta daemon ping"

# Kill
kill <PID>
```

---

### 4.3 Mejora Adicional: TTL Infinito

**Agregar opción** `--ttl 0` para daemon persistente:

**Modificar** [lsp_daemon.py:70-76](../../src/infrastructure/lsp_daemon.py#L70-L76):

```python
# 6. Event Loop
while self.running:
    try:
        # Check TTL (skip if TTL=0)
        if self.ttl > 0:  # ← Agregar check
            if time.time() - self.last_activity > self.ttl:
                self.telemetry.event("lsp.daemon_status", {}, {"status": "shutdown_ttl"}, 1)
                break

        try:
            conn, _ = server.accept()
            conn.settimeout(None)
            self._handle_client(conn)
        except socket.timeout:
            continue
```

**Uso**:
```bash
# Daemon sin TTL (manual shutdown)
trifecta daemon start --segment . --ttl 0

# Shutdown manual:
trifecta daemon shutdown --segment .
```

---

### 4.4 Tests de Validación

#### **Test 1: Ping Renueva TTL**

```python
def test_ping_renews_ttl(clean_daemon_env):
    """Verify ping renews daemon TTL."""
    root = clean_daemon_env
    
    # Start daemon with short TTL
    cmd = [sys.executable, "-m", "src.infrastructure.lsp_daemon", "start", "--root", str(root), "--ttl", "10"]
    subprocess.Popen(cmd, start_new_session=True)
    
    # Wait for startup
    seg_id = compute_segment_id(root)
    pid_file = get_daemon_pid_path(seg_id)
    assert wait_for_file(pid_file, timeout=5.0)
    
    # Wait 5s (half TTL)
    time.sleep(5)
    
    # Ping to renew
    client = LSPDaemonClient(root)
    resp1 = client.send({"method": "ping"})
    assert resp1["status"] == "ok"
    ttl1 = resp1["ttl_remaining"]
    assert ttl1 > 8  # Should be close to 10s (renewed)
    
    # Wait 3s more (would be 8s without ping)
    time.sleep(3)
    
    # Check daemon still alive
    assert pid_file.exists()
    
    # Get TTL again
    resp2 = client.send({"method": "ping"})
    ttl2 = resp2["ttl_remaining"]
    assert ttl2 > 5  # Should be ~7s (10 - 3)
```

#### **Test 2: TTL=0 Nunca Expira**

```python
def test_daemon_with_infinite_ttl(clean_daemon_env):
    """Verify daemon with TTL=0 never shuts down."""
    root = clean_daemon_env
    
    # Start daemon with TTL=0
    cmd = [sys.executable, "-m", "src.infrastructure.lsp_daemon", "start", "--root", str(root), "--ttl", "0"]
    subprocess.Popen(cmd, start_new_session=True)
    
    seg_id = compute_segment_id(root)
    pid_file = get_daemon_pid_path(seg_id)
    assert wait_for_file(pid_file, timeout=5.0)
    
    # Wait 5 seconds (would shutdown with TTL < 5)
    time.sleep(5)
    
    # Daemon should still be alive
    assert pid_file.exists()
    
    client = LSPDaemonClient(root)
    resp = client.send({"method": "status"})
    assert resp["status"] == "ok"
```

#### **Test 3: Keep-Alive CLI**

```python
def test_daemon_ping_cli(clean_daemon_env):
    """Verify daemon ping CLI command works."""
    root = clean_daemon_env
    
    # Start daemon
    LSPDaemonClient(root).connect_or_spawn()
    
    # Wait for startup
    seg_id = compute_segment_id(root)
    pid_file = get_daemon_pid_path(seg_id)
    assert wait_for_file(pid_file, timeout=5.0)
    
    # Run ping CLI
    result = subprocess.run(
        [sys.executable, "-m", "src.infrastructure.cli", "daemon", "ping", "--segment", str(root)],
        capture_output=True,
        text=True,
    )
    
    assert result.returncode == 0
    assert "✓ Daemon pinged" in result.stdout
    assert "TTL:" in result.stdout
```

---

## Métricas de Éxito

- ✅ Comando `daemon ping` funcional
- ✅ Keep-alive loop sin crashes
- ✅ TTL renovado correctamente
- ✅ TTL=0 permite daemon persistente
- ✅ Reducción de restarts innecesarios (>50%)

---

## Riesgos y Mitigaciones

### Riesgo 1: Daemon Zombie con TTL=0

**Probabilidad**: Media  
**Impacto**: Medio (consume recursos)

**Mitigación**:
- Comando `daemon list` para ver daemons activos
- Comando `daemon shutdown-all` para cleanup
- Warning en docs sobre TTL=0

### Riesgo 2: Keep-Alive Process Leak

**Probabilidad**: Baja  
**Impacto**: Bajo

**Mitigación**:
- PID tracking del keep-alive process
- Auto-stop cuando daemon muere
- Comando `daemon stop-keep-alive`

---

## Timeline

| Tarea | Duración |
|-------|----------|
| Agregar método ping | 30min |
| CLI daemon commands | 1h |
| TTL=0 support | 30min |
| Tests | 1h |
| Docs | 30min |
| **Total** | **~3.5h** |

---

## Próximos Pasos

1. ✅ Crear branch `feature/daemon-keepalive`
2. ⏳ Implementar método ping
3. ⏳ Crear CLI commands
4. ⏳ Agregar tests
5. ⏳ Merge a main

---

**Investigado**: 2026-01-05  
**Estado**: Listo para Implementación
