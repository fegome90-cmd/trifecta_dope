| # | Hallazgo | Severidad | Evidencia (archivo:línea) | Impacto | Recomendación |
|---|----------|-----------|---------------------------|---------|---------------|
| 1 | **PATH HYGIENE VIOLATION** | CRÍTICA | `_ctx/context_pack.json` contiene `/Users/felipe_gonzalez/Developer/agent_h` | PII expuesto, no portable | Sanitizar rutas en write + test tripwire |
| 2 | **pytest ImportError (3 files)** | ALTA | `test_ast_lsp_pr2.py:16`, `test_pr2_integration.py:12`, `test_telemetry_extension.py:10` | Tests no ejecutan, feedback perdido | Crear compat shims o arreglar imports |
| 3 | **SymbolInfo no existe** | ALTA | Tests importan `SymbolInfo` de `ast_parser`, grep returns nada | Bloquea tests PR2 | Definir clase o stub compatible |
| 4 | **_relpath privado expuesto** | MEDIA | `test_telemetry_extension.py:10` importa `_relpath` (privado) | Violación encapsulación | Usar API pública o re-exportar |
| 5 | **LSP output skeleton-only** | MEDIA | `cli_ast.py:259-268` siempre retorna skeleton, ignora response LSP real | LSP no aporta valor real | Retornar response LSP o quitar daemon |
| 6 | **ast symbols FILE_NOT_FOUND** | MEDIA | `trifecta ast symbols sym://python/mod/context_service` → error | Feature L1 rota | Corregir SymbolResolver |
| 7 | **Lock mechanisms duplicados** | BAJA | `fcntl.flock` (file_system_utils.py:40) vs `fcntl.lockf` (lsp_daemon.py:50) | Confusión, dos APIs | Docum
