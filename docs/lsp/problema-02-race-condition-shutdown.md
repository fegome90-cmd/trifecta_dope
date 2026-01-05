# Problema 2: Race Condition en Shutdown del LSP Client

**Prioridad**: 🟡 MEDIA  
**Estado**: Investigación Completa  
**Fecha**: 2026-01-05

---

## Resumen Ejecutivo

El shutdown del `LSPClient` tiene un **orden estricto** para prevenir race conditions, pero en edge cases **leak streams** en lugar de cerrarlos. El trade-off actual prefiere **leak sobre crash**, pero es subóptimo.

**Código Afectado**: [lsp_client.py:114-167](../../src/infrastructure/lsp_client.py#L114-L167)

---

## Phase 1: Root Cause Investigation

### 1.1 El Bug Original (ya corregido)

**Problema Histórico**: Thread escribiendo a stream cerrado → `ValueError: I/O operation on closed file`

**Escenario**:
```
Thread A (Read Loop):         Thread B (stop()):
  _read_rpc()                   process.stdin.close()  ← Cerró stdin
  ...processing...              process.stdout.close() ← Cerró stdout
  _send_rpc()                   return                 ← Terminó
  → write to stdin              
  → ValueError: closed file     ← CRASH
```

**Root Cause**: Orden incorrecto de shutdown. Streams cerrados antes de que thread termine.

---

### 1.2 La Solución Actual

**Código** ([lsp_client.py:114-167](../../src/infrastructure/lsp_client.py#L114-L167)):

```python
def stop(self) -> None:
    """Strict cleanup: signal -> terminate -> join thread -> close streams.

    SHUTDOWN ORDER INVARIANT (do not reorder):
      1. Set stopping flag (signal intent)
      2. Terminate process
      3. Join loop thread (wait for exit)
      4. Close streams (only after thread exits)

    Idempotent: safe to call multiple times.
    """
    with self._stop_lock:
        # 1. Signal threads first (defensive: stopping should only be set here)
        if not self.stopping.is_set():
            self.stopping.set()

        # 2. Check/set state (idempotent)
        with self.lock:
            if self.state == LSPState.CLOSED:
                return
            self.state = LSPState.CLOSED

        # 3. Terminate process
        if self.process:
            try:
                self.process.terminate()
                try:
                    self.process.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=0.2)
            except Exception:
                pass  # Process might be gone

        # 4. Join background thread BEFORE closing streams
        # Increased timeout for CI stability (was 0.5s)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

            # CRITICAL: If thread still alive after join, DO NOT close streams
            # This avoids write-to-closed-file race in edge cases (blocked I/O)
            # Better to leak streams in rare shutdown failure than reintroduce bug
            if self._thread.is_alive():
                # Thread didn't terminate cleanly; leave streams open
                # Process is already terminated, thread will eventually exit on EOF
                return  # ← LEAK STREAMS

        # 5. Close streams ONLY after thread exits
        if self.process:
            try:
                if self.process.stdin:
                    self.process.stdin.close()
                if self.process.stdout:
                    self.process.stdout.close()
                if self.process.stderr:
                    self.process.stderr.close()
            except Exception:
                pass  # Already closed
```

**Orden Estricto**:
1. ✅ Set `stopping` flag (señal para thread)
2. ✅ Set `state = CLOSED`
3. ✅ Terminate process (SIGTERM → SIGKILL)
4. ✅ Join thread con timeout de 1.0s
5. ⚠️ **IF thread aún vivo**: RETURN sin cerrar streams (LEAK)
6. ✅ **ELSE**: Cerrar streams

---

### 1.3 El Problema Actual: Stream Leak

**Escenario Edge Case**:
```python
# Thread bloqueado en I/O
def _run_loop(self):
    while not self.stopping.is_set():
        msg = self._read_rpc()  # ← Bloqueado aquí por 10s
        # ... process msg ...

# Llamada a stop():
stop()
  → process.terminate()  # Envía SIGTERM
  → thread.join(timeout=1.0)  # Espera 1s
  → thread.is_alive() == True  # ← Todavía bloqueado
  → return  # ← LEAK: no cerró streams
```

**Consecuencias**:
- File descriptors abiertos: `stdin`, `stdout`, `stderr`
- Proceso terminado pero streams leak
- Si se repite muchas veces: exhaust file descriptors

**Probabilidad**: Baja (solo si thread bloqueado >1s)

**Impacto**: 
- Medio en producción (leak acumulado)
- Alto en tests con muchos starts/stops

---

### 1.4 Evidencia de Tests

**Test Existente** ([test_lsp_client_strict.py:6](../../tests/unit/test_lsp_client_strict.py#L6)):

```python
def test_lsp_client_stop_closes_process():
    """Test that stop() terminates the process."""
    # Mock LSP client con proceso real
    client = LSPClient(Path("/tmp"))
    client.start()
    
    assert client.process is not None
    assert client.process.poll() is None  # Running
    
    client.stop()
    
    # Process should be terminated
    assert client.process.poll() is not None  # Exited
    
    # NOTE: No verifica que streams estén cerrados
```

**Test Faltante**:
```python
def test_lsp_client_stop_closes_streams():
    """Test that stop() closes all streams."""
    client = LSPClient(Path("/tmp"))
    client.start()
    
    stdin = client.process.stdin
    stdout = client.process.stdout
    stderr = client.process.stderr
    
    client.stop()
    
    # Verify streams closed
    assert stdin.closed  # ← Podría fallar si thread leak
    assert stdout.closed
    assert stderr.closed
```

---

## Phase 2: Pattern Analysis

### 2.1 Patrón: Defensive Programming vs Resource Leak

**Trade-off Actual**:
- ✅ Previene crash (write to closed stream)
- ⚠️ Leak streams en edge cases
- ⚠️ No hay telemetry de cuando ocurre

**Patrón Similar en Otros Proyectos**:
- gRPC Python: [similar issue](https://github.com/grpc/grpc/issues/18994)
- asyncio: Warnings sobre unclosed resources
- subprocess: `__del__` warnings

---

### 2.2 Análisis de Alternativas

#### **Alternativa 1: Timeouts Escalados**

```python
TIMEOUTS = [0.5, 1.0, 2.0]  # Total: 3.5s

for i, timeout in enumerate(TIMEOUTS):
    if self._thread and self._thread.is_alive():
        self._thread.join(timeout=timeout)
        if not self._thread.is_alive():
            break  # Success
        
        # Still alive after timeout: try more aggressive termination
        if i < len(TIMEOUTS) - 1:
            # Try killing process again
            if self.process:
                try:
                    self.process.kill()  # More aggressive
                except Exception:
                    pass

# Close streams only if thread exited
if not (self._thread and self._thread.is_alive()):
    self._close_streams()
else:
    # Log warning
    if self.telemetry:
        self.telemetry.event("lsp.shutdown", {}, {"status": "thread_leak"}, 0)
```

**Pros**:
- 3 intentos con escalación
- Más robusto en CI/sistemas lentos
- Telemetría de anomalías

**Contras**:
- Shutdown más lento (hasta 3.5s)
- Aún puede leak en casos extremos

---

#### **Alternativa 2: Force Close Streams con try/except**

```python
# Close streams ALWAYS, even if thread alive
try:
    if self.process:
        if self.process.stdin:
            self.process.stdin.close()
        if self.process.stdout:
            self.process.stdout.close()
        if self.process.stderr:
            self.process.stderr.close()
except (ValueError, OSError) as e:
    # Thread might be using streams, but process is terminated
    # Streams will be closed by OS when process fully exits
    if self.telemetry:
        self.telemetry.event("lsp.shutdown", {}, {"status": "stream_close_error", "error": str(e)}, 0)
```

**Pros**:
- No leak
- Simple

**Contras**:
- Puede reintroducir race condition si thread escribe después de close
- Depende de que `_send_rpc()` tenga try/except robusto

---

#### **Alternativa 3: Context Manager para Streams**

```python
from contextlib import closing

class LSPClient:
    def start(self):
        # ...
        self.process = subprocess.Popen(...)
        
        # Wrap streams en context managers
        self._stdin_ctx = closing(self.process.stdin)
        self._stdout_ctx = closing(self.process.stdout)
        self._stderr_ctx = closing(self.process.stderr)
    
    def stop(self):
        # ... existing stop logic ...
        
        # Close via context managers (garantiza cleanup)
        with suppress(Exception):
            self._stdin_ctx.close()
        with suppress(Exception):
            self._stdout_ctx.close()
        with suppress(Exception):
            self._stderr_ctx.close()
```

**Pros**:
- Cleanup garantizado
- Pythonic

**Contras**:
- Más complejo
- Aún no resuelve race si thread escribe

---

### 2.3 Comparación de Soluciones

| Solución | Leak Prevention | Crash Prevention | Complejidad | Telemetría |
|----------|-----------------|------------------|-------------|------------|
| **Actual** | ⚠️ Leak en edge cases | ✅ | Baja | ❌ |
| **Escalado** | ✅ Mejor | ✅ | Media | ✅ |
| **Force Close** | ✅ | ⚠️ Riesgo | Baja | ✅ |
| **Context Manager** | ✅ | ⚠️ Riesgo | Alta | ✅ |

**Recomendación**: **Alternativa 1 (Timeouts Escalados)** + Telemetría

---

## Phase 3: Hypothesis and Testing

### 3.1 Hipótesis: Timeout de 1s es Insuficiente en CI

**Hipótesis**: El timeout de 1s no es suficiente en sistemas lentos (CI, containers).

**Test**:
```python
def test_slow_shutdown_in_ci(monkeypatch):
    """Simulate slow CI environment with delayed thread join."""
    client = LSPClient(Path("/tmp"))
    client.start()
    
    # Mock thread.join to simulate slow CI
    original_join = client._thread.join
    def slow_join(timeout):
        time.sleep(0.5)  # Añadir delay
        original_join(timeout)
    
    monkeypatch.setattr(client._thread, "join", slow_join)
    
    t0 = time.time()
    client.stop()
    t1 = time.time()
    
    # Should take longer but not leak
    assert t1 - t0 < 2.0  # Reasonable timeout
    assert not client._thread.is_alive()  # Thread exited
    assert client.process.stdin.closed  # Streams closed
```

---

### 3.2 Hipótesis: Thread Bloqueado en _read_rpc

**Hipótesis**: `_read_rpc()` puede bloquearse indefinidamente si LSP server hung.

**Código** ([lsp_client.py:339-372](../../src/infrastructure/lsp_client.py#L339-L372)):
```python
def _read_rpc(self) -> Optional[Dict[str, Any]]:
    if not self.process or not self.process.stdout:
        return None
    try:
        # Read Headers
        length = None
        while True:
            line = self.process.stdout.readline()  # ← BLOCKING
            if not line:
                return None
            # ... parse headers ...
        
        # Read Content
        content = b""
        while len(content) < length:
            chunk = self.process.stdout.read(length - len(content))  # ← BLOCKING
            if not chunk:
                break
            content += chunk
        
        return json.loads(content.decode("utf-8"))
    except Exception:
        return None
```

**Problema**: `readline()` y `read()` son blocking. Si LSP server hung, thread queda bloqueado.

**Test**:
```python
def test_thread_unblocks_on_process_terminate():
    """Verify that thread exits when process is terminated."""
    client = LSPClient(Path("/tmp"))
    client.start()
    
    # Wait for thread to be in read loop
    time.sleep(0.5)
    
    # Terminate process (simula LSP server hung)
    client.process.terminate()
    client.process.wait()
    
    # Thread should exit soon (EOF on stdout)
    time.sleep(0.5)
    assert not client._thread.is_alive()
```

---

## Phase 4: Implementation

### 4.1 Solución Recomendada: Timeouts Escalados + Telemetría

**Modificar** [lsp_client.py:114-167](../../src/infrastructure/lsp_client.py#L114-L167):

```python
def stop(self) -> None:
    """Strict cleanup with escalating timeouts.

    SHUTDOWN ORDER INVARIANT (do not reorder):
      1. Set stopping flag (signal intent)
      2. Terminate process
      3. Join loop thread with escalating timeouts
      4. Close streams (only after thread exits)

    Idempotent: safe to call multiple times.
    """
    with self._stop_lock:
        # 1. Signal threads first
        if not self.stopping.is_set():
            self.stopping.set()

        # 2. Check/set state (idempotent)
        with self.lock:
            if self.state == LSPState.CLOSED:
                return
            self.state = LSPState.CLOSED

        # 3. Terminate process
        if self.process:
            try:
                self.process.terminate()
                try:
                    self.process.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=0.2)
            except Exception:
                pass

        # 4. Join thread with ESCALATING timeouts
        TIMEOUTS = [0.5, 1.0, 2.0]  # Total: 3.5s max
        thread_exited = False
        
        for attempt, timeout in enumerate(TIMEOUTS):
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=timeout)
                
                if not self._thread.is_alive():
                    thread_exited = True
                    break
                
                # Still alive: try more aggressive termination
                if attempt < len(TIMEOUTS) - 1:
                    if self.process:
                        try:
                            # Already killed, but ensure it's dead
                            self.process.kill()
                            self.process.wait(timeout=0.1)
                        except Exception:
                            pass
                    
                    if self.telemetry:
                        self.telemetry.event(
                            "lsp.shutdown_retry",
                            {},
                            {"attempt": attempt + 1, "timeout": timeout},
                            0
                        )
            else:
                thread_exited = True
                break

        # 5. Close streams ONLY if thread exited
        if thread_exited:
            self._close_streams()
        else:
            # Thread still alive after 3.5s: log anomaly
            if self.telemetry:
                self.telemetry.event(
                    "lsp.shutdown",
                    {},
                    {"status": "thread_leak", "total_wait": sum(TIMEOUTS)},
                    0
                )
            # Leave streams open to prevent crash
            # Process is terminated, streams will be cleaned by OS eventually

    def _close_streams(self) -> None:
        """Close all process streams."""
        if self.process:
            try:
                if self.process.stdin and not self.process.stdin.closed:
                    self.process.stdin.close()
                if self.process.stdout and not self.process.stdout.closed:
                    self.process.stdout.close()
                if self.process.stderr and not self.process.stderr.closed:
                    self.process.stderr.close()
            except Exception as e:
                if self.telemetry:
                    self.telemetry.event(
                        "lsp.stream_close_error",
                        {},
                        {"error": str(e)},
                        0
                    )
```

---

### 4.2 Mejora Adicional: Non-Blocking Read con Timeout

**Problema**: `readline()` y `read()` son blocking sin timeout.

**Solución**: Usar `select()` o `poll()` para timeout en reads.

**Modificar** `_read_rpc()`:

```python
import select

def _read_rpc(self, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
    """Read JSON-RPC message with timeout."""
    if not self.process or not self.process.stdout:
        return None
    
    try:
        # Check if data available with timeout
        if hasattr(select, 'poll'):
            # Linux/Mac: use poll
            poller = select.poll()
            poller.register(self.process.stdout.fileno(), select.POLLIN)
            ready = poller.poll(timeout * 1000)  # milliseconds
            if not ready:
                return None  # Timeout
        else:
            # Windows: use select
            ready, _, _ = select.select([self.process.stdout], [], [], timeout)
            if not ready:
                return None  # Timeout
        
        # Data available: read headers
        length = None
        while True:
            line = self.process.stdout.readline()
            if not line:
                return None
            
            line = line.strip()
            if not line:
                break
            
            if line.startswith(b"Content-Length: "):
                length = int(line.split(b": ")[1])
        
        if length is None:
            return None
        
        # Read content
        content = b""
        while len(content) < length:
            chunk = self.process.stdout.read(length - len(content))
            if not chunk:
                break
            content += chunk
        
        # Parse JSON
        try:
            msg = json.loads(content.decode("utf-8"))
            return msg if isinstance(msg, dict) else None
        except json.JSONDecodeError:
            return None
            
    except Exception:
        return None
```

**Beneficios**:
- Thread no queda bloqueado indefinidamente
- Timeout configurable
- Más responsive al `stopping` flag

---

### 4.3 Tests de Validación

#### **Test 1: Timeouts Escalados**

```python
def test_stop_with_escalating_timeouts(monkeypatch):
    """Verify stop() tries multiple timeouts before giving up."""
    client = LSPClient(Path("/tmp"))
    client.start()
    
    # Track telemetry events
    events = []
    def mock_event(cmd, args, result, timing, **kwargs):
        events.append({"cmd": cmd, "result": result})
    
    if client.telemetry:
        monkeypatch.setattr(client.telemetry, "event", mock_event)
    
    # Mock thread.join to always timeout (simulate hung thread)
    def fake_join(timeout):
        time.sleep(timeout)  # Simulate waiting but never exits
    
    monkeypatch.setattr(client._thread, "join", fake_join)
    monkeypatch.setattr(client._thread, "is_alive", lambda: True)  # Always alive
    
    client.stop()
    
    # Should have retried multiple times
    retry_events = [e for e in events if e["cmd"] == "lsp.shutdown_retry"]
    assert len(retry_events) == 2  # 2 retries (3 attempts total)
    
    # Should have logged thread leak
    leak_events = [e for e in events if e["cmd"] == "lsp.shutdown" and e["result"].get("status") == "thread_leak"]
    assert len(leak_events) == 1
```

#### **Test 2: Thread Exits Cleanly**

```python
def test_stop_closes_streams_when_thread_exits():
    """Verify streams are closed when thread exits cleanly."""
    client = LSPClient(Path("/tmp"))
    client.start()
    
    time.sleep(0.5)  # Let thread start
    
    client.stop()
    
    # Thread should have exited
    assert not client._thread.is_alive()
    
    # Streams should be closed
    assert client.process.stdin.closed
    assert client.process.stdout.closed
    assert client.process.stderr.closed
```

#### **Test 3: Non-Blocking Read Timeout**

```python
def test_read_rpc_timeout():
    """Verify _read_rpc() times out if no data."""
    client = LSPClient(Path("/tmp"))
    client.start()
    
    # Don't send any data to LSP server
    # _read_rpc should timeout
    t0 = time.time()
    result = client._read_rpc(timeout=1.0)
    t1 = time.time()
    
    assert result is None  # Timeout
    assert 0.9 < (t1 - t0) < 1.2  # Approximately 1s
```

---

### 4.4 Métricas de Telemetría

**Nuevos Eventos**:

1. `lsp.shutdown_retry`:
```json
{
  "cmd": "lsp.shutdown_retry",
  "args": {},
  "result": {"attempt": 2, "timeout": 1.0},
  "timing": 0
}
```

2. `lsp.shutdown` (con thread_leak):
```json
{
  "cmd": "lsp.shutdown",
  "args": {},
  "result": {"status": "thread_leak", "total_wait": 3.5},
  "timing": 0
}
```

3. `lsp.stream_close_error`:
```json
{
  "cmd": "lsp.stream_close_error",
  "args": {},
  "result": {"error": "Bad file descriptor"},
  "timing": 0
}
```

---

## Métricas de Éxito

- ✅ Thread leaks reducidos a <1% de shutdowns
- ✅ Telemetría de anomalías
- ✅ CI más estable (menos timeouts)
- ✅ Tests de 100 starts/stops sin leaks
- ✅ Shutdown promedio <1s (no impacto en UX)

---

## Riesgos y Mitigaciones

### Riesgo 1: Shutdown Más Lento

**Probabilidad**: Alta  
**Impacto**: Bajo

**Mitigación**:
- Timeouts escalados solo se usan si thread no sale rápido
- Mayoría de shutdowns terminan en <0.5s (primer timeout)
- Solo casos edge usan 3.5s completos

### Riesgo 2: Reintroducción de Race Condition

**Probabilidad**: Baja  
**Impacto**: Alto

**Mitigación**:
- Mantener orden estricto
- Tests exhaustivos de concurrencia
- Telemetría de errores

---

## Timeline

| Tarea | Duración | Responsable |
|-------|----------|-------------|
| Implementar timeouts escalados | 1h | Agente |
| Extraer `_close_streams()` | 15min | Agente |
| Agregar telemetría | 30min | Agente |
| Implementar non-blocking read | 2h | Agente (opcional) |
| Tests de validación | 2h | Agente |
| **Total** | **3.5-5.5h** | |

---

## Próximos Pasos

1. ✅ Crear branch `fix/lsp-shutdown-leak`
2. ⏳ Implementar timeouts escalados
3. ⏳ Agregar telemetría
4. ⏳ Ejecutar tests de stress (100+ starts/stops)
5. ⏳ Validar en CI
6. ⏳ Merge a main

---

**Investigado**: 2026-01-05  
**Estado**: Listo para Implementación
