### False Positives (feature selected when fallback expected: 2)

| Task ID | Task | Expected | Got | Why |
|---------|------|----------|-----|-----|
| 28 | "the prime thing" | prime_indexing | prime_indexing | L3 matched via "prime" term - acceptable |
| 22 | "stats stuff" | observability_telemetry | observability_telemetry | L3 matched via "stats" term - acceptable |
