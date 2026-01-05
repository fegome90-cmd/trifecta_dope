### 3.2 LSP Daemon

**Ubicación**: `src/infrastructure/lsp_daemon.py`

**Características**:
- **Socket IPC**: Comunicación vía Unix socket
- **TTL**: 180 segundos de inactividad antes de shutdown
- **Lifecycle**: `connect_or_spawn()` → Spawn único → Warm wait → Ready
- **Telemetría**: Eventos `lsp.daemon_status`, `lsp.request`, `lsp.fallback`

**Flujo de Conexión**:

```python
# cli_ast.py:41-44
from src.infrastructure.lsp_daemon import LSPDaemonClient

client = LSPDaemonClient(root)
client.connect_or_spawn()  # Fire & Forget spawn if needed
```

**Estado del Daemon**:
```
SPAWNED → WARMING → READY → (TTL) → SHUTDOWN
         ↑                        ↓
         └────────── fallback ────┘
```
