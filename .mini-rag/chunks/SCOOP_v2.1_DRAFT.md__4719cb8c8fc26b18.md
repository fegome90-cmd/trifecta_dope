Dataset:
   - Tipo: Test suite existente
   - Tamaño: 15 integration tests
   - Worst-case: Todos los tests fallan
   - Representativo: Tests cubren comandos críticos
   Umbral: FAIL si > 0% (cero tolerancia a regresión)
   Consecuencia: Block merge + rollback

2. **Métrica**: Data loss rate
   Definición: % de session entries perdidas por fallas de write
   Fórmula: `(failed_writes / attempted_writes) * 100`
   Comando:
   ```bash
   # Check telemetry for failed session.entry writes
   jq -c 'select(.cmd == "session.entry" and .result.status == "error")' \
     _ctx/telemetry/events.jsonl | wc -l
   ```
   Dataset:
   - Tipo: Telemetry under stress
   - Tamaño: 1000 append operations
   - Worst-case: Concurrent writes, disk full
   - Representativo: Normal + stress scenarios
   Umbral: FAIL si > 0.1% (max 1 loss per 1000 writes)
   Consecuencia: Rollback + fix before merge

3. **Métrica**: Privacy leak rate
   Definición: % de outputs que contienen paths absolutos
   Fórmula: `(outputs_with_leaks / total_outputs) * 100`
   Comando:
   ```bash
   uv run trifecta session query -s . --all | \
     rg "/Users/|/home/" && echo "LEAK" || echo "CLEAN"
   ```
   Dataset:
   - Tipo: All session entries
   - Tamaño: All
   - Worst-case: Error messages con stack traces
   - Representativo: SÍ
   Umbral: FAIL si > 0% (zero tolerance)
   Consecuencia: Block release + audit

---
