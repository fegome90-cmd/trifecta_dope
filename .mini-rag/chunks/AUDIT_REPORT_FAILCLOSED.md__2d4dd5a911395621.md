**3b) Performance benchmark**:
```bash
python scripts/bench_session_query.py
# Expected: p95 < 100ms on 10K dataset
```

**Test Gate**:
```bash
# Generate benchmark dataset
uv run python scripts/generate_benchmark_dataset.py --events 10000 --output _ctx/telemetry/events.jsonl

# Run benchmark
uv run python scripts/bench_session_query.py
# MUST: p95 < 100ms
```

---
