### A.1) Features MODIFICADAS (no eliminadas)

| Feature | Estado Actual | Cambio Propuesto | Evidencia |
|:--------|:--------------|:-----------------|:----------|
| `session append` | **EXISTE** - Escribe a session.md | Extender para escribir TAMBIÉN a telemetry.jsonl | `src/infrastructure/cli.py:L1280-L1341` |
| session.md | **EXISTE** - Archivo markdown append-only | Se mantiene, puede generarse desde JSONL (V2) | `_ctx/session_trifecta_dope.md` (21KB, 397 líneas) |
| Telemetry JSONL | **EXISTE** - events.jsonl con 2186 eventos | Añadir event type `session.entry` | `_ctx/telemetry/events.jsonl` (606KB) |

**verdict**: ✅ **CERO features eliminadas**. Todas son extensiones.

---
