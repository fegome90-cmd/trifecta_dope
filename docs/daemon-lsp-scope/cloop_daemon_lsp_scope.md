# CLOOP Scope: Subsistema Daemon + LSP de Trifecta

**Fecha**: 2026-03-22
**Método**: CLOOP (Clarify → Layout → Operate → Observe → Reflect)
**Evidencia**: Código fuente del repo `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope`

## Skills relevantes encontrados con skill-hub

| Skill | Relevancia | Nota |
|-------|-----------|------|
| `python-cli-patterns` | **ALTA** | Patrones Typer/Rich para CLI del daemon. Contiene error handling, command groups, Rich output — aplicable a `daemon run` y comandos daemon. |
| `pm2-monitor` | BAJA | PM2/Node.js, no aplica a Python |
| `trifecta-daemon` | NINGUNA | Fantasma — indexado sin SKILL.md |
| `trifecta-global-usage` | NINGUNA | Fantasma — indexado sin SKILL.md |

---

# 1. Clarify

## Preguntas cerradas por evidencia

### ¿Qué problema exacto intenta resolver el daemon hoy?

**Evidencia**: El daemon tiene DOS propósitos declarados en código:

1. `LSPDaemonServer` (`src/infrastructure/lsp_daemon.py`): Mantener un proceso pyright/pylsp vivo para reutilizar entre requests, evitando el cold-start del LSP (~500ms por spawn).
2. `DaemonManager` (`src/platform/daemon_manager.py`): Servir como runtime manager para index/query operations con un protocolo simple PING/HEALTH/SHUTDOWN.

**Contradicción**: Los dos sistemas no comparten protocolo, paths ni propósito real. El CLI `daemon run` implementa un TERCER protocolo inline que no usa ninguno de los dos.

### ¿Cuál es su unidad operacional real?

**LSPDaemonServer**: Proceso UNIX daemon con socket AF_UNIX, fcntl locking, TTL, y LSPClient embebido que spawnea pyright/pylsp por stdio.

**DaemonManager**: Proceso UNIX daemon con socket AF_UNIX en runtime_dir, protocolo simple, sin LSP.

**daemon run (CLI)**: Proceso UNIX daemon inline con protocolo PING/HEALTH/SHUTDOWN hardcodeado, sin LSP, sin relación con los otros dos.

### ¿Qué rol exacto cumple el LSP dentro del sistema?

**Evidencia en `src/infrastructure/lsp_client.py`**: El LSPClient spawnea pyright o pylsp, maneja estado COLD→WARMING→READY→FAILED→CLOSED, ejecuta handshake initialize/initialized, y sirve requests textDocument/definition y textDocument/hover.

**Evidencia en `src/application/lsp_manager.py`**: LSPManager es una tercera implementación que spawnea pyright con `--outputjson`, tiene su propio state machine COLD→WARMING→READY→FAILED, y marca READY cuando recibe publishDiagnostics.

**Contradicción**: LSPManager.request_definition() tiene un `_request_with_timeout` que dice "Would read from stdout here in real implementation / For MVP: return mock response or None". Esto significa que **NUNCA devuelve datos reales**.

### ¿Daemon y LSP son el mismo sistema, capas distintas o un acoplamiento parcial?

**Evidencia**: Son TRES sistemas completamente separados:

| Sistema | Archivo | Protocolo | LSP integrado | Usado por CLI |
|---------|---------|-----------|---------------|---------------|
| LSPDaemonServer | infrastructure/lsp_daemon.py | JSON over UNIX socket | SÍ (LSPClient) | NO |
| DaemonManager | platform/daemon_manager.py | Custom (daemon dir) | NO | SÍ (daemon start/stop/status) |
| daemon run | cli.py (inline) | PING/HEALTH/SHUTDOWN | NO | SÍ (daemon run) |
| LSPManager | application/lsp_manager.py | JSON-RPC stdio (pyright) | SÍ (directo) | NO |

### ¿Qué significa hoy "operativo" para cada uno?

- **LSPDaemonServer**: Puede spawnearse via `python -m src.infrastructure.lsp_daemon start --root <path>`. Tests confirman que spawnea, escribe PID/socket, responde a status. **NO es invocado por el CLI principal**.
- **DaemonManager**: Usado por `trifecta daemon start/stop/status/restart`. Spawnea `daemon run` como subprocess.
- **daemon run**: El proceso real que se ejecuta. Responde PING/HEALTH/SHUTDOWN. **NO tiene LSP**.
- **LSPManager**: Usado por `src/application/symbol_selector.py` con `lsp_enabled=False` por defecto. Su `request_definition()` siempre retorna None.

### ¿Cuál es la diferencia real en el código entre running/healthy/ready/degraded/failed?

**running**: `DaemonStatus.running` en `platform/daemon_manager.py` = PID existe + socket existe + `os.kill(pid, 0)` no falla.

**healthy**: `HealthChecker.check()` en `platform/health.py` = runtime_dir existe + runtime.db accesible + daemon socket/PID válidos.

