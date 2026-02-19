# HN Benchmark Methodology

## Task Specification

**Goal**: Compare token costs between two approaches to providing context to an AI agent:
- (A) **Baseline Context Dumping**: Dump the entire context pack (all chunks) without using CLI search/get
- (B) **CLI with PCC**: Use `ctx.search` and `ctx.get` to selectively retrieve context

**Queries Used**: 5 vague queries (same queries for both scenarios):
- q01: "telemetry"
- q02: "config"
- q03: "search"
- q04: "error"
- q05: "test"

## Acceptance Criteria Checklist

Both scenarios must satisfy the same acceptance criteria:

- [x] Context pack builds successfully (`trifecta ctx build --segment .`)
- [x] All 5 queries are processed via `ctx.search`
- [x] Metrics are collected for each trial (N=10)
- [x] Results are reproducible (same corpus revision: `ceaf20c62377`)

**PASS Criteria**:
- Baseline: Context pack reads from `_ctx/context_pack.json` successfully, tokens counted via tiktoken
- CLI: `ctx.search` returns ≥1 result for each query

**FAIL-Closed Validation**:
- If baseline fails to read JSON: status=error, exclude from stats
- If zero_hit_rate > 50%: status=invalid, exclude from stats

## Run Parameters

| Parameter | Value |
|-----------|-------|
| Model | minimax-m2.5:free |
| Temperature | N/A (CLI-only, no LLM inference) |
| N Trials | 10 |
| Segment | `.` (current directory) |
| τ (tau) | 0.3 (relevance threshold) |
| Corpus Revision | `ceaf20c62377` |
| Token Encoding | `o200k_base` (tiktoken) |

## Token Counting

Token counting uses **tiktoken** with `o200k_base` encoding for accurate measurement:

### Baseline (Context Dump)
- **baseline_context_tokens**: Full chunk text + delimiters (`--- BEGIN file [chunk_id] ---` ... `--- END ---`) + index reference. This simulates a "dump all context" approach with realistic formatting.
- **baseline_query_tokens**: Tiktoken count of combined query strings (6 tokens for all 5 queries)
- **baseline_total_tokens**: baseline_context_tokens + baseline_query_tokens

### CLI (PCC - ctx.search)
- **pcc_query_tokens**: Tiktoken count of query strings (6 tokens)
- **pcc_tool_args_tokens**: Tiktoken count of tool arguments as JSON (66 tokens)
- **pcc_tool_result_tokens**: Tiktoken count of preview text from search results (478 tokens)
- **pcc_total_tokens**: pcc_query_tokens + pcc_tool_args_tokens + pcc_tool_result_tokens

## Cost Model

**MiniMax M2.5 Free Tier**:
- Input: $0.00 per 1M tokens
- Output: $0.00 per 1M tokens

Note: Since this is a free tier, cost is $0. However, the token counts are still meaningful for comparing efficiency.

## Wall Time Measurement

- **Start**: Before first CLI invocation
- **End**: After last CLI invocation completes
- **Method**: Python `time.time()` with millisecond precision

## Zero-Hit Definition

A **zero-hit** occurs when `ctx.search` returns 0 results above the relevance threshold τ.

- **τ (tau)**: 0.3 (default relevance threshold in Trifecta)
- **Corpus Revision**: Git commit SHA (`ceaf20c62377`) that identifies the exact state
- **Segment ID**: `trifecta_dope` (derived from directory name)

**Zero-Hit Rate**: `(#search calls with 0 hits) / (total search calls)`

## Evidence Sources

- **CLI Version**: `uv run trifecta --version`
- **Git Commit**: `git rev-parse HEAD`
- **Context Pack**: `_ctx/context_pack.json` (written by `trifecta ctx build --segment .`)
- **Benchmark Script**: `scripts/run_hn_benchmark.py`
- **Raw Data**: `data/hn_runs.csv`

## Reproducibility

To reproduce these results:

```bash
cd /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope
uv run python scripts/run_hn_benchmark.py
```

This will:
1. Run 10 baseline trials (context dump)
2. Run 10 CLI trials (ctx.search for each query)
3. Output results to `data/hn_runs.csv`
4. Print summary statistics
