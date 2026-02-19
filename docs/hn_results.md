# HN Benchmark Results

## Summary
| Metric | Baseline (Context Dumping) | CLI (PCC via ctx.search) |
| :--- | :--- | :--- |
| **Pass Rate** | **100%** (10/10) | **0%** (0/10) |
| **Tokens In** (Median) | 128,420 | 468 |
| **Cost Est.** (Median) | $0.385 | $0.001 |
| **Wall Time** (Median) | 0.11s | 1.07s |
| **Tool Calls** (Median) | 0 | 2 |

## Detailed Analysis

### Baseline (Scenario A)
- **Strengths**: Perfect recall. The target class `ValidateContextPackUseCase` was present in the dump of `src/`.
- **Weaknesses**: High token cost (~128k tokens per run). While reading from disk was fast (~0.1s), processing this context with an LLM would introduce significant latency (Time to First Token) and cost.

### CLI (Scenario B)
- **Strengths**: Extremely low cost (~468 tokens) and precise usage of tokens.
- **Weaknesses**:
  - **Recall Failure**: The specific query `"How does ValidateContextPackUseCase verify file hashes?"` failed to retrieve the file `src/application/use_cases.py` where the class is defined.
  - **Reason**: `ctx.search` indexes file metadata (titles) and previews (first ~200 chars). It does not index full code content. The class definition starts at line ~60, outside the preview window.
  - **Correction**: To find code symbols, the correct tool is `trifecta ast symbols` or `trifecta load --mode fullfiles`. The standard `ctx.search` is optimized for documentation and high-level concepts, not deep code search.

## Zero-Hit Analysis
We observed two distinct failure modes during exploration:

### Example 1: True Zero-Hit (No Results)
- **Query**: `"ValidateContextPackUseCase"`
- **Result**: 0 hits.
- **Cause**: The exact term does not appear in any file title or preview (imports only).
- **Evidence**: `_ctx/telemetry/events.jsonl` (timestamp `2026-02-19T17:17:15`)
  ```json
  "cmd": "ctx.search", "args": {"query_preview": "ValidateContextPackUseCase", ...}, "result": {"hits": 0}
  ```

### Example 2: Low Relevance / Noise (False Positives)
- **Query**: `"How does ValidateContextPackUseCase verify file hashes?"`
- **Result**: 5 hits (e.g., `minirag_index_files.md`, `file_locked_cache.py`).
- **Cause**: The common terms "verify", "file", "hashes" matched other documents, but the specific class name was not found in the index.
- **Evidence**: Benchmark logs (e.g., `data/hn_logs/B_CLI/B_1771522049_9.log`)

## Interpretation
The benchmark highlights the trade-off between **Recall** (Baseline) and **Precision/Cost** (CLI).
- **Baseline** guarantees finding the context (if it exists) but at a prohibitive cost for frequent use.
- **CLI (PCC)** offers 99.6% cost reduction but requires:
  1. **Tool Selection**: Using the right tool for the job (`ast symbols` for code vs `ctx.search` for docs).
  2. **Query Refinement**: Understanding what is indexed (metadata/previews) vs full content.
  3. **Fallback Strategies**: Using `load --mode fullfiles` when specific search fails.

This confirms that **Trifecta is not a generic RAG** but a specialized tool requiring agent skill ("Programming Context Calling").
