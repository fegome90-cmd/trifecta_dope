```json
   {
     "type": "object",
     "required": ["status", "actions"],
     "properties": {
       "status": {"type": "string", "enum": ["ok", "error"]},
       "actions": {
         "type": "object",
         "properties": {
           "context_pack_rebuilt": {"type": "boolean"},
           "validated": {"type": "boolean"},
           "session_synced": {"type": "boolean"}
         }
       }
     }
   }
   ```

   Output válido ejemplo:
   ```json
   {"status": "ok", "actions": {"context_pack_rebuilt": true, "validated": true, "session_synced": true}}
   ```

   Regresión:
   - Cambio en estructura de output (rompe scripts que parsean)
   - `ctx sync` NO llama session sync (workflow incompleto)

   Test E2E:
   ```bash
   pytest tests/e2e/test_ctx_sync_workflow.py -v
   ```

4. **Comando**:
   ```bash
   uv run trifecta session load -s . --last 3 --format compact
   ```
   Uso real: Agente carga últimas 3 entries como contexto minimalista

   Output Contract:
   ```json
   {
     "type": "array",
     "items": {
       "type": "object",
       "required": ["ts", "summary", "type"],
       "properties": {
         "ts": {"type": "string"},
         "summary": {"type": "string"},
         "type": {"type": "string"}
       }
     }
   }
   ```

   Output válido ejemplo:
