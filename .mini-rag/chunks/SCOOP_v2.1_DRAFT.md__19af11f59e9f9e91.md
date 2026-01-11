```json
   [
     {"ts": "2026-01-04T11:00", "summary": "Fixed LSP bug", "type": "debug"},
     {"ts": "2026-01-04T10:30", "summary": "Added tests", "type": "develop"},
     {"ts": "2026-01-04T10:00", "summary": "Updated docs", "type": "document"}
   ]
   ```

   Regresión:
   - `compact` mode incluye fields innecesarios (files, commands) → viola token efficiency

   Test E2E:
   ```bash
   pytest tests/e2e/test_session_load_workflow.py -v
   ```

5. **Comando**:
   ```bash
   rg '"cmd": "session.entry"' _ctx/telemetry/events.jsonl | head -n 5
   ```
   Uso real: Debugging manual / auditoría de telemetry

   Output Contract:
   ```
   Cada línea debe ser JSON válido con cmd == "session.entry"
   ```

   Output válido ejemplo:
   ```json
   {"ts": "2026-01-04T11:00:00", "cmd": "session.entry", "args": {...}, "result": {...}}
   ```

   Regresión:
   - Malformed JSON (comas dobles, quotes sin escape)
   - `cmd` != "session.entry" (typo en write logic)

   Test E2E:
   ```bash
   # Validate all session entries are parseable JSON
   rg '"cmd": "session.entry"' _ctx/telemetry/events.jsonl | jq empty
   ```

---