**ready**: `LSPClient.is_ready()` = state == LSPState.READY (después de handshake initialize exitoso + invariant checks).

**degraded**: `CapabilityState.DEGRADED` en `domain/lsp_contracts.py` = fallback a AST-only. **Nunca se usa en código real**.

**failed**: `LSPState.FAILED` = handshake falló, proceso murió, o invariant check falló.

**Contradicción**: El health check de `platform/health.py` usa paths de `DaemonManager` (runtime_dir/daemon/socket), NO de `LSPDaemonServer` (/tmp/trifecta_lsp_*.sock). Son sistemas completamente separados.

### ¿Qué superficies son oficiales y cuáles son artefactos incidentales?

**Oficiales (con CLI)**:

- `trifecta daemon start --repo <path>`
- `trifecta daemon stop --repo <path>`
- `trifecta daemon status --repo <path>`
- `trifecta daemon restart --repo <path>`
- `trifecta daemon run` (invocado internamente)

**Artefactos incidentales (sin CLI, solo tests/scripts)**:

- `LSPDaemonServer` / `LSPDaemonClient` (invocable via `python -m src.infrastructure.lsp_daemon`)
- `LSPManager` (usado internamente por symbol_selector, siempre con `lsp_enabled=False`)

### ¿Qué contrato parece querer existir aunque todavía no esté formalizado?

El sistema sugiere un contrato donde:

1. Un daemon mantiene un LSP vivo para un repo
2. El daemon responde a requests de status/health
3. El daemon se auto-limpia después de TTL
4. El daemon es singleton por repo (fcntl lock)

**Pero el código real implementa**: Un daemon simple sin LSP (daemon run) que solo responde PING/HEALTH/SHUTDOWN, y un daemon LSP completo (LSPDaemonServer) que nunca es invocado.

## Definiciones operativas preliminares

### Daemon (operativa)

Un proceso UNIX que mantiene un socket AF_UNIX en `~/.local/share/trifecta/repos/<fingerprint>/runtime/daemon/`, responde PING/HEALTH/SHUTDOWN, se auto-limpia al recibir SIGTERM. **NO tiene LSP integrado**.

### LSP (operativa)

Un cliente LSP (`LSPClient`) que spawnea pyright/pylsp por stdio, maneja estado COLD→WARMING→READY→FAILED, y puede servir requests textDocument/definition y textDocument/hover. **Existe en código pero no está conectado al daemon del CLI**.

## Ambigüedades reales que el código no resuelve

1. **¿Por qué hay tres implementaciones de daemon?** No hay documentación que explique la relación entre LSPDaemonServer, DaemonManager/daemon_run, y LSPManager.
2. **¿LSPManager.request_definition() alguna vez devuelve datos?** El código dice "For MVP: return mock response or None". No hay evidencia de que funcione.
3. **¿Qué daemon responde `trifecta daemon status`?** Responde DaemonUseCase → DaemonManager, que chequea runtime_dir/daemon/socket. NO chequea /tmp/trifecta_lsp_*.sock.
4. **¿runtime.db es requerido para health?** HealthChecker.check() lo requiere, pero DaemonManager.start() no lo crea. Solo `trifecta index` lo crea (como search.db, no runtime.db).
5. **DEFAULT_TTL inconsistente**: `lsp_daemon.py` define DEFAULT_TTL = 180 y luego DEFAULT_TTL = 300. El CLI usa DAEMON_TTL_IDLE = 300.

---

# 2. Layout

## Mapa de arquitectura en texto

```
CLI Layer (src/infrastructure/cli.py)
├── daemon_app (typer sub-app)
│   ├── daemon start → DaemonUseCase.start() → DaemonManager.start()
│   ├── daemon stop → DaemonUseCase.stop() → DaemonManager.stop()
│   ├── daemon status → DaemonUseCase.status() → DaemonManager.status() + HealthChecker.check()
│   ├── daemon restart → DaemonUseCase.restart() → DaemonManager.restart()
│   └── daemon run → [INLINE: socket server con PING/HEALTH/SHUTDOWN]
│
Application Layer
├── daemon_use_case.py → DaemonUseCase (orchestra DaemonManager + HealthChecker)
├── lsp_manager.py → LSPManager (pyright headless, NUNCA usado con enabled=True)
└── symbol_selector.py → usa LSPManager con lsp_enabled=False

Platform Layer
├── daemon_manager.py → DaemonManager (start/stop/restart/status)
└── health.py → HealthChecker (runtime_exists, db_accessible, daemon_healthy)

Infrastructure Layer
├── lsp_daemon.py → LSPDaemonServer + LSPDaemonClient (UNIX socket, JSON protocol)
│   └── usa lsp_client.py → LSPClient (spawnea pyright/pylsp, stdio JSON-RPC)
├── daemon_paths.py → get_daemon_socket_path/lock/pid (paths en /tmp con segment_id)
└── telemetry.py → Telemetry (event logging)

Domain Layer
└── lsp_contracts.py → LSPResponse, CapabilityState, FallbackReason, Backend
```

