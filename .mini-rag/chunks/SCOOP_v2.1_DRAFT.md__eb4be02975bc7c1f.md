```json
   {
     "type": "array",
     "items": {
       "type": "object",
       "required": ["ts", "summary", "type", "outcome"],
       "properties": {
         "ts": {"type": "string", "format": "date-time"},
         "summary": {"type": "string", "minLength": 1},
         "type": {"type": "string", "enum": ["debug", "develop", "document", "refactor"]},
         "files": {"type": "array", "items": {"type": "string"}},
         "commands": {"type": "array", "items": {"type": "string"}},
         "outcome": {"type": "string", "enum": ["success", "partial", "failed"]},
         "tags": {"type": "array", "items": {"type": "string"}}
       }
     }
   }
   ```

   Output válido ejemplo:
   ```json
   [
     {
       "ts": "2026-01-04T11:00:00-03:00",
       "summary": "Fixed LSP bug",
       "type": "debug",
       "files": ["src/lsp.py"],
       "commands": ["pytest tests/"],
       "outcome": "success",
       "tags": ["lsp", "daemon"]
     }
   ]
   ```

   Regresión:
   - Output incluye `run_id`, `timing_ms`, `warnings` (campos telemetry no limpiados)
   - `ts` en formato no-ISO (ej: epoch)

   Test E2E:
   ```bash
   pytest tests/e2e/test_session_query_workflow.py -v
   ```

3. **Comando**:
   ```bash
   uv run trifecta ctx sync -s .
   ```
   Uso real: Macro que rebuild context pack + validate + session sync

   Output Contract (same as current - NO DEBE CAMBIAR):
