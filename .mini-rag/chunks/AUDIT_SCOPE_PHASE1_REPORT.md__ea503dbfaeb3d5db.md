## B) Invariantes Identificadas

| # | Invariante | Ubicación SSOT | Evidencia |
|---|------------|----------------|-----------|
| 1 | **segment_root resolution** | `src/infrastructure/segment_utils.py:6-28` | `resolve_segment_root()` usa marcadores `.git` o `pyproject.toml` |
| 2 | **segment_id = 8 chars SHA256** | `src/infrastructure/segment_utils.py:31-37` | `compute_segment_id()` retorna `hashlib.sha256(path_str.encode()).hexdigest()[:8]` |
| 3 | **Schema version = 1** | `src/domain/context_models.py:42` | `schema_version: int = 1` (Pydantic) |
| 4 | **timing_ms >= 1** | `src/infrastructure/telemetry.py:66` | `"timing_ms": max(1, timing_ms)` |
| 5 | **stop_reason enum** | `src/application/context_service.py:139-213` | Valores: `"complete"`, `"budget"`, `"max_chunks"`, `"evidence"` |
| 6 | **Chunk ID format** | `src/application/context_service.py:10-32` | `parse_chunk_id()`: formato `"kind:hash"` con kind lowercase |
| 7 | **Daemon TTL = 180s** | `src/infrastructure/lsp_daemon.py:22` | `DEFAULT_TTL = 180` |
| 8 | **Socket path length limit** | `src/infrastructure/daemon_paths.py:13` | `MAX_UNIX_SOCKET_PATH = 100` |
| 9 | **No PII en telemetría** | `src/infrastructure/telemetry.py` | Verificado: no rutas absolutas en `events.jsonl` |
| 10 | **Cleanup idempotente** | `src/infrastructure/lsp_daemon.py:161-180` | `cleanup()` usa `unlink()` con `exists()` check |

---
