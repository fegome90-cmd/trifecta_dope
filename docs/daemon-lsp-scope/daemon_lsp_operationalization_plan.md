# Plan de Operacionalización: Subsistema Daemon + LSP

**Fecha**: 2026-03-22
**Input**: `docs/cloop_daemon_lsp_scope.md` (CLOOP scope completado)
**Estado**: Plan de implementación — sin código todavía

---

# 1. Veredicto

## Línea operacional recomendada

**DaemonManager + daemon run** es la línea oficial.

**Razones**:

- Es la única superficie con CLI funcional (`trifecta daemon start/stop/status/restart`)
- Es la única superficie con tests de integración (`tests/integration/daemon/test_daemon_manager.py`)
- Es la única superficie con health check (`platform/health.py`)
- Es la única superficie con telemetry events (`daemon_status` via Telemetry)
- Es la única superficie que el usuario puede invocar hoy

## Alternativas descartadas

| Alternativa | Razón de descarte |
|-------------|-------------------|
| LSPDaemonServer como línea oficial | No tiene CLI. No es invocado por ningún comando. No tiene health check integrado. Cambiar la línea oficial requeriría reescribir el CLI. |
| Crear un cuarto sistema | Prohibido por el marco de trabajo. Ya hay demasiada fragmentación. |
| LSPManager como línea oficial | Es un stub. `request_definition()` siempre retorna None. No es un sistema operativo. |

**Nota**: LSPDaemonServer y LSPClient NO se eliminan. Se integran como capability detrás de la superficie oficial. LSPDaemonServer queda como referencia de implementación, no como autoridad operacional.

---

# 2. Qué está sólido

Solo bases reales sobre las que se puede construir:

1. **DaemonManager.start() funciona**: Spawnea `daemon run` como subprocess, espera socket, escribe PID. Tests pasan.

2. **daemon run responde PING/HEALTH/SHUTDOWN**: Protocolo simple, funcional, con telemetry de uptime.

3. **LSPClient.start() funciona**: Spawnea pyright/pylsp, ejecuta handshake initialize/initialized, transiciona COLD→WARMING→READY. Tests pasan.

4. **daemon_paths.py valida AF_UNIX limits**: Paths cortos en /tmp, validación de base dir, validación de longitud.

5. **LSP contracts están bien diseñados**: CapabilityState, FallbackReason, ResponseState, Backend. Enum claros, métodos factory correctos. Listos para usar cuando se integre LSP.

6. **Tests de daemon existen**: `test_lsp_daemon.py` (5 tests), `test_daemon_manager.py`, `test_daemon_paths_constraints.py`, `test_cli_hardening.py`.

7. **Telemetry infrastructure existe**: Clase `Telemetry` con event(), incr(), observe(), flush(). Lista para emitir eventos del daemon.

---

# 3. Qué está blando/riesgoso/contradictorio

## Riesgos de implementación si se avanza sin cerrar contrato

1. **Health check contaminado por runtime.db** (P1): HealthChecker._check_db_accessible() requiere runtime.db que nadie crea. Si se avanza sin resolver ownership, health siempre será 66.67%. Esto genera falsa sensación de degradación.

2. **Protocolo daemon sin declaración formal** (P1): PING/HEALTH/SHUTDOWN funciona pero no hay contrato escrito. Si se agregan comandos LSP al protocolo sin definir el contrato primero, se introduce acoplamiento implícito.

3. **Race condition en singleton** (P1): DaemonManager.is_running() check + start() no es atómico. Dos `daemon start` simultáneos pueden crear dos procesos. Esto no se ha observado en tests pero es un riesgo real.

4. **DEFAULT_TTL inconsistente** (P2): lsp_daemon.py tiene dos definiciones (180 y 300). Si se integra LSPClient sin unificar, el TTL del daemon será ambiguo.

5. **Sin TTL en daemon run** (P2): daemon run corre indefinidamente. Si se integra LSP sin TTL, un LSP colgado mantendrá el daemon vivo indefinidamente.

6. **LSPDaemonServer no se elimina, se deja como referencia** (P2): Si no se documenta explícitamente que LSPDaemonServer no es autoridad, futuros desarrolladores podrían intentar usarlo directamente.

7. **Telemetry no cubre daemon run** (P2): daemon run no emite eventos de telemetry. Si se integra LSP sin telemetry, no habrá observabilidad de las requests LSP.

---

# 4. Plan propuesto por fases

## Fase 1: Contrato y autoridad

### Objetivo

Declarar formalmente cuál es la línea operacional, qué protocolo soporta, y qué artefactos son autoridad vs referencia.

### Cambios esperados

- Nuevo archivo `docs/daemon_contract.md` con contrato del protocolo daemon
- Actualización de `docs/CONTRACTS.md` para referenciar el contrato daemon
- Comentario en `src/infrastructure/lsp_daemon.py` indicando que NO es autoridad operacional

