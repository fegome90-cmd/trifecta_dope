# Search Guidance Baseline Report (Phase 1.1)

**Date**: 2026-01-05
**Dataset**: `docs/datasets/search_queries_v1.yaml` (30 queries)
**Metric Source**: `_ctx/metrics/search_dataset_v1_summary.json`
**Execution**: `bash scripts/run_search_dataset.sh docs/datasets/search_queries_v1.yaml`

## Scope Note
In Phase 1, we measured `hit_rate`, `avg_hits`, and `unique_paths_avg`. **We did not use Score as a gate** due to heuristic variability. The focus is on binary recall (Zero Hits vs Any Hits).

## Metrics Baseline

| Class | Count | Hit Rate | Avg Hits | Unique Paths Avg |
|-------|-------|----------|----------|------------------|
| **VAGUE** | 10 | 0.20 | 0.30 | 0.30 |
| **SEMI** | 10 | 0.50 | 1.10 | 1.00 |
| **GUIDED** | 10 | 0.70 | 0.90 | 0.80 |

## Evidence Paths
All commands executed were logged verbatim.

- **Baseline Mini (Vague)**: `_ctx/logs/f1_1_fix/baseline_q00_vague.log`
- **Baseline Mini (Guided)**: `_ctx/logs/f1_1_fix/baseline_q01_guided.log`
- **Dataset Logs**: `_ctx/logs/search_dataset_v1/*.log`
- **Summary JSON**: `_ctx/metrics/search_dataset_v1_summary.json`

## Observations
1.  **Critical Failure in Vague Queries**: 80% failure rate (Hit Rate 0.20).
2.  **Inconsistent Semi-Guided**: 50% failure rate.
3.  **Gap in Guided**: 30% failure rate despite specific intent anchors.

## Verdict: PASS
The baseline confirms the hypothesis with reproducible evidence. The runner successfully executed 30 queries with full logging, and the parser produced a compliant summary JSON. The +50pp gap between Vague and Guided hit rates validates the "Central Telefónica" initiative.
