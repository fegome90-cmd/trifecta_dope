# Contrato del Daemon: Trifecta

**Fecha**: 2026-03-22
**Fase**: 1 (Autoridad + tabla de verdad)
**Línea oficial**: `DaemonManager + daemon run`

---

## 1. Superficie oficial

| Comando | Descripción |
|---------|-------------|
| `trifecta daemon start --repo <path>` | Spawnea daemon en background |
| `trifecta daemon stop --repo <path>` | Detiene daemon (SIGTERM) |
| `trifecta daemon status --repo <path>` | Reporta estado del daemon |
| `trifecta daemon restart --repo <path>` | stop + start |
| `trifecta daemon run` | Invocado internamente por DaemonManager |

## 2. Superficies NO oficiales

| Sistema | Razón de no-autoridad |
|---------|----------------------|
| `LSPDaemonServer` (`src/infrastructure/lsp_daemon.py`) | No tiene CLI. No es invocado por comandos oficiales. Referencia de implementación LSP. |
| `LSPManager` (`src/application/lsp_manager.py`) | Stub. `request_definition()` siempre retorna None. Fuera del camino feliz. |

## 3. Protocolo

El daemon responde sobre UNIX socket en `runtime_dir/daemon/socket`.

### Request/Response

| Comando Request | Response |
|----------------|----------|
| `PING` | `PONG\n` |
| `HEALTH` | `{"status":"ok","pid":<int>,"uptime":<int>,"version":"1.0.0","protocol":["PING","HEALTH","SHUTDOWN"]}\n` |
| `SHUTDOWN` | `OK\n` (daemon se mata) |
| Cualquier otro | `ERROR: Unknown command\n` |

### Formato

- Request: texto plano, max 128 bytes
- Response: texto plano o JSON + `\n`
- Transporte: AF_UNIX socket

## 4. Tabla de verdad

| Estado | Definición | Cómo se verifica |
|--------|------------|------------------|
| **running** | Proceso vivo + socket existe + PID válido | `os.kill(pid, 0)` no falla + `socket_path.exists()` |
| **ready** | running + responde HEALTH con JSON válido | Conectar al socket, enviar `HEALTH`, recibir JSON con `status: ok` |
| **failed** | Proceso no vivo O socket no existe | `os.kill(pid, 0)` falla O `socket_path` no existe |
| **degraded** | ready + LSP no disponible (Fase 3+) | HEALTH OK pero LSP state ≠ READY |

**Nota**: Estados degraded solo aplica después de Fase 3 (integración LSP). Hoy no hay estado degraded operativo.

## 5. Matriz de ownership

| Artefacto | Owner | Create | Read | Cleanup | Liveness |
|-----------|-------|--------|------|---------|----------|
| socket | DaemonManager | `start()` | `status()` | `_cleanup_files()` | SÍ |
| pid | DaemonManager | `start()` | `status()` | `_cleanup_files()` | SÍ |
| log | DaemonManager | `start()` (append) | Manual | NO auto | NO |
| runtime.db | N/A (chequeo mal modelado, fuera de health) | N/A | N/A | N/A | NO |
| singleton | socket bind (implícito) | `start()` (bind) | `start()` (bind fail) | `_cleanup_files()` | SÍ |

### Paths

| Artefacto | Path |
|-----------|------|
| socket | `~/.local/share/trifecta/repos/<fingerprint>/runtime/daemon/socket` |
| pid | `~/.local/share/trifecta/repos/<fingerprint>/runtime/daemon/pid` |
| log | `~/.local/share/trifecta/repos/<fingerprint>/runtime/daemon/log` |

## 6. Alcance de Fase 1

- Declarar línea operacional oficial
- Documentar protocolo PING/HEALTH/SHUTDOWN
- Definir tabla de verdad
- Definir matriz de ownership
- Marcar superficies no oficiales

## 7. No-objetivos de Fase 1

- No cambiar código funcional
- No integrar LSP
- No modificar health check
- No agregar telemetry
- No cambiar protocolo
