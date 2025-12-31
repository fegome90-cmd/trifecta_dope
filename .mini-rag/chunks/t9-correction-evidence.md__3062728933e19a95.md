### A.3 Get: session_ast.md (Budget Test)

```bash
$ trifecta ctx get --segment /Users/felipe_gonzalez/Developer/AST --ids "session:b6d0238267" --mode excerpt --budget-token-est 900
Retrieved 1 chunk(s) (mode=excerpt, tokens=~195):

## [session:b6d0238267] session_ast.md
---
segment: ast
profile: handoff_log
output_contract:
append_only: true
require_sections: [History, NextUserRequest]
max_history_entries: 10
forbid: [refactors, long_essays]
---
# Session Log - Ast
## Active Session
- **Objetivo**: ✅ Task 11 completada - Integration tests + bug fix
- **Archivos a tocar**: src/integration/, symbol-extractor.ts
- **Gates a correr**: ✅ npm run build, ✅ npx vitest run (34 passing)
- **Riesgos detectados**: SymbolExtractor no detectaba type_identifier - FIXED
---
## TRIFECTA_SESSION_CONTRACT
> ⚠️ **Este contrato NO es ejecutado por el sistema en v1.** Es puramente documental.
```yaml
schema_version: 1
segment: ast
autopilot:
enabled: true
debounce_ms: 800
lock_file: _ctx/.autopilot.lock

... [Contenido truncado, usa mode='raw' para ver todo]
```

**Result:** ✅ PASS - 195 tokens < 900 budget

### A.4 Context Pack Contents

```bash
