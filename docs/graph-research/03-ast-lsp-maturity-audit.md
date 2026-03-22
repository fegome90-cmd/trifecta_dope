# Auditoría de Consistencia - Madurez AST y LSP

Fecha: 2026-03-13
Objetivo: Resolver contradicción entre afirmaciones de "M1 Production Ready" vs "prototipo/debug script"

---

## A. Resumen Ejecutivo

| Componente | Estado Real | Evidencia |
|------------|-------------|-----------|
| **AST** | ✅ USABLE como base para Graph | Parser estable con cache, 51 tests activos, contrato JSON documentado |
| **LSP Daemon** | ⚠️ USABLE con fallback obligatorio | Fallback a AST integrado, pero NO usar en critical path |
| **Contradicción** | Docs previas mezclan estado con aspiración | Código muestra piezasoperativas pero con limitaciones |

---

## B. AST Real Hoy

### Entry Point en Producción

| Archivo | Función | Uso |
|---------|---------|-----|
| `src/application/ast_parser.py:45` | `SkeletonMapBuilder.build()` | Parser principal |
| `src/infrastructure/cli_ast.py:61` | `trifecta ast symbols` | CLI entrypoint |

### Contrato de Salida (M1)

```json
{
  "status": "ok",
  "segment_root": "/path/to/segment",
  "file_rel": "src/module.py",
  "symbols": [
    {"kind": "class", "name": "MyClass", "line": 10},
    {"kind": "function", "name": "my_func", "line": 20}
  ],
  "cache_status": "hit|miss|error",
  "cache_key": "segment:rel/path:hash:1"
}
```

### Versionado

| Aspecto | Estado |
|---------|--------|
| Cache version | ✅Sí (`CACHE_VERSION = 1` en ast_parser.py:48) |
| Formato versionado | ✅ Clave incluye versión |
| Breaking changes | ❌ No detectadas |

### Comandos CLI que lo Consumen

```
trifecta ast symbols <uri> [--segment .] [--persist-cache]
trifecta ast cache-stats [--segment .]
trifecta ast clear-cache [--segment .]
```

### Tests que lo Cubren

| Test File | Cobertura |
|-----------|-----------|
| `tests/acceptance/test_ast_symbols_returns_real_symbols.py` | End-to-end CLI |
| `tests/unit/test_skeleton_builder_real.py` | Parser unit |
| `tests/unit/test_ast_cache.py` | Cache LRU |
| `tests/integration/test_ast_cache_persist_cross_run_cli.py` | Persistencia |
| `tests/integration/test_ast_cache_telemetry.py` | Telemetría |

**Total: 51 tests relacionados** (resultado de grep)

### Limitaciones Reales

| Limitación | Severidad | Nota |
|-----------|----------|------|
| Solo top-level symbols | Media | No extrae nested classes/functions |
| Solo Python | Baja | No es multi-lenguaje |
| Sin imports analysis | Media | No sigue imports |
| Sin type hints extraction | Baja | Solo signature stub |

### Veredicto: AST

- **USABLE** como base para Graph
- **NO** es "Production Ready" en sentido estricto (limitaciones above)
- **SÍ** tiene contrato estable, tests, cache, y CLI operativo

---

## C. LSP Real Hoy

### Flujo Real de Start/Status/Query

```
trifecta daemon start <repo>
trifecta daemon stop <repo>
trifecta daemon status <repo>
trifecta ast hover <file> <line> <col>
```

### Arquitectura

```
LSPDaemonServer (socket UNIX)
    ├── Lock (fcntl)
    ├── Socket path
    ├── PID file
    └── LSPDaemonClient (spawns subprocess)
            └── LSPClient (pylsp o pyright-langserver)
```

### Operaciones Expuestas

| Método LSP | CLI Exposición | Estado |
|------------|---------------|--------|
| `textDocument/hover` | `trifecta ast hover` | ✅ Operativo |
| `textDocument/didOpen` | Interno | ✅ Operativo |
| `textDocument/definition` | ❌ No expuesto | - |
| `textDocument/completion` | ❌ No expuesto | - |

### Dependencias de Entorno

| Dependencia | Requerida | Fallback |
|-------------|-----------|----------|
| `pylsp` o `pyright-langserver` | ⚠️Sí | AST fallback |
| UNIX socket | ⚠️Sí | No (solo UNIX) |
| TTL configurable | ✅180s default | - |

### Tests de Integración

| Test File | Cobertura |
|-----------|-----------|
| `tests/integration/test_lsp_daemon.py` | Spawn, lock, TTL, cold start |
| `tests/integration/test_lsp_telemetry.py` | Eventos |
| `tests/integration/test_lsp_contract_fallback.py` | Fallback contract |
| `tests/unit/test_lsp_client_strict.py` | Cleanup |

### Fallback a AST

El sistema tiene fallback integrado (lsp_client.py:222-240):

```python
def _emit_fallback(self, requested_method: str, reason: str):
    """Emit lsp.fallback telemetry event when LSP is unavailable."""
    self._log_event(
        "lsp.fallback",
        {"requested_method": requested_method},
        {"status": "fallback_to_ast", "reason": reason},
        0,
        fallback_to="ast",
    )
```

