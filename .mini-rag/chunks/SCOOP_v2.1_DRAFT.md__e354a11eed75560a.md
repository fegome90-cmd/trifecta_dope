2. **Flag**: `--files` debe aceptar CSV (compatibilidad con scripts existentes)
   Output: Parse correcto
   Test:
   ```bash
   uv run trifecta session append -s . --summary "test" --files "a.py,b.py" 2>&1 | grep "ok"
   ```

3. **Telemetry schema**: `ts`, `run_id`, `cmd`, `args`, `result` NO deben cambiar
   Output: Schema estable
   Test:
   ```bash
   jq -c 'keys | sort' _ctx/telemetry/events.jsonl | head -n 1 | \
     grep '["args","cmd","result","run_id","ts","warnings","x"]'
   ```

---