### Artefactos tocados

- `docs/daemon_contract.md` (nuevo)
- `docs/CONTRACTS.md` (actualización)
- `src/infrastructure/lsp_daemon.py` (comentario de no-autoridad)

### Riesgos

- Bajo. Solo documentación y comentarios.

### Criterio de "cerrado localmente"

- `docs/daemon_contract.md` existe y describe: protocolo PING/HEALTH/SHUTDOWN, paths, ownership de artefactos, estado de LSP (no integrado todavía).
- `lsp_daemon.py` tiene comentario claro indicando que no es la superficie oficial.

### Criterio de "cerrado técnicamente"

- El contrato es consistente con el comportamiento observado del daemon (PING→PONG, HEALTH→JSON, SHUTDOWN→OK).
- No hay contradicciones entre el contrato y el código.

### Qué NO se hará

- No se cambia código del daemon.
- No se integra LSP.
- No se modifica health check.

---

## Fase 2: Higiene operacional del daemon oficial

### Objetivo

Cerrar los huecos operacionales del daemon actual sin cambiar su funcionalidad.

### Cambios esperados

- Resolver ownership de runtime.db: o el daemon lo crea automáticamente, o health check deja de requerirlo
- Unificar DEFAULT_TTL en lsp_daemon.py (eliminar duplicación)
- Agregar TTL a daemon run (opcional, con default "infinito" para backward compat)
- Agregar telemetry events a daemon run (daemon_status events)

### Artefactos tocados

- `src/platform/health.py` (resolver runtime.db)
- `src/infrastructure/lsp_daemon.py` (unificar DEFAULT_TTL)
- `src/infrastructure/cli.py` daemon_run (agregar TTL opcional + telemetry)

### Riesgos

- Medio. Cambios en health check pueden afectar el score reportado.
- Cambiar DEFAULT_TTL puede afectar comportamiento si hay scripts que dependen del valor actual.

### Criterio de "cerrado localmente"

- Health check reporta 100% cuando daemon está corriendo (sin runtime.db hack manual).
- DEFAULT_TTL tiene un solo valor en lsp_daemon.py.
- daemon run emite telemetry events de daemon_status.

### Criterio de "cerrado técnicamente"

- Tests de health pasan con daemon corriendo.
- No hay regresiones en tests existentes.
- Telemetry events de daemon aparecen en events.jsonl.

### Qué NO se hará

- No se integra LSP.
- No se cambia el protocolo PING/HEALTH/SHUTDOWN.
- No se elimina LSPDaemonServer.

---

## Fase 3: Integración mínima LSP dentro del daemon oficial

### Objetivo

Conectar LSPClient detrás de daemon run para que el daemon pueda servir requests LSP.

### Cambios esperados

- daemon run importa y usa LSPClient
- Nuevo comando en el protocolo daemon: `LSP <method> <params_json>` (o variante JSON-RPC)
- daemon run spawnea LSPClient al inicio (o lazy on first LSP request)
- daemon run pasa requests LSP a LSPClient.request()
- Health check incluye estado LSP (COLD/WARMING/READY/FAILED)

### Artefactos tocados

- `src/infrastructure/cli.py` daemon_run (integrar LSPClient)
- `src/platform/health.py` (agregar check de LSP state)

### Riesgos

- Alto. Es el cambio más grande. Requiere que daemon run maneje dos concerns (socket server + LSP lifecycle).
- LSPClient spawnea pyright/pylsp que pueden no estar instalados. El daemon debe manejar graceful degradation.
- TTL del daemon debe considerar actividad LSP, no solo socket accepts.

### Criterio de "cerrado localmente"

- daemon run puede spawnear LSPClient cuando pyright/pylsp está instalado.
- daemon run responde a requests LSP con datos reales (hover, definition).
- daemon run responde con fallback explícito cuando LSP no está disponible (usando lsp_contracts.py).
- Health check reporta LSP state.

### Criterio de "cerrado técnicamente"

- Tests de integración pasan: daemon start → LSP request → respuesta válida.
- Telemetry events de lsp.request aparecen en events.jsonl.
- Fallback a AST funciona cuando LSP no está disponible.
- No hay memory leaks ni procesos zombis después de daemon stop.

### Qué NO se hará

- No se reemplaza daemon run con LSPDaemonServer.
- No se elimina LSPDaemonServer (queda como referencia).
- No se integra LSPManager.
- No se implementan todas las capabilities LSP (solo hover y definition como MVP).

---

## Fase 4: Poda/deprecación disciplinada

### Objetivo

Eliminar código muerto y marcar explícitamente lo que queda como referencia.

### Cambios esperados

- Marcar LSPManager como DEPRECATED con comentario claro
- Marcar LSPDaemonServer como REFERENCE IMPLEMENTATION (no eliminar, pero documentar que no es autoridad)
- Eliminar DEFAULT_TTL duplicado (ya resuelto en Fase 2)
- Si hay code paths muertos en lsp_daemon.py, marcarlos con TODO

