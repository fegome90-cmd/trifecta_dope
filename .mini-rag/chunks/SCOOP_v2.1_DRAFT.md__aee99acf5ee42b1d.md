## 2) Restricciones duras (No-go zones + validación)

1. **Restricción**: NO background daemons sin supervisión
   Razón: Operational risk - daemon muere silenciosamente, entries se pierden sin recovery
   Test que valida:
   ```bash
   # Verifica que session append NO spawns background process
   ps aux | grep -i "session.*daemon" && exit 1 || exit 0
   ```
   CI gate: NEEDS TEST by 2026-01-10

2. **Restricción**: NO duplicar JSONL files (un solo telemetry.jsonl)
   Razón: Tech debt - sincronización entre dos archivos es fuente de bugs
   Test que valida:
   ```bash
   # Verifica que NO existe session_journal.jsonl
   test ! -f _ctx/session_journal.jsonl
   ```
   CI gate: `tests/acceptance/test_no_duplicate_jsonl.py`

3. **Restricción**: NO romper CLI UX existente (flags actuales deben funcionar)
   Razón: Backward compatibility - scripts/CI dependen de `session append --files`
   Test que valida:
   ```bash
   uv run trifecta session append -s . --summary "test" --files "a.py" 2>&1 | grep -v "error"
   ```
   CI gate: `tests/integration/test_session_append.py`

4. **Restricción**: Query performance < 100ms (p95)
   Razón: UX - agente usa session queries múltiples veces por hora
   Test que valida:
   ```bash
   time uv run trifecta session query -s . --last 5 2>&1 | grep "real.*0m0\.[0-9][0-9]s"
   ```
   CI gate: `tests/performance/test_session_query_latency.py`
