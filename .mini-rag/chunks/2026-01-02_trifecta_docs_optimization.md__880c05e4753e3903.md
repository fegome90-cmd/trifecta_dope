#### ELIMINAR (22 líneas)

1. **L90-93: Resources (On-Demand)** → Duplicado en agent.md

   ```diff
   - ## Resources (On-Demand)
   - - `@_ctx/prime_trifecta_dope.md` - Lista de lectura obligatoria
   - - `@_ctx/agent.md` - Stack técnico y gates
   - - `@_ctx/session_trifecta_dope.md` - Log de handoffs (runtime)
   ```

2. **L52-56: STALE FAIL-CLOSED PROTOCOL** → Mover a agent.md

   ```diff
   - STALE FAIL-CLOSED PROTOCOL (CRITICAL):
   - - Si `ctx validate` falla o `stale_detected=true` -> STOP inmediatamente
   - - Ejecutar: `trifecta ctx sync --segment .` + `trifecta ctx validate --segment .`
   - - Registrar en session.md: "Stale: true -> sync+validate executed"
   - - Prohibido continuar hasta PASS
   ```

3. **L29-50: CRITICAL PROTOCOL** → Simplificar (reducir de 22 a 8 líneas)