### Artefactos tocados

- `src/application/lsp_manager.py` (comentario DEPRECATED)
- `src/infrastructure/lsp_daemon.py` (comentario REFERENCE IMPLEMENTATION)

### Riesgos

- Bajo. Solo comentarios y documentación.

### Criterio de "cerrado localmente"

- LSPManager tiene comentario DEPRECATED.
- LSPDaemonServer tiene comentario REFERENCE IMPLEMENTATION.
- No hay código muerto sin marcar.

### Criterio de "cerrado técnicamente"

- Tests existentes siguen pasando.
- No se eliminó código que alguien usa.

### Qué NO se hará

- No se elimina LSPManager (podría ser útil como referencia).
- No se elimina LSPDaemonServer (es referencia de implementación LSP completa).
- No se reescribe nada.

---

# 5. Orden de ejecución recomendado

```
Fase 1 (Contrato y autoridad)
    ↓
Fase 2 (Higiene operacional)
    ↓
Fase 3 (Integración LSP)
    ↓
Fase 4 (Poda/deprecación)
```

**Dependencias**:

- Fase 2 depende de Fase 1 (necesita contrato para saber qué corregir).
- Fase 3 depende de Fase 2 (necesita health limpio y TTL unificado para integrar LSP sin ambigüedad).
- Fase 4 depende de Fase 3 (necesita saber qué quedó vivo después de la integración).

**No se puede saltar fases**. Cada fase cierra un hueco que la siguiente necesita cerrado.

---

# 6. Riesgos de mala secuencia

## Si se parte por health (Fase 2 antes de Fase 1)

- Se corrige health check sin saber qué es "correcto". ¿runtime.db debe existir? ¿Es capability opcional? Sin contrato, se arriesga corregir en la dirección equivocada.
- Se pierde tiempo en higiene de un sistema que podría ser reemplazado si luego se decide que LSPDaemonServer es mejor línea oficial.

## Si se parte por LSP (Fase 3 antes de Fase 1 y 2)

- Se integra LSP sin contrato de protocolo. ¿Cómo se agregan comandos LSP al protocolo PING/HEALTH/SHUTDOWN? Sin contrato, se introduce acoplamiento implícito.
- Se integra LSP con health contaminado. Health reportará 66.67% incluso con LSP funcionando, generando confusión.
- Se integra LSP con DEFAULT_TTL inconsistente. ¿Cuál TTL aplica? ¿El de 180s o el de 300s?

## Si se parte por cleanup/refactor (Fase 4 antes de Fase 1, 2, 3)

- Se poda código que podría ser necesario para la integración LSP.
- Se marca como DEPRECATED algo que luego se necesita.
- Se pierde referencia de implementación antes de integrar la funcionalidad.

---

# 7. Siguiente paso recomendado

El entregable inmediato es un **ADR corto** que declare:

1. `DaemonManager + daemon run` es la línea operacional oficial del daemon.
2. `LSPClient` será integrado detrás de esa superficie en Fase 3.
3. `LSPDaemonServer` es referencia de implementación, no autoridad.
4. `LSPManager` queda fuera del camino feliz.
5. El protocolo daemon soportará PING/HEALTH/SHUTDOWN + comandos LSP (a definir en Fase 1).

**Archivo sugerido**: `docs/adr/ADR-008-daemon-lsp-official-line.md`

---

# 8. Prompt para agente implementador (Fase 1)

```
Tarea: Implementar Fase 1 del plan de operacionalización daemon+LSP.

Contexto: El scope CLOOP está en docs/cloop_daemon_lsp_scope.md. El plan está en docs/daemon_lsp_operationalization_plan.md.

Objetivo: Declarar formalmente la línea operacional del daemon.

Pasos:
1. Crear docs/daemon_contract.md con:
   - Protocolo PING/HEALTH/SHUTDOWN documentado (formato de request, formato de response)
   - Paths de artefactos (socket, pid, log) y su ownership
   - Estado actual de LSP (no integrado todavía, plan para Fase 3)
   - Health checks actuales y su significado
   - TTL behavior

2. Actualizar docs/CONTRACTS.md para referenciar docs/daemon_contract.md

3. Agregar comentario en src/infrastructure/lsp_daemon.py (inicio del archivo) indicando:
   - "REFERENCE IMPLEMENTATION: This module is not the official daemon surface."
   - "Official surface: DaemonManager + daemon run (see docs/daemon_contract.md)"
   - "This module is kept for reference and potential future use."

Reglas:
- No cambiar código funcional.
- No eliminar archivos.
- Solo documentación y comentarios.
- Citar evidencia del scope CLOOP cuando sea relevante.
- Mantener foco exclusivo en daemon + LSP.
