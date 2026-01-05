## APÉNDICE B: Dependencias Externas

| Dependencia | Versión | Propósito | Risk | Fallback |
|-------------|---------|-----------|------|----------|
| `fcntl` (stdlib) | Python 3.12+ | File locking (POSIX) | LOW (Windows no soporta) | Skip locking en Windows con warning |
| `hashlib` (stdlib) | Python 3.12+ | SHA256 para manifest integrity | NONE | N/A |
| `subprocess` (stdlib) | Python 3.12+ | Background task spawn | LOW (shell injection risk) | Sanitize args con shlex.quote |
| `pyright` (LSP, opcional) | 1.1.350+ | AST events para bundles | HIGH (external binary) | Graceful degradation si no disponible |
| `pyyaml` (existente) | 6.0+ | Policy YAML parsing | NONE (ya usado) | N/A |
| `dataclasses` (stdlib) **(v1.1)** | Python 3.12+ | Result monad (Ok/Err) | NONE | N/A (ya implementado) |
| `typing` (stdlib) **(v1.1)** | Python 3.12+ | TypeAlias para Result | NONE | N/A |

**Nota**: NO agregar dependencias nuevas pesadas (ej: tree-sitter, numpy) para MVP. Usar stdlib siempre que sea posible. **PCC Metrics y Result Monad ya están en codebase (v1.1).**

---
