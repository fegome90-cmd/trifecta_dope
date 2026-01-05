| # | Riesgo | Severidad | Ubicación | Evidencia |
|---|--------|-----------|-----------|-----------|
| 1 | **ContextPack duplicado** | ALTA | `src/domain/context_models.py` vs `src/domain/models.py:100-105` | Dos definiciones distintas (Pydantic vs dataclass) |
| 2 | **Tests con import errors** | MEDIA | `tests/unit/test_ast_lsp_pr2.py`, `test_pr2_integration.py`, `test_telemetry_extension.py` | ImportError: `SymbolInfo`, `SkeletonMapBuilder`, `_relpath` no existen |
| 3 | **segment_id derivation inconsistente** | MEDIA | `compute_segment_id()` vs `normalize_segment_id()` | SHA256 de path vs lógica diferente |
| 4 | **Lock mechanisms duplicados** | MEDIA | `fcntl.lockf` (lsp_daemon) vs `flock` (file_system_utils) | Dos implementaciones diferentes |
| 5 | **ast symbols FILE_NOT_FOUND** | MEDIA | `src/infrastructure/cli_ast.py:31-175` | SymbolResolver no encuentra módulos existentes |
| 6 | **LSP output skeleton-only** | BAJA | `src/infrastructure/cli_ast.py:259-268` | LSP response siempre retorna skeleton, no usa data real |
| 7 | **AST parser stub** | BAJA | `src/application/ast_parser.py:18-32` | tree-sitter removido, retorna fake children |
| 8 | **Daemon zombies potenciales** | MEDIA | `src/infrastructure/lsp_daemon.py:77-95` | TTL de 180s sin verificar si daemon realmente murió |
| 9 | **Socket path no verificado** | BAJA | `/tmp/trifecta_lsp_*.sock` | No se verificó si so
