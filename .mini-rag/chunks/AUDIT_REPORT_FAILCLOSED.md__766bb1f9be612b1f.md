### C.3) Dataset benchmark (SCOOP sección 9)

**Propuesta SCOOP**:
```bash
uv run python scripts/generate_benchmark_dataset.py \
  --output _ctx/telemetry_benchmark_10k.jsonl \
  --events 10000 \
  --ctx-ratio 0.7 \
  --lsp-ratio 0.2 \
  --session-ratio 0.1
```

**PROBLEMA**: ❌ Script NO EXISTE

**BLOCKER #5**: Crear `scripts/generate_benchmark_dataset.py`:
