# Informe: Subsistema Daemon + LSP

**Fecha**: 2026-03-27
**Estado**: LSP vía daemon `validado localmente`

---

## Avanzado

### Bugs corregidos (6)

| # | Bug | Archivo | Fix |
|---|-----|---------|-----|
| 1 | Wiring `runtime_dir` → `LSPClient` | `runner.py`, `daemon_manager.py`, `daemon_use_case.py`, `cli.py` | `repo_root` propagado correctamente |
| 2 | Handshake falla con notificaciones previas | `lsp_client.py` | Loop tolerante para skip `window/logMessage` |
| 3 | Timeout 2s insuficiente | `lsp_client.py`, `daemon_manager.py` | `TRIFECTA_LSP_REQUEST_TIMEOUT` env var (default 30s) |
| 4 | `handle_lsp_request()` trata notificaciones como requests | `lsp_handler.py` | Distingue notificaciones vs requests |
| 5 | didOpen params formato incorrecto | `lsp_handler.py` | Transforma `{"path","content"}` a formato LSP `{"textDocument":{...}}` |
| 6 | `LSP.request()` no distinguía error response | `lsp_client.py` | Manejo de `__lsp_error__` sentinel |

### Capabilities validadas

| Capability | Clasificación | Evidencia |
|------------|---------------|-----------|
| Daemon core | `validado localmente` | `lsp.state: READY`, PID, HEALTH 100% |
| Wiring repo_root | `validado localmente` | Tests 3/3 passed |
| Handshake LSP | `validado localmente` | Loop tolerante, READY confirmado |
| Notificaciones vs requests | `validado localmente` | didOpen sin timeout |
| `didOpen` vía daemon | `validado localmente` | `backend: lsp_pyright` |
| `hover` vía daemon | `validado localmente` | `backend: lsp_pyright`, contenido útil real |
| Timeout configurable | `validado localmente` | `TRIFECTA_LSP_REQUEST_TIMEOUT` env var |

### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `src/platform/daemon_manager.py` | `repo_root` param, `TRIFECTA_REPO_ROOT`, `LSP_REQUEST_TIMEOUT` configurable |
| `src/infrastructure/daemon/runner.py` | Campo `repo_root`, `from_env()` lee env vars, `_initialize_lsp_client()` usa `repo_root` |
| `src/application/daemon_use_case.py` | `repo_root` param |
| `src/infrastructure/cli.py` | `daemon_*` pasan `repo_root` |
| `src/infrastructure/lsp_client.py` | Handshake tolerante, timeout configurable, stderr drain, logging diagnóstico |
| `src/infrastructure/daemon/lsp_handler.py` | Distingue notificaciones vs requests, transforma didOpen a formato LSP |

### Tests nuevos

| Test | Archivo | Verifica |
|------|---------|----------|
| `test_daemon_runner_uses_repo_root_for_lsp_client` | `test_runner_repo_root.py` | Wiring repo_root |
| `test_daemon_runner_from_env_reads_repo_root` | `test_runner_repo_root.py` | Env var reading |
| `test_daemon_runner_from_env_fails_without_repo_root` | `test_runner_repo_root.py` | Fail-closed |
| `test_didopen_transforms_daemon_params_to_lsp_format` | `test_lsp_handler_didopen_format.py` | didOpen LSP format |
| `test_didopen_detects_language_from_extension` | `test_lsp_handler_didopen_format.py` | Language detection |

**Tests existentes**: 10/10 passed

### Evidencia de validación

```
hover status: ok
hover backend: lsp_pyright
hover response_state: complete
hover CONTENTS: YES - (module) __future__

Record of phased-in incompatible language changes.
```

---

## Pendiente

| Capability | Estado | Bloqueo |
|------------|--------|---------|
| `textDocument/definition` vía daemon | `no validado` | No ejecutado aún |
| TTL con timeout natural | `implementado, no validado` | Requiere esperar 300s |
| Telemetry events.jsonl | `implementado, no validado` | No verificado escritura |

### Próximo paso recomendado

Validar `textDocument/definition` vía daemon sobre un símbolo conocido del repo.
