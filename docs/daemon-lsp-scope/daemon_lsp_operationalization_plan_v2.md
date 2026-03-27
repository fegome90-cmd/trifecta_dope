# Plan de Operacionalización v2: Subsistema Daemon + LSP

**Fecha**: 2026-03-22
**Input**: `docs/daemon-lsp-scope/cloop_daemon_lsp_scope.md`
**Estado**: Plan ejecutable — sin código todavía
**Línea oficial**: `DaemonManager + daemon run`

---

# 1. Veredicto

## Línea operacional recomendada

**DaemonManager + daemon run** es la línea oficial.

**Alternativas descartadas**:

- `LSPDaemonServer`: No tiene CLI. No es invocado por ningún comando oficial. Queda como referencia.
- `LSPManager`: Stub. `request_definition()` siempre retorna None. Queda fuera del camino feliz.
- Cuarto sistema: Prohibido. Ya hay demasiada fragmentación.

**Integración LSP**: `LSPClient` se conectará detrás de `daemon run`. No se crea nueva superficie.

---

# 2. Qué está sólido

1. `DaemonManager.start()` funciona: spawnea subprocess, espera socket, escribe PID. Tests pasan.
2. `daemon run` responde PING/HEALTH/SHUTDOWN. Protocolo simple, funcional.
3. `LSPClient.start()` funciona: spawnea pyright/pylsp, handshake, state machine. Tests pasan.
4. `daemon_paths.py` valida AF_UNIX limits correctamente.
5. `lsp_contracts.py` tiene enums y métodos factory listos para usar.
6. Tests de daemon existen y pasan: `test_lsp_daemon.py`, `test_daemon_manager.py`, `test_daemon_paths_constraints.py`.
7. `Telemetry` infrastructure existe y funciona.

---

# 3. Qué está blando/riesgoso/contradictorio

1. **runtime.db sin ownership**: Health check lo requiere pero nadie lo crea. Hipótesis a validar (ver Fase 2).
2. **Protocolo sin envelope formal**: PING/HEALTH/SHUTDOWN funciona pero no hay contrato escrito con envelope JSON-RPC ni similar.
3. **Race condition singleton**: `DaemonManager.is_running()` + `start()` no es atómico.
4. **DEFAULT_TTL duplicado**: `lsp_daemon.py` línea 30 (180) y línea 262 (300).
5. **daemon run sin TTL**: Corre indefinidamente hasta SIGTERM.
6. **daemon run sin telemetry**: No emite eventos.
7. **LSP nunca servido**: El daemon oficial no puede servir requests LSP.

---

# 4. Plan v2 por fases

## Tabla de verdad mínima

| Estado | Definición | Cómo se verifica |
|--------|------------|------------------|
| **running** | Proceso vivo + socket existe + PID válido | `os.kill(pid, 0)` no falla + socket_path.exists() |
| **ready** | running + responde HEALTH con JSON válido | Conectar al socket, enviar HEALTH, recibir JSON con status ok |
| **failed** | Proceso no vivo O socket no existe | `os.kill(pid, 0)` falla O socket_path no existe |
| **degraded** | ready + LSP no disponible (Fase 3+) | PING OK pero LSP state ≠ READY |

## Matriz de ownership mínima

| Artefacto | Owner | Create | Read | Cleanup | Liveness |
|-----------|-------|--------|------|---------|----------|
| socket | DaemonManager | `start()` | `status()` | `_cleanup_files()` | SÍ |
| pid | DaemonManager | `start()` | `status()` | `_cleanup_files()` | SÍ |
| log | DaemonManager | `start()` (append) | Manual | NO auto | NO |
| runtime.db | N/A (chequeo mal modelado, eliminar de health) | N/A | N/A | N/A | NO |
| singleton | socket bind (implícito) | `start()` (bind) | `start()` (bind fail) | `_cleanup_files()` | SÍ |

---

## Fase 1: Autoridad + tabla de verdad

### Objetivo

Declarar formalmente la línea operacional, el protocolo, y la tabla de verdad. Sin cambios de código.

### Artefactos tocados

- `docs/daemon-lsp-scope/daemon_contract.md` (nuevo)
- `docs/CONTRACTS.md` (referencia)
- `src/infrastructure/lsp_daemon.py` (comentario: REFERENCE, no autoridad)
- `src/application/lsp_manager.py` (comentario: STUB, fuera de camino feliz)

### Decisiones previas requeridas

- Ninguna. Solo documentación.

### Criterio de cerrado localmente

