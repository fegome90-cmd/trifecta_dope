## 9) Benchmark Dataset (representativo)

**DATASET**:

Tipo: Synthetic (generado, pero con distribución real-like)

Tamaño: 10,000 events (70% ctx.*, 20% lsp.*, 10% session.entry)

Distribución:
- 7000 ctx events (sync, search, get, validate)
- 2000 lsp events (spawn, request, state_change)
- 1000 session.entry events (100 debug, 400 develop, 300 document, 200 refactor)

**REPRESENTATIVIDAD**:

¿Incluye worst-case? **SÍ**
- Worst-case 1: Query --all sobre 10K events (max scan)
- Worst-case 2: Concurrent writes (10 session append en paralelo)
- Worst-case 3: Malformed JSON en telemetry (recovery test)

¿Distribución == producción? **Aproximado (validated guess)**
- Ratio ctx:lsp:session basado en telemetry actual (500 events muestra)
- Extrapolado a 10K

**Generar**:
```bash
# Script generador
uv run python scripts/generate_benchmark_dataset.py \
  --output _ctx/telemetry_benchmark_10k.jsonl \
  --events 10000 \
  --ctx-ratio 0.7 \
  --lsp-ratio 0.2 \
  --session-ratio 0.1
```

**Ubicación**: `_ctx/telemetry_benchmark_10k.jsonl`

**BENCHMARK**:
```bash
# Copiar benchmark como telemetry activo
cp _ctx/telemetry_benchmark_10k.jsonl _ctx/telemetry/events.jsonl

# Run performance test
time uv run trifecta session query -s . --last 10

# Expected: < 100ms
```

**Output esperado**:
```
real    0m0.047s  (<100ms = PASS)
user    0m0.035s
sys     0m0.012s
```

---