## Tabla de surfaces y ownership

| Surface | Owner | Create Path | Read Path | Cleanup Path | Requerido para liveness |
|---------|-------|-------------|-----------|--------------|------------------------|
| runtime_dir/daemon/socket | DaemonManager | DaemonManager.start() | DaemonManager.status() | DaemonManager._cleanup_files() | SÍ (daemon healthy) |
| runtime_dir/daemon/pid | DaemonManager | DaemonManager.start() | DaemonManager.status() | DaemonManager._cleanup_files() | SÍ (daemon healthy) |
| runtime_dir/daemon/log | DaemonManager | DaemonManager.start() (append) | Manual | No auto-cleanup | NO |
| runtime_dir/runtime.db | HealthChecker (read-only) | NO (espera que exista) | HealthChecker._check_db_accessible() | NO | SÍ (health check) |
| /tmp/trifecta_lsp_{seg_id}.sock | LSPDaemonServer | LSPDaemonServer.start() | LSPDaemonClient | LSPDaemonServer.cleanup() | NO (no usado por CLI) |
| /tmp/trifecta_lsp_{seg_id}.pid | LSPDaemonServer | LSPDaemonServer.start() | LSPDaemonClient | LSPDaemonServer.cleanup() | NO |
| /tmp/trifecta_lsp_{seg_id}.lock | LSPDaemonServer | LSPDaemonServer.start() | LSPDaemonServer | LSPDaemonServer.cleanup() | NO |

## Tabla de entrypoints y responsabilidades

| Comando | Módulo | Responsabilidad real |
|---------|--------|---------------------|
| `trifecta daemon start --repo` | cli.py → DaemonUseCase | Spawnea `daemon run` como subprocess, espera socket |
| `trifecta daemon stop --repo` | cli.py → DaemonUseCase | SIGTERM al PID, limpia archivos |
| `trifecta daemon status --repo` | cli.py → DaemonUseCase | Lee PID/socket, ejecuta HealthChecker |
| `trifecta daemon restart --repo` | cli.py → DaemonUseCase | stop + start |
| `trifecta daemon run` | cli.py (inline) | Socket server PING/HEALTH/SHUTDOWN |

## Tabla de dependencias y acoplamientos

