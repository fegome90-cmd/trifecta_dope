## 4) Workflows críticos (output contract + JSON schema)

1. **Comando**:
   ```bash
   uv run trifecta session append -s . --summary "Fixed bug" --type debug --files "a.py" --commands "pytest" --outcome success --tags "lsp"
   ```
   Uso real: Agente registra task completada después de debugging session

   Output Contract (JSON Schema):
   ```json
   {
     "type": "object",
     "required": ["status", "message"],
     "properties": {
       "status": {"type": "string", "enum": ["ok", "error"]},
       "message": {"type": "string"},
       "entry_id": {"type": "string", "pattern": "^session:[a-f0-9]{10}$"}
     }
   }
   ```

   Output válido ejemplo:
   ```json
   {"status": "ok", "message": "✅ Appended to telemetry", "entry_id": "session:abc1234567"}
   ```

   Regresión (ejemplos INVÁLIDOS):
   - `{"status": "error", "message": "File not found"}` (NO debe fallar silenciosamente)
   - Output sin entry_id (no se puede verificar write)

   Test E2E:
   ```bash
   pytest tests/e2e/test_session_append_workflow.py -v
   ```

2. **Comando**:
   ```bash
   uv run trifecta session query -s . --type debug --last 10
   ```
   Uso real: Agente busca últimas 10 entries de debugging para contexto

   Output Contract (JSON Schema):
