### 7.3 Métricas de Telemetría

| Evento | Props | Métricas |
|--------|-------|----------|
| `selector.resolve` | `symbol_query`, `resolved` | `duration_ms` |
| `ast.parse` | `file`, `symbols_count` | `cache_hit` |
| `lsp.request` | `method`, `resolved` | `duration_ms` |
| `lsp.fallback` | `reason`, `fallback_to` | `warm_wait_ms` |
| `lsp.daemon_status` | `state` | `warm_wait_ms` |

---