- `daemon_contract.md` existe con: protocolo PING/HEALTH/SHUTDOWN documentado, tabla de verdad, matriz de ownership, estado LSP (no integrado).
- `lsp_daemon.py` tiene comentario REFERENCE IMPLEMENTATION.
- `lsp_manager.py` tiene comentario STUB.

### Criterio de cerrado técnicamente

- Contrato es verificable contra comportamiento observado (PING→PONG, HEALTH→JSON).
- No hay contradicciones entre contrato y código.

### No-objetivos

- No cambiar código funcional.
- No integrar LSP.
- No modificar health check.

---

## Fase 2: Veracidad operacional del daemon oficial

### Objetivo

Cerrar los huecos que impiden que el daemon reporte estado veraz. Resolver la hipótesis de runtime.db.

### Hipótesis a validar sobre runtime.db

**Pregunta**: ¿runtime.db es requisito de readiness, capability secundaria, o chequeo mal modelado?

**Validación**:

1. Buscar en código quién lee runtime.db después de crearlo.
2. Si nadie lo lee para funcionalidad core → es **chequeo mal modelado**. Eliminar del health check.
3. Si alguien lo lee para funcionalidad secundaria → es **capability secundaria**. Health check debe marcarlo como degraded, no failed.
4. Si el daemon lo necesita para arrancar → es **requisito de readiness**. Daemon debe crearlo automáticamente.

**Decisión**: Eliminar check de runtime.db del health check. Evidencia del scope CLOOP: `trifecta index` crea `search.db`, no `runtime.db`. HealthChecker es el único lector. → Es **chequeo mal modelado**.

### Artefactos tocados

- `src/platform/health.py` (eliminar check de runtime.db: es chequeo mal modelado, nadie lo lee para funcionalidad core)
- `src/infrastructure/lsp_daemon.py` (unificar DEFAULT_TTL a un solo valor)
- `src/infrastructure/cli.py` daemon_run (agregar telemetry events de daemon_status)

### Decisiones previas requeridas

- Fase 1 completada (contrato existe).
- Decisión sobre runtime.db (requiere validación de código).

### Criterio de cerrado localmente

- Health check no incluye runtime.db.
- DEFAULT_TTL tiene un solo valor en lsp_daemon.py.
- daemon run emite al menos un event de telemetry `daemon_status`.

### Criterio de cerrado técnicamente

- Tests de health pasan con daemon corriendo sin intervención manual.
- No hay regresiones en tests existentes.
- Telemetry event aparece en events.jsonl después de daemon start.

### No-objetivos

- No integrar LSP.
- No cambiar el protocolo PING/HEALTH/SHUTDOWN.
- No eliminar LSPDaemonServer.

---

## Fase 3: Costura de integración LSP

### Objetivo

Conectar LSPClient detrás de daemon run. El daemon debe poder servir requests LSP con envelope formal.

### Requisito de envelope formal

El protocolo daemon actual (PING/HEALTH/SHUTDOWN) se extiende con un envelope JSON para LSP:

```
→ {"method": "lsp/hover", "params": {"uri": "...", "line": 0, "col": 0}}
← {"status": "ok", "data": {...}} o {"status": "error", "message": "..."}
```

**No se inventa protocolo ad hoc**. Se usa JSON sobre el socket existente, consistente con el estilo de HEALTH (que ya devuelve JSON).

### Artefactos tocados

- `src/infrastructure/cli.py` daemon_run (importar LSPClient, manejar envelope JSON, delegar a LSPClient.request())

### Decisiones previas requeridas

- Fase 1 completada (contrato define extensiones).
- Fase 2 completada (health limpio, telemetry activo).
- Decisión sobre: ¿spawn LSP al inicio o lazy on first request?

### Criterio de cerrado localmente

- daemon run puede spawnear LSPClient cuando pyright/pylsp está instalado.
- daemon run responde a `{"method": "lsp/hover", ...}` con datos reales del LSP.
- daemon run responde con fallback explícito cuando LSP no está disponible (usando lsp_contracts.py).
- Estado degraded se reporta cuando LSP no está READY.

### Criterio de cerrado técnicamente

- Test de integración: daemon start → enviar envelope LSP → recibir respuesta válida.
- Telemetry events de `lsp.request` aparecen en events.jsonl.
- No hay procesos zombis después de daemon stop.
- Fallback funciona: si pyright no instalado, daemon responde con CapabilityState.DEGRADED.

### Criterio de cerrado técnicamente (adicional)

- daemon detecta LSP state FAILED y responde con CapabilityState.DEGRADED en vez de colgar.
- No hay procesos zombis después de daemon stop.

### No-objetivos

