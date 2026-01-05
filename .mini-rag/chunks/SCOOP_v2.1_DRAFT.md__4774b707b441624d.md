## 3) Métricas y gates (reproducible + dataset representativo)

**ÉXITO**:

1. **Métrica**: Query latency (p95)
   Definición: Tiempo desde invocación de `session query` hasta output completo
   Fórmula: `p95(latency_samples)` donde latency = end_time - start_time
   Comando:
   ```bash
   # Ejecutar 100 queries y medir p95
   for i in {1..100}; do
     time uv run trifecta session query -s . --last 5 2>&1 | grep real
   done | awk '{print $2}' | sort -n | tail -n 5 | head -n 1
   ```
   Dataset:
   - Tipo: Real (telemetry actual del proyecto)
   - Tamaño: 10K events mínimo
   - Worst-case incluido: SÍ (query con --all flag sobre 50K events)
   - Representativo: Distribución real de events (70% ctx.*, 20% lsp.*, 10% session)
   Umbral: PASS si < 100ms
   Justificación: Agente usa queries múltiples/hora, >100ms degrada UX

2. **Métrica**: Schema compliance rate
   Definición: % de session entries que pasan validación de JSON schema
   Fórmula: `(valid_entries / total_entries) * 100`
   Comando:
   ```bash
   jq -c 'select(.cmd == "session.entry")' _ctx/telemetry/events.jsonl | \
     jq -s 'map(select(.args.summary != null and .args.type != null)) | length'
   ```
