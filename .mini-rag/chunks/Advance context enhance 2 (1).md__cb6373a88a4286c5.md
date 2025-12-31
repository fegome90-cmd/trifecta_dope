### Metrics to track

1. **Average tokens per turn**: Should decrease by 40-60% compared to loading all context upfront
2. **Citation rate**: % of responses that include `[chunk_id]` references (target: >80%)
3. **Search recall**: % of queries where top-5 results include relevant chunks (target: >90%)
4. **Latency constraint**: Maximum 1 search + 1 get per turn enforced by runtime
