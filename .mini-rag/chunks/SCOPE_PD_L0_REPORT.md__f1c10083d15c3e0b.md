## A) Inventario de componentes

| Componente | Archivo(s) | Función(es) clave | Rol |
|------------|------------|-------------------|-----|
| **ctx sync** | `src/infrastructure/cli.py` | `sync()` | Macro: Build + Validate. Orquestador de indexación. |
| **prime** | `_ctx/prime_*.md` | N/A | Lista de lectura obligatoria y prioritizada (SOT para el agente). |
| **context_pack** | `_ctx/context_pack.json` | `ContextPack` (model) | Almacén de chunks indexados y metadatos del segmento. |
| **chunking** | `src/application/use_cases.py` | `BuildContextPackUseCase` | Ingesta de archivos. En v1 usa `whole_file`. |
| **index** | `context_pack.json` | `index` field | Mapa de búsqueda rápida (preview, title, token_est). |
| **skeleton** | `src/application/context_service.py` | `_skeletonize()` | Genera vista estructural (headers + signatures) on-demand. |
| **LSP hooks** | `src/infrastructure/cli_ast.py` | `symbols()`, `hover()` | Puente hacia el LSP Daemon para info técnica profunda. |
| **telemetry events**| `src/infrastructure/telemetry.py` | `event()`, `flush()` | Registro de latencia, hits y uso de tokens. |

---
