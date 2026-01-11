## 3) QUÉ SE DESCARTA (NUNCA EXISTIÓ)

**Estos nunca estuvieron implementados → NO hay borrado, son ideas rechazadas:**

| Feature Propuesta | Estado | Evidencia de NO-EXISTENCIA | Alternativa Adoptada |
|:------------------|:-------|:---------------------------|:---------------------|
| **session_journal.jsonl separado** | Nunca existió | `ls _ctx/session*.jsonl` → No matches (exit 124) | Reutilizar telemetry.jsonl con event type |
| **Auto-detección de tool use** | Nunca existió | `rg "auto.*detect.*tool" src/` → 0 matches (AUDIT:L35-L40) | Flags `--files`, `--commands` (YA EXISTEN) |
| **Background daemon/script** | Nunca existió | `rg "daemon.*session" .` → 0 matches (AUDIT:L42-L47) | Hook síncrono en session append |
| **session query command** | Nunca existió | `rg "def.*session.*query" src/` → exit 1 (no matches) | Comando NUEVO en V1 |
| **session load command** | Nunca existió | `uv run trifecta session load --help` → "No such command 'load'" (exit 2) | Comando NUEVO en V1 |
