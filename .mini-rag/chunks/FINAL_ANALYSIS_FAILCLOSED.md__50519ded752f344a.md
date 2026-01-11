## 1) VEREDICTO: ¿QUÉ VAN A BORRAR?

**Se borra (existente):** **NADA.**

**Evidencia literal**:
> AUDIT_REPORT_FAILCLOSED.md:L20: **verdict**: ✅ **CERO features eliminadas**. Todas son extensiones.

**Confirmaciones via comandos reproducibles**:
```bash
# session_append EXISTE
$ uv run trifecta ast symbols "sym://python/mod/src.infrastructure.cli"
{"symbols": [..., {"kind": "function", "name": "session_append", "line": 1281}]}

# session query NO EXISTE (comando nuevo, no borrado)
$ rg "def.*session.*query" src/ --type py
(exit code 1 - no matches)

# session*.jsonl NO EXISTE (nunca existió, no se borra)
$ ls _ctx/session*.jsonl 2>&1
fish: No matches for wildcard '_ctx/session*.jsonl'

# Telemetry EXISTE y SE MANTIENE
$ ls -la _ctx/telemetry/events.jsonl
-rw-r--r-- 1 felipe_gonzalez staff 606421 Jan 4 12:26 _ctx/telemetry/events.jsonl
```

---