- No reemplazar daemon run con LSPDaemonServer.
- No integrar LSPManager.
- No implementar todas las capabilities LSP (solo hover y definition como MVP).
- No eliminar LSPDaemonServer.

---

## Fase 4: Hardening + observabilidad

### Objetivo

Cerrar race conditions, agregar observabilidad, y asegurar que el daemon es operable sin sorpresas.

### Artefactos tocados

- `src/platform/daemon_manager.py` (singleton locking: file lock o socket bind check atómico)
- `src/infrastructure/cli.py` daemon_run (agregar TTL opcional via env var o flag)

### Decisiones previas requeridas

- Fase 3 completada (daemon sirve LSP).
- Decisión sobre: ¿file lock o socket bind como mecanismo de singleton?

### Criterio de cerrado localmente

- Dos `daemon start` simultáneos no crean dos procesos.
- daemon run respeta TTL si se configura.
- Telemetry cubre: daemon_status, lsp.request, lsp.fallback.

### Criterio de cerrado técnicamente

- Test de concurrencia: dos starts simultáneos → solo uno queda vivo.
- TTL funciona: daemon se apaga después del período configurado.
- No hay regresiones.

### No-objetivos

- No cambiar el protocolo.
- No reescribir LSPClient.
- No eliminar código.

---

## Fase 5: Deprecación/poda

### Objetivo

Marcar explícitamente el código que no es autoridad. No eliminar nada.

### Artefactos tocados

- `src/application/lsp_manager.py` (comentario DEPRECATED al inicio del archivo)
- `src/infrastructure/lsp_daemon.py` (comentario ya puesto en Fase 1, verificar consistencia)

### Decisiones previas requeridas

- Fases 1-4 completadas.

### Criterio de cerrado localmente

- LSPManager tiene comentario DEPRECATED.
- LSPDaemonServer tiene comentario REFERENCE IMPLEMENTATION (verificado).
- No hay código muerto sin marcar.

### Criterio de cerrado técnicamente

- Tests existentes siguen pasando.
- No se eliminó código que alguien usa.

### No-objetivos

- No eliminar LSPManager.
- No eliminar LSPDaemonServer.
- No reescribir nada.

---

# 5. Orden de ejecución

```
Fase 1 (Autoridad + tabla de verdad)
    ↓
Fase 2 (Veracidad operacional)
    ↓
Fase 3 (Costura LSP)
    ↓
Fase 4 (Hardening)
    ↓
Fase 5 (Deprecación)
```

**Dependencias**:

- Fase 2 necesita Fase 1: contrato define qué es "correcto" para health.
- Fase 3 necesita Fase 2: health limpio + telemetry activo para integrar LSP sin ambigüedad.
- Fase 4 necesita Fase 3: hardening de un daemon que ya sirve LSP.
- Fase 5 necesita Fases 1-4: saber qué quedó vivo para marcar correctamente.

**No se puede saltar fases**.

---

# 6. Riesgos de mala secuencia

## Partir por health (Fase 2 antes de Fase 1)

- Se corrige health sin saber qué es "correcto". Sin contrato, se arriesga corregir en la dirección equivocada.
- Se pierde tiempo en higiene de un sistema que podría tener su línea oficial redefinida.

## Partir por LSP (Fase 3 antes de Fase 1 y 2)

- Se integra LSP sin contrato de protocolo. ¿Cómo se agregan comandos LSP? Sin envelope formal, se introduce acoplamiento implícito.
- Se integra LSP con health contaminado. Health reportará degraded permanente, generando confusión.
- Se integra LSP con DEFAULT_TTL inconsistente. Ambigüedad sobre qué TTL aplica.

## Partir por cleanup (Fase 5 antes de Fase 1-4)

- Se poda código que podría ser necesario para la integración LSP.
- Se marca como DEPRECATED algo que luego se necesita.
- Se pierde referencia de implementación antes de integrar la funcionalidad.

---

# 7. Siguiente paso recomendado

**Implementar Fase 1**: Crear `docs/daemon-lsp-scope/daemon_contract.md` con:

- Protocolo PING/HEALTH/SHUTDOWN documentado (formato request/response)
- Tabla de verdad (running/ready/failed/degraded)
- Matriz de ownership (socket/pid/log/runtime.db/locks)
- Estado LSP actual (no integrado, plan para Fase 3)

**Agregar comentarios** en:

- `src/infrastructure/lsp_daemon.py`: REFERENCE IMPLEMENTATION
- `src/application/lsp_manager.py`: STUB / OUT OF HAPPY PATH

**Sin cambios de código funcional**. Solo documentación y comentarios.
