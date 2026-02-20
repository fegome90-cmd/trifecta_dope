# HN Benchmark Results

## Summary

This benchmark compares two approaches to providing context to an AI agent:
- **(A) Baseline**: Dump the entire context pack (all chunks) - no CLI search/get
- **(B) CLI with PCC**: Use `ctx.search` and `ctx.get` to selectively retrieve context

**Methodology**: See [`docs/hn_methodology.md`](hn_methodology.md)

---

## Results

### Table 1: Tokens and Cost (Median + IQR)

| Metric | Baseline (A) | CLI (B) | Delta |
|--------|-------------|---------|-------|
| tokens_in (context) | 893,363 | 550 | -892,813 |
| tokens_out (query) | 6 | 6 | 0 |
| **total_tokens** | **893,369** | **550** | **-892,813** |
| cost_est | $0.00 | $0.00 | $0.00 |
| pass_rate | 100% | 100% | - |

### Table 2: Time and Latency (Median + IQR)

| Metric | Baseline (A) | CLI (B) | Delta |
|--------|-------------|---------|-------|
| wall_time_s | 0.590 (IQR: 0.021) | 0.958 (IQR: 0.044) | +0.368 |
| tool_calls | 0 | 5 | +5 |
| avg_tool_rtt_ms | N/A | 191.3 (IQR: 8.9) | - |
| p95_tool_rtt_ms | N/A | ~197 | - |
| zero_hit_rate | N/A | 0% | - |

---

## Key Findings

### Token Savings
- **99.9% token reduction** when using CLI with PCC vs full context dump
- Baseline: 893,363 tokens (full context pack with delimiters, tiktoken count)
- CLI: 550 tokens (selective retrieval: 6 query + 66 tool args + 478 tool results)

### Latency Trade-off
- CLI approach takes ~1.6x longer (0.958s vs 0.590s)
- This is due to:
  - Multiple tool calls (5 search calls)
  - CLI overhead per call
  - Average RTT: 191.3ms per tool call

### Zero-Hit Rate
- **0% zero-hit rate** in CLI mode
- All 5 queries returned relevant results:
  - "telemetry" → 3 hits
  - "config" → 3 hits  
  - "search" → 3 hits
  - "error" → 3 hits
  - "test" → 3 hits

---

## Caveats

1. **Token counting**: Uses tiktoken with `o200k_base` encoding for accurate counting
2. **Cost model**: MiniMax M2.5 free tier - cost is $0 for both approaches
3. **Scope**: This benchmark measures context retrieval only, not end-to-end LLM inference
4. **Queries used**: 5 vague queries (telemetry, config, search, error, test)
5. **Segment**: Current repo (`.`) with 349 chunks in context pack
6. **Baseline definition**: Full context pack dump via `_ctx/context_pack.json`

---

## Variance

- Baseline: Near-zero variance (deterministic - same pack every time)
- CLI: Low variance in tool_calls (5 for all runs), low variance in RTT

---

## Evidence

- Raw data: [`data/hn_runs.csv`](data/hn_runs.csv)
- Methodology: [`docs/hn_methodology.md`](hn_methodology.md)
- Benchmark script: [`scripts/run_hn_benchmark.py`](scripts/run_hn_benchmark.py)
- Corpus revision: `ceaf20c62377`
