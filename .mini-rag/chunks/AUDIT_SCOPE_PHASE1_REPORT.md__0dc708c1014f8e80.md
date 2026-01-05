## A) Scope Map

| Feature | Ruta CLI | Archivo(s) Principal(es) | Archivos Soporte |
|---------|----------|-------------------------|------------------|
| **ctx sync** | `trifecta ctx sync` | `src/application/use_cases.py` | `src/infrastructure/cli.py:280-320` |
| **ctx search** | `trifecta ctx search` | `src/application/context_service.py:52-109` | `src/infrastructure/cli.py:322-360` |
| **ctx get** | `trifecta ctx get` | `src/application/context_service.py:111-223` | `src/infrastructure/cli.py:362-450` |
| **PD L0 Skeleton** | `--mode skeleton` | `src/application/context_service.py:265-301` | N/A |
| **PD L1 AST hover** | `trifecta ast hover` | `src/infrastructure/cli_ast.py:182-298` | `src/infrastructure/lsp_daemon.py` |
| **PD L1 AST symbols** | `trifecta ast symbols` | `src/infrastructure/cli_ast.py:31-175` | `src/application/ast_parser.py` |
| **LSP Daemon** | (implicit) | `src/infrastructure/lsp_daemon.py:25-180` | `src/infrastructure/daemon_paths.py` |
| **Telemetría** | (todos los comandos) | `src/infrastructure/telemetry.py:12-95` | `_ctx/telemetry/events.jsonl` |
| **Context Pack Schema** | `context_pack.json` | `src/domain/context_models.py:39-48` | `src/domain/models.py:100-105` |

---
