### CRITICAL - DUPLICACIÓN ENCONTRADA:

| Concepto | SSOT Real | Duplicación Encontrada | Severidad |
|----------|-----------|------------------------|-----------|
| **ContextPack schema** | `src/domain/context_models.py:39-48` (Pydantic) | `src/domain/models.py:100-105` (dataclass) | **ALTA** |
| **segment_id compute** | `src/infrastructure/segment_utils.py:31-37` | `src/domain/models.py:24-29` (property) | MEDIA |
| **Lock mechanism** | `src/infrastructure/lsp_daemon.py:50` (fcntl.lockf) | `src/infrastructure/file_system_utils.py:38-46` (flock) | MEDIA |
| **schema_version check** | `src/infrastructure/alias_loader.py:39-40` | `src/application/use_cases.py:647-648` | BAJA |