| Desde | Hacia | Tipo | Acoplamiento |
|-------|-------|------|-------------|
| DaemonUseCase | DaemonManager | Directo (composición) | Alto |
| DaemonUseCase | HealthChecker | Directo (composición) | Alto |
| DaemonManager | cli.py daemon run | Subprocess (invoca) | Medio (env var) |
| LSPDaemonServer | LSPClient | Directo (composición) | Alto |
| LSPDaemonServer | daemon_paths.py | Directo (import) | Medio |
| LSPManager | subprocess (pyright) | Directo (spawnea) | Alto |
| HealthChecker | runtime_dir/daemon/* | Filesystem (lee) | Medio |
| HealthChecker | runtime_dir/runtime.db | Filesystem (lee) | Medio |
| CLI daemon start | resolve_segment_ref | Directo (import) | Bajo |

---

# 3. Operate

## Secuencia operacional real

### 1. Start

```bash
trifecta daemon start --repo .
```

**Flujo real**:

1. CLI resuelve segment_ref → obtiene fingerprint
2. Calcula runtime_dir = `~/.local/share/trifecta/repos/<fingerprint>/runtime`
3. DaemonUseCase.start() → DaemonManager.start()
4. DaemonManager verifica is_running() → false
5. Crea runtime_dir/daemon/ directory
6. Spawnea: `python <cli.py> daemon run` con TRIFECTA_RUNTIME_DIR env var
7. Espera 5 segundos a que aparezca socket_path
8. Escribe PID a pid_path

**Resultado observado**: "Daemon started" si socket aparece en 5s, "Failed to start daemon" si no.

### 2. Status

```bash
trifecta daemon status --repo .
```

**Flujo real**:

1. DaemonUseCase.status() → DaemonManager.status() + HealthChecker.check()
2. DaemonManager: lee pid_path, verifica os.kill(pid, 0), verifica socket_path.exists()
3. HealthChecker: runtime_dir.exists() + runtime.db accesible + daemon socket/PID válidos
4. Retorna JSON con running, pid, socket, health

**Resultado esperado vs observado**:

- Esperado: Health score 100% si daemon está corriendo
- Observado: Health score 66.67% porque runtime.db no existe (creado por `trifecta index`, no por daemon)

### 3. Health

```bash
trifecta daemon status --repo . --json
```

**Checks reales**:

- `runtime_exists`: ¿runtime_dir existe? → Generalmente TRUE
- `db_accessible`: ¿runtime_dir/runtime.db existe y es SQLite válido? → FALSE hasta que se ejecute `trifecta index`
- `daemon_healthy`: ¿socket + PID válidos? → TRUE si daemon está corriendo

### 4. Request/acción servida por el daemon

```bash
echo "PING" | nc -U ~/.local/share/trifecta/repos/<fingerprint>/runtime/daemon/socket
```

**Protocolo real**: Solo PING, HEALTH, SHUTDOWN. Cualquier otro comando devuelve "ERROR: Unknown command".

### 5. Operación LSP real

**NO HAY operación LSP real servida por el daemon del CLI**. El daemon run solo responde PING/HEALTH/SHUTDOWN.

LSPDaemonServer (no usado por CLI) soportaría:

- `{"method": "status"}` → estado del LSPClient
- `{"method": "did_open", "params": {"path": "...", "content": "..."}}` → abre archivo
- `{"method": "request", "params": {"method": "textDocument/hover", "params": {...}}}` → request LSP

### 6. Restart

```bash
trifecta daemon restart --repo .
```

**Flujo real**: stop() → start(). Mismo flujo que start después de stop.

### 7. Stop/Cleanup

```bash
trifecta daemon stop --repo .
```

**Flujo real**:

1. Lee PID de pid_path
2. os.kill(pid, SIGTERM)
3. Espera 5 segundos a que proceso desaparezca
4. Si no desaparece: os.kill(pid, SIGKILL)
5. Limpia pid_path y socket_path

### 8. Cold start

Primera invocación de `daemon start` cuando no hay daemon previo. Funciona correctamente si el runtime_dir se puede crear.

### 9. Re-entry / Singleton behavior

**DaemonManager**: No tiene locking explícito. Verifica is_running() antes de start(), pero hay race condition posible.
**LSPDaemonServer**: Usa fcntl.lockf() para singleton. Si lock falla, imprime "Daemon already running." y retorna.
**daemon run (CLI)**: No tiene locking. Si se invoca dos veces, el segundo falla al hacer bind() al socket existente.

## Tabla "esperado vs observado"

| Comando | Esperado | Observado | Discrepancia |
|---------|----------|-----------|-------------|
| daemon start | Inicia daemon con LSP | Inicia daemon SIN LSP | LSP no integrado |
| daemon status | Health 100% | Health 66.67% | runtime.db no existe |
| daemon status --json | Incluye LSP state | No incluye LSP state | LSP no integrado |
| PING | PONG | PONG | ✅ Consistente |
| HEALTH | JSON con uptime | JSON con uptime | ✅ Consistente |
| Request LSP | Respuesta LSP | "Unknown command" | LSP no integrado |

## Contradicciones concretas

1. **`src/infrastructure/lsp_daemon.py` línea 262**: `DEFAULT_TTL = 300` sobreescribe `DEFAULT_TTL = 180` de línea 30. Dos definiciones del mismo constant en el mismo archivo.

2. **`src/platform/health.py` espera runtime.db** pero ningún código crea runtime.db. `trifecta index` crea search.db, no runtime.db. La única forma de que health sea 100% es crear runtime.db manualmente con sqlite3.

3. **`src/application/lsp_manager.py` línea 119**: `request_definition()` tiene comentario "Would read from stdout here in real implementation / For MVP: return mock response or None". Nunca devuelve datos reales.

4. **`src/infrastructure/cli.py` daemon run**: Implementa su propio protocolo PING/HEALTH/SHUTDOWN inline, sin usar LSPDaemonServer ni LSPClient. El daemon del CLI NO tiene LSP.

5. **`src/infrastructure/lsp_daemon.py` LSPDaemonClient._spawn_daemon()**: Invoca `python -m src.infrastructure.lsp_daemon start --root`, pero el CLI nunca usa LSPDaemonClient. Usa DaemonManager que invoca `daemon run`.

6. **Health check usa paths de DaemonManager** (runtime_dir/daemon/*) pero LSPDaemonServer usa paths de daemon_paths.py (/tmp/trifecta_lsp_*). Son sistemas completamente separados sin integración.

---

# 4. Observe

## Diagnóstico técnico por capas

### Daemon (trifecta daemon)

- **Capa CLI**: ✅ Funcional. Comandos start/stop/status/restart implementados.
- **Capa Application (DaemonUseCase)**: ✅ Funcional. Orquesta correctamente DaemonManager + HealthChecker.
- **Capa Platform (DaemonManager)**: ✅ Funcional. Start/stop/restart/status operan correctamente.
- **Capa Runtime (daemon run)**: ⚠️ Parcialmente funcional. Responde PING/HEALTH/SHUTDOWN pero NO tiene LSP.
- **Protocolo**: ⚠️ Limitado. Solo 3 comandos, no sirve requests de código.

### LSP

- **LSPClient**: ✅ Implementado. Spawnea pyright/pylsp, handshake, state machine, requests.
- **LSPDaemonServer**: ✅ Implementado. Servidor UNIX socket que usa LSPClient.
- **LSPManager**: ⚠️ Stub. `request_definition()` siempre retorna None.
- **Integración con daemon CLI**: ❌ NO EXISTE. El daemon del CLI no tiene LSP.
- **Integración con commands de usuario**: ❌ NO EXISTE. Ningún comando CLI invoca LSP.

## Clasificación de cada capability

| Capability | Estado | Evidencia |
|------------|--------|-----------|
| daemon start | **implementada + usable local** | CLI funciona, spawnea proceso |
| daemon stop | **implementada + usable local** | CLI funciona, mata proceso |
| daemon status | **implementada + usable local** | CLI funciona, reporta estado |
| daemon restart | **implementada + usable local** | CLI funciona |
| daemon PING | **implementada + usable local** | Responde PONG |
| daemon HEALTH | **implementada + usable local** | Responde JSON |
| daemon SHUTDOWN | **implementada + usable local** | Mata proceso |
| LSP spawn | **implementada** | LSPClient.start() funciona |
| LSP handshake | **implementada** | LSPClient._run_loop() hace initialize |
| LSP definition | **implementada** | LSPClient.request("textDocument/definition") |
| LSP hover | **implementada** | LSPClient.request("textDocument/hover") |
| LSP via daemon | **NO EXISTE** | daemon run no tiene LSP |
| LSP via CLI | **NO EXISTE** | Ningún comando CLI usa LSP |
| LSPManager definition | **stub/WIP** | Siempre retorna None |
| Health check runtime.db | **chequeo mal modelado** | runtime.db no es creado por nadie |
| LSP contracts (FULL/DEGRADED) | **implementada pero no usada** | Clases existen, nadie las instancia |
| Fallback protocol | **implementada pero no usada** | Métodos existen, nadie los llama |

## Top 10 riesgos reales del subsistema

1. **Fragmentación de daemon**: Tres implementaciones separadas (LSPDaemonServer, DaemonManager/daemon_run, LSPManager) sin integración. Cualquier cambio requiere tocar múltiples sistemas.

2. **LSP nunca servido por daemon**: El daemon del CLI responde PING/HEALTH/SHUTDOWN pero no puede servir requests LSP. El LSPClient existe pero no está conectado.

3. **Health check falso negativo**: HealthChecker requiere runtime.db que nadie crea. Health score 66.67% permanente hasta que se ejecute `sqlite3 runtime.db "SELECT 1"` manualmente.

4. **Race condition en singleton**: DaemonManager.is_running() check + start() no es atómico. Dos instancias pueden intentar iniciar simultáneamente.

5. **DEFAULT_TTL inconsistente**: lsp_daemon.py tiene dos definiciones (180 y 300). El CLI usa 300. Confunde configuración.

6. **LSPManager siempre disabled**: `symbol_selector.py` instancia LSPManager con `lsp_enabled=False`. Nunca se activa.

7. **Sin integración daemon↔LSP**: El daemon del CLI no puede mantener un LSP vivo. Cada request LSP requeriría un cold start.

8. **Protocolo daemon limitado**: Solo PING/HEALTH/SHUTDOWN. No puede servir búsquedas, indexación, o requests LSP.

9. **Sin TTL en daemon run**: El daemon run del CLI no tiene TTL. Corre indefinidamente hasta SIGTERM. LSPDaemonServer tiene TTL de 180s.

10. **runtime.db phantom dependency**: Health check falla si runtime.db no existe, pero ningún flujo normal lo crea. Es un artefacto manual.

## Top 10 huecos de contrato

1. **No hay contrato que defina qué responde el daemon**: El protocolo PING/HEALTH/SHUTDOWN no está documentado.

2. **No hay contrato de health**: Health score 66.67% vs 100% no tiene significado operacional claro.

3. **No hay contrato LSP↔daemon**: No se define cuándo el daemon debería mantener un LSP vivo.

4. **No hay contrato de cleanup**: ¿Quién limpia runtime.db? ¿Quién limpia logs?

5. **No hay contrato de readiness**: ¿Qué significa "daemon listo"? ¿Socket existe? ¿Responde PING? ¿LSP está READY?

6. **No hay contrato de degraded mode**: CapabilityState.DEGRADED existe en lsp_contracts.py pero nunca se usa.

7. **No hay contrato de fallback**: FallbackReason enum existe pero nunca se instancia en el daemon del CLI.

8. **No hay contrato de multi-repo**: ¿Un daemon por repo? ¿Un daemon global? El código soporta ambos pero no declara política.

9. **No hay contrato de versionado del protocolo**: HEALTH responde "version": "1.0.0" pero no hay versionado real del protocolo.

10. **No hay contrato de telemetry del daemon**: ¿Qué eventos se emiten? ¿Cuándo? El daemon run no emite eventos de telemetry.

---

# 5. Reflect

## A. Veredicto ejecutivo

### Daemon: PARCIALMENTE OPERATIVO

- **Start/stop/status/restart**: ✅ Funcionan correctamente
- **Protocolo**: ⚠️ Solo PING/HEALTH/SHUTDOWN, no sirve contenido
- **LSP integrado**: ❌ NO. El daemon del CLI no tiene LSP
- **Health**: ⚠️ Funciona pero con falso negativo (runtime.db)
- **Certificación**: NO CERTIFICADO. Falta integración LSP, health preciso, protocolo completo

### LSP: NO OPERATIVO (a nivel de sistema)

- **LSPClient**: ✅ Implementado y testeado
- **LSPDaemonServer**: ✅ Implementado pero NO conectado al CLI
- **LSPManager**: ⚠️ Stub/WIP. `request_definition()` siempre retorna None
- **Integración con daemon**: ❌ NO EXISTE
- **Integración con CLI**: ❌ NO EXISTE
- **Certificación**: NO CERTIFICADO. Existen piezas pero no forman un sistema operativo

## B. Qué está sólido

1. **LSPClient** (`src/infrastructure/lsp_client.py`): Implementación completa de cliente LSP con state machine, handshake, requests, shutdown ordenado, telemetry. Tests pasan.

2. **LSP contracts** (`src/domain/lsp_contracts.py`): Contratos bien diseñados con CapabilityState, FallbackReason, ResponseState, Backend. Enum claros, métodos factory correctos.

3. **DaemonManager** (`src/platform/daemon_manager.py`): Start/stop/restart/status funcionan correctamente con subprocess, PID tracking, socket detection.

4. **daemon_paths.py** (`src/infrastructure/daemon_paths.py`): Validación de AF_UNIX path limits, paths cortos en /tmp, validación de base dir.

5. **Tests de daemon** (`tests/integration/test_lsp_daemon.py`): Tests sólidos para spawn, singleton, TTL cleanup, cold start, no blocking.

6. **Tests de daemon manager** (`tests/integration/daemon/test_daemon_manager.py`): Tests para status dataclass, path validation, runtime dir allowed.

## C. Qué está blando/riesgoso/contradictorio

### Contradicción documental

- No hay documentación que explique por qué hay tres implementaciones de daemon/LSP
- La session log dice "daemon is NOT a common LSP" pero el daemon del CLI NO tiene LSP
- El technical report menciona "daemon health improved 33% → 66.67%" pero no explica que 66.67% es el máximo posible sin runtime.db

### Contradicción de código

- `lsp_daemon.py` tiene DEFAULT_TTL = 180 y DEFAULT_TTL = 300 en el mismo archivo
- `lsp_manager.py` request_definition() dice "For MVP: return mock response or None" - nunca funciona
- `daemon run` implementa protocolo inline sin usar LSPDaemonServer ni LSPClient
- HealthChecker espera runtime.db pero nadie lo crea
- LSPManager se instancia con `lsp_enabled=False` en symbol_selector.py

### Contradicción operacional

- `trifecta daemon status` reporta health 66.67% en condiciones normales
- El daemon responde HEALTH con "protocol": ["PING", "HEALTH", "SHUTDOWN"] pero no puede servir LSP
- LSPDaemonServer existe y funciona pero no es invocado por ningún comando CLI
- Los tests de LSP pasan pero el LSP nunca es usado en producción

## D. Contrato mínimo que parece emerger

### Contrato mínimo actual del daemon

```
DADO un repo con fingerprint F
CUANDO se ejecuta `trifecta daemon start --repo <path>`
ENTONCES un proceso se spawnea en background
Y crea runtime_dir/daemon/socket
Y crea runtime_dir/daemon/pid
Y responde PING con PONG
Y responde HEALTH con JSON {status, pid, uptime, version, protocol}
Y responde SHUTDOWN con OK y se mata
Y al recibir SIGTERM limpia socket y pid
```

### Contrato mínimo actual del LSP

```
DADO un workspace root
CUANDO se instancia LSPClient(root)
Y se llama start()
ENTONCES spawnea pyright o pylsp
Y ejecuta handshake initialize/initialized
Y transiciona COLD → WARMING → READY (si invariants pasan)
Y puede servir requests textDocument/definition y textDocument/hover
Y al llamar stop() termina proceso y cierra streams
```

**NOTA**: Estos dos contratos NO están conectados. El daemon no usa LSPClient.

## E. Qué falta para un batch de operacionalización

1. **Decisión arquitectónica**: ¿Unificar LSPDaemonServer y DaemonManager? ¿O mantener separados y conectarlos? La decisión debe ser explícita.

2. **Integración daemon↔LSP**: El daemon del CLI debe poder mantener un LSP vivo. Esto requiere que `daemon run` use LSPClient o LSPDaemonServer.

3. **Fix health check**: O crear runtime.db automáticamente, o cambiar el check para no requerirlo. El estado actual es un falso negativo.

4. **Protocolo unificado**: Definir un solo protocolo que soporte PING/HEALTH/SHUTDOWN + LSP requests.

5. **Eliminar LSPManager o conectarlo**: LSPManager.request_definition() nunca funciona. O implementarlo o eliminarlo.

6. **Documentar arquitectura**: Explicar qué sistema es el "real" y cuáles son legacy/WIP.

7. **Tests de integración**: Tests que validen daemon + LSP juntos, no por separado.

8. **TTL para daemon run**: Agregar TTL al daemon del CLI (como LSPDaemonServer tiene).

9. **Telemetry en daemon run**: El daemon del CLI no emite eventos de telemetry.

10. **Unificar DEFAULT_TTL**: Eliminar la duplicación en lsp_daemon.py.

---

## Anexo A — Mapa de archivos y módulos

### Domain

| Archivo | Propósito | Estado |
|---------|-----------|--------|
| `src/domain/lsp_contracts.py` | Contratos LSP (LSPResponse, CapabilityState, etc.) | ✅ Implementado, no usado por daemon CLI |

### Application

| Archivo | Propósito | Estado |
|---------|-----------|--------|
| `src/application/daemon_use_case.py` | Orquesta DaemonManager + HealthChecker | ✅ Funcional |
| `src/application/lsp_manager.py` | LSP headless con pyright | ⚠️ Stub (request_definition siempre None) |

### Infrastructure

| Archivo | Propósito | Estado |
|---------|-----------|--------|
| `src/infrastructure/lsp_daemon.py` | LSPDaemonServer + LSPDaemonClient | ✅ Implementado, NO usado por CLI |
| `src/infrastructure/lsp_client.py` | Cliente LSP (pyright/pylsp) | ✅ Implementado |
| `src/infrastructure/daemon_paths.py` | Paths para daemon (/tmp) | ✅ Funcional |
| `src/infrastructure/cli.py` | CLI con daemon_app + daemon run inline | ✅ Funcional (daemon simple) |

### Platform

| Archivo | Propósito | Estado |
|---------|-----------|--------|
| `src/platform/daemon_manager.py` | DaemonManager (start/stop/restart/status) | ✅ Funcional |
| `src/platform/health.py` | HealthChecker (3 checks) | ⚠️ Falso negativo por runtime.db |

### Tests

| Archivo | Propósito | Estado |
|---------|-----------|--------|
| `tests/integration/test_lsp_daemon.py` | Tests LSPDaemonServer/LSPDaemonClient | ✅ 5 tests |
| `tests/integration/daemon/test_daemon_manager.py` | Tests DaemonManager | ✅ Tests |
| `tests/integration/test_daemon_paths_constraints.py` | Tests daemon_paths validation | ✅ Tests |
| `tests/unit/test_lsp_client_strict.py` | Tests LSPClient strict | ✅ Tests |
| `tests/unit/test_lsp_ready_contract.py` | Tests LSP ready contract | ✅ Tests |
| `tests/unit/test_cli_hardening.py` | Tests CLI daemon run hardening | ✅ Tests |
| `tests/integration/test_lsp_contract_fallback.py` | Tests LSP fallback contracts | ✅ Tests |

---

## Anexo B — Entry points y comandos

| Comando | Archivo | Función | Invoca LSP? |
|---------|---------|---------|-------------|
| `trifecta daemon start --repo` | cli.py:daemon_start | DaemonUseCase.start() → DaemonManager.start() | NO |
| `trifecta daemon stop --repo` | cli.py:daemon_stop | DaemonUseCase.stop() → DaemonManager.stop() | NO |
| `trifecta daemon status --repo` | cli.py:daemon_status | DaemonUseCase.status() | NO |
| `trifecta daemon restart --repo` | cli.py:daemon_restart | DaemonUseCase.restart() | NO |
| `trifecta daemon run` | cli.py:daemon_run | Inline socket server PING/HEALTH/SHUTDOWN | NO |
| `python -m src.infrastructure.lsp_daemon start --root` | lsp_daemon.py:**main** | LSPDaemonServer.start() | SÍ |

---

## Anexo C — Surfaces y ownership

| Surface | Owner | Lifecycle |
|---------|-------|-----------|
| `~/.local/share/trifecta/repos/<id>/runtime/daemon/socket` | DaemonManager | Created by start(), cleaned by stop() |
| `~/.local/share/trifecta/repos/<id>/runtime/daemon/pid` | DaemonManager | Created by start(), cleaned by stop() |
| `~/.local/share/trifecta/repos/<id>/runtime/daemon/log` | DaemonManager | Created by start(), never auto-cleaned |
| `~/.local/share/trifecta/repos/<id>/runtime/runtime.db` | NADIE (esperado por HealthChecker) | Nunca creado automáticamente |
| `/tmp/trifecta_lsp_<seg_id>.sock` | LSPDaemonServer | Created by start(), cleaned by cleanup() |
| `/tmp/trifecta_lsp_<seg_id>.pid` | LSPDaemonServer | Created by start(), cleaned by cleanup() |
| `/tmp/trifecta_lsp_<seg_id>.lock` | LSPDaemonServer | Created by start(), cleaned by cleanup() |

---

## Anexo D — Capacidades daemon/LSP y estado real

| Capability | Implementada | Cableada | Usable local | Estable | Stub/WIP |
|------------|-------------|----------|-------------|---------|----------|
| daemon start | ✅ | ✅ | ✅ | ✅ | |
| daemon stop | ✅ | ✅ | ✅ | ✅ | |
| daemon status | ✅ | ✅ | ⚠️ | ✅ | |
| daemon restart | ✅ | ✅ | ✅ | ✅ | |
| daemon PING | ✅ | ✅ | ✅ | ✅ | |
| daemon HEALTH | ✅ | ✅ | ✅ | ✅ | |
| daemon SHUTDOWN | ✅ | ✅ | ✅ | ✅ | |
| LSP spawn | ✅ | ❌ | ❌ | ✅ | |
| LSP handshake | ✅ | ❌ | ❌ | ✅ | |
| LSP definition | ✅ | ❌ | ❌ | ✅ | |
| LSP hover | ✅ | ❌ | ❌ | ✅ | |
| LSP via daemon | ❌ | ❌ | ❌ | ❌ | |
| LSP via CLI | ❌ | ❌ | ❌ | ❌ | |
| LSPManager definition | | | | | ⚠️ STUB |
| Health 100% | ⚠️ | ⚠️ | ❌ | ❌ | |

---

## Anexo E — Contradicciones detectadas

1. **DEFAULT_TTL duplicado**: `src/infrastructure/lsp_daemon.py` línea 30 (`DEFAULT_TTL = 180`) y línea 262 (`DEFAULT_TTL = 300`). El CLI usa 300 (DaemonManager).

2. **runtime.db no creado**: `src/platform/health.py` _check_db_accessible() espera runtime_dir/runtime.db, pero ningún código lo crea. `trifecta index` crea search.db, no runtime.db.

3. **LSPManager stub**: `src/application/lsp_manager.py` request_definition() línea 119: "Would read from stdout here in real implementation / For MVP: return mock response or None".

4. **Tres sistemas de daemon no integrados**: LSPDaemonServer, DaemonManager/daemon_run, LSPManager coexisten sin integración.

5. **daemon run sin LSP**: El daemon del CLI (`daemon run`) no tiene LSP. Solo responde PING/HEALTH/SHUTDOWN.

6. **LSPDaemonServer no invocado**: LSPDaemonClient._spawn_daemon() invoca `python -m src.infrastructure.lsp_daemon`, pero el CLI nunca usa LSPDaemonClient.

7. **Health check usa paths incorrectos**: HealthChecker chequea runtime_dir/daemon/*(paths de DaemonManager) pero si el daemon real fuera LSPDaemonServer, los paths serían /tmp/trifecta_lsp_*.

---

## Anexo F — Riesgos residuales

1. **Fragmentación arquitectónica** (P0): Tres sistemas de daemon no integrados.
2. **LSP nunca servido** (P0): El daemon CLI no puede servir requests LSP.
3. **Health falso negativo** (P1): runtime.db no existe → health siempre 66.67%.
4. **Race condition singleton** (P1): DaemonManager no tiene locking atómico.
5. **DEFAULT_TTL inconsistente** (P2): Dos valores en mismo archivo.
6. **LSPManager siempre disabled** (P2): Nunca se activa en producción.
7. **Sin TTL en daemon run** (P2): Corre indefinidamente.
8. **Sin telemetry en daemon run** (P2): No emite eventos.
9. **Protocolo sin versionado** (P3): HEALTH dice "version": "1.0.0" pero no hay versionado real.
10. **Sin tests de integración daemon+LSP** (P2): Tests son por separado.

---

## Anexo G — Preguntas abiertas que siguen sin autoridad clara

1. **¿Cuál es el daemon "real"?** ¿LSPDaemonServer, DaemonManager, o daemon run? No hay documentación que lo declare.

2. **¿Por qué LSPDaemonServer no es usado por el CLI?** Existe, funciona, tiene tests, pero el CLI usa daemon run que no tiene LSP.

3. **¿runtime.db debería existir?** Health check lo requiere pero nadie lo crea. ¿Es un bug o un feature incompleto?

4. **¿LSPManager fue abandonado?** Su request_definition() siempre retorna None. ¿Se planea implementar o eliminar?

5. **¿Cuál es el plan para LSP en el daemon?** ¿Se va a conectar LSPClient al daemon run? ¿Se va a reemplazar daemon run con LSPDaemonServer?

6. **¿Quién es el owner del subsistema?** No hay evidencia de quién mantiene esta arquitectura fragmentada.

7. **¿Hay un ADR que documente la decisión de tres sistemas?** No se encontró ADR que explique la fragmentación.

8. **¿El daemon debería tener TTL?** LSPDaemonServer tiene TTL de 180s. daemon run no tiene TTL. ¿Cuál es la política?

9. **¿El daemon debería emitir telemetry?** daemon run no emite eventos. LSPDaemonServer sí. ¿Cuál es el estándar?

10. **¿Cuándo se cierra técnicamente el daemon?** ¿Cuando responde PING? ¿Cuando health es 100%? ¿Cuando LSP está READY? No hay definición.