### Limitaciones Reales

| Limitación | Severidad | Nota |
|-----------|----------|------|
| Solo Python LSP | Alta | Solo pylsp/pyright |
| Estado "RELAXED READY" | Alta | No es "FULL READY" |
| Fallback obligatorio | Alta | Critical path NO debe depender |
| UNIX-only | Media | No funciona en Windows |
| TTL 180s | Media | Requiere warmup |

### Veredicto: LSP

- **USABLE como enriquecimiento opcional**
- **NO APT** para critical path (debe haber fallback a AST)
- **RELAXED READY** significa: funcional pero con limitaciones conocidas

---

## D. Contradicciones entre Documentos y Código

### Lo que Decían Docs Previas

> "AST/LSP son prototipos/debug scripts con gap alto"

### Lo que Muestra el Código

| Aspecto | Doc Decía | Código Muestra |
|---------|----------|-----------------|
| Tests | ¿Prototipo? | 51 tests activos |
| CLI | ¿Debug script? | 4 comandos operativos |
| Fallback | ¿No existe? | Integrado y telemetrizado |
| Cache | ¿No existe? | SQLite + LRU + Null |
| Contrato | ¿Inestable? | JSON estable con versionado |

### Lo que la Doc Nueva Afirma

> "AST M1 Production Ready"
> "LSP Daemon operativo con TTL y fallback"

### Análisis

La **doc nueva** tiene razón en que **el código está operativo**, pero:

1. "Production Ready" es optimista dado las limitaciones
2. "RELAXED READY" es el estado correcto del LSP
3. La **doc vieja** mixeaba frustración de desarrollo con estado real

---

## E. Verdad Actual Consolidada

### AST

| Afirmación | Tipo | Notas |
|------------|------|-------|
| Parser estable | ✅True | stdlib ast, top-level only |
| Cache operativo | ✅True | SQLite + LRU |
| CLI usable | ✅True | 4 comandos |
| Contrato versionado | ✅True | CACHE_VERSION = 1 |
| "Production Ready" | ⚠️Exagerado | Limitaciones reales (ver sección B) |

### LSP

| Afirmación | Tipo | Notas |
|------------|------|-------|
|Daemon operativo | ✅True | UNIX socket, TTL 180s |
| Fallback a AST | ✅True | Integrado y telemetrizado |
| "Production Ready" | ❌Falso | Es "RELAXED READY" |
| Safe para critical path | ❌Falso | Fallback obligatorio |

---

## F. Qué Puede Entrar al MVP Graph

### AST - APTO ✅

| Uso | Evaluación |
|-----|------------|
| Nodos del grafo | ✅ Stable, versionado |
| Relaciones estructurales | ⚠️ Solo top-level |
| Cache de símbolos | ✅ SQLite existente |
| CLI de indexación | ✅`trifecta ast symbols` |

### LSP - CON RESTRICCIONES ⚠️

| Uso | Evaluación |
|-----|------------|
| Enriquecimiento opcional | ✅ Safe si hay fallback |
| Hover resolution | ✅`trifecta ast hover` existe |
| Precisión mejorada | ⚠️Solo si LSP disponible |
| Critical path | ❌NO - usar AST fallback |

---

## G. Qué Debe Esperar

### Para Graph v1

| Componente | Status |
|------------|--------|
| AST como base | ✅ Listo para consumir |
| LSP como enriquecimiento | ⚠️ Solo como bonus, no requerido |
| tree-sitter | ❌ No necesario (stdlib ast funciona) |

### Para Graph v2+

- Multi-lenguaje (requiere tree-sitter)
- Nested symbols (requiere extensión parser)
- LSP-based definition lookup (requiere daemon estable)

---

## H. Recomendación de Documentación

### Archivos a Corregir/Archivar

| Archivo | Acción |
|---------|--------|
| `docs/lsp/*.md` | Revisar - contienen narrativas de frustration |
| `docs/ast-lsp-connect/*.md` | Archivar - son análisis antiguos |
| `docs/cli/AST_LSP_DAEMON_USAGE_REPORT.md` | Archivar - docs de debug |
| `agent_trifecta_dope.md` | ✅ Ya tiene "RELAXED READY" correcto |

### Formulación Correcta para Futura Doc

**AST**:
> Sistema de extracción de símbolos Python vía stdlib ast. Cache SQLite versionado. CLI estable. Limitaciones: solo top-level, solo Python.

**LSP**:
> Daemon opcional para enriquecimiento de precisión. Fallback a AST obligatorio. Estado: RELAXED READY (funcional con limitaciones).

---

## I. Cierre

| Pregunta | Respuesta |
|----------|-----------|
| ¿AST es "M1 Production Ready"? | **Parcialmente** - usable pero con limitaciones |
| ¿LSP es "operativo"? | **Sí** - pero "RELAXED READY" no "Production Ready" |
| ¿Puedo usar AST para Graph? | **Sí** - es la base correcta |
| ¿Puedo usar LSP para Graph? | **Sí** - pero solo como enriquecimiento opcional, nunca en critical path |
| ¿Están los docs viejos obsoletos? | **Parcialmente** - contienen narrativas de frustración que mixean con estado real |
