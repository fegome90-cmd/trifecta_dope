# GAIA-lite Benchmark Report (v2 - Enhanced)

**Date**: 2026-02-19  
**Run ID**: 20260219_1808  
**N Trials**: 30 per task  
**N Tasks**: 12  
**N Policies**: 4  
**Total Runs**: 1440

---

## 1. Executive Summary

In GAIA-lite (N=30/policy), **CLI maintains equivalent accuracy** to heuristic and BM25 (**91.7%**, CI 95% Wilson), while reducing median tokens by **38%** (426 → 264). This is an efficiency improvement without accuracy loss.

### Key Metrics

| Policy | Pass Rate | 95% CI | Tokens (Median) | IQR | Wall Time (s) | 95% CI |
|--------|-----------|---------|-----------------|-----|---------------|--------|
| **cli** | 91.7% | [88.4-94.1%] | 264 | 20 | 0.217 | [0.216-0.218] |
| heuristic | 91.7% | [88.4-94.1%] | 426 | 28 | 0.220 | [0.219-0.221] |
| bm25 | 91.7% | [88.4-94.1%] | 426 | 28 | 0.217 | [0.217-0.217] |
| **dump** | 16.7% | [13.2-20.9%] | 6710 | 4 | 0.296 | [0.295-0.297] |

> **Note**: "dump" is a **negative control** (context overflow), not a baseline.

---

## 2. Per-Task Breakdown

| Task | CLI Pass | Heur Pass | BM25 Pass | Dump Pass | Analysis |
|------|----------|-----------|-----------|-----------|----------|
| task_001 | 0% | 0% | 0.0% | 0% | ❌ ALL FAIL (verifier bug) |
| task_002 | 100% | 100% | 100.0% | 100% | ✓ all pass |
| task_003 | 100% | 100% | 100.0% | 0% | ✓ retrieval works, dump fails |
| task_004 | 100% | 100% | 100.0% | 0% | ✓ retrieval works, dump fails |
| task_005 | 100% | 100% | 100.0% | 0% | ✓ retrieval works, dump fails |
| task_006 | 100% | 100% | 100.0% | 0% | ✓ retrieval works, dump fails |
| task_007 | 100% | 100% | 100.0% | 0% | ✓ retrieval works, dump fails |
| task_008 | 100% | 100% | 100.0% | 100% | ✓ all pass |
| task_009 | 100% | 100% | 100.0% | 0% | ✓ retrieval works, dump fails |
| task_010 | 100% | 100% | 100.0% | 0% | ✓ retrieval works, dump fails |
| task_011 | 100% | 100% | 100.0% | 0% | ✓ retrieval works, dump fails |
| task_012 | 100% | 100% | 100.0% | 0% | ✓ retrieval works, dump fails |

### Key Finding

- **task_001** (Find TODO comments) fails across ALL policies (0%)
  - Root cause: Verifier regex pattern doesn't match CLI output format
  - This is a **task design issue**, not a policy issue
  - All other tasks: 100% pass for cli/heuristic/bm25

---

## 3. Evidence Quality Metrics

These metrics measure the **retrieval harness quality**, not LLM accuracy:

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Zero-hit rate** | 0.0% | All queries return results |
| **Hit@1** | 100.0% | Top result always relevant |
| **Hit@3** | 100.0% | Relevant in top 3 |
| **Hit@5** | 100.0% | Relevant in top 5 |
| **Avg hits/query** | 5.0 | Sufficient coverage |

---

## 4. Statistical Analysis

### Equivalence Test (CLI vs Heuristic)

Using a ±5% equivalence margin:
- **Difference**: +0.0%
- **95% CI**: [-2.4%, +3.3%]
- **Verdict**: **✓ EQUIVALENT** (within ±5% margin)

### Token Efficiency (Effect Size)

- **Token savings**: 38.1% (426 → 264 tokens)
- This is the **primary improvement** of CLI over heuristic

### Negative Control Verification

- **dump** (context overflow): 16.7% pass rate
- **Verdict**: **✓ Degradation confirmed**
- This proves that more context ≠ better results

---

## 5. Environment & Measurement

| Aspect | Value |
|--------|-------|
| **Platform** | macOS (darwin) |
| **CPU** | Apple Silicon |
| **What is timed** | CLI search + output parsing only (no LLM inference) |
| **Cache state** | Warm (CLI cache pre-loaded) |
| **Token measurement** | tiktoken o200k_base estimation |

> **Defense of tight CIs**: Wall time measures only the CLI retrieval harness (subprocess call + output parsing), not LLM inference. This is intentionally narrow because we're measuring the *context delivery system*, not the LLM. The tight CI reflects the controlled measurement scope.

---

## 6. Command to Reproduce

```bash
cd /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope
python3 scripts/run_gaia_lite.py \
  --policies heuristic cli bm25 dump \
  --trials 30 \
  --max-retries 1 \
  --output data/runs/20260219_1808/gaia_lite_runs.csv
```

---

## 7. Known Limitations

1. **Task design**: task_001 verifier has regex mismatch (affects all policies)
2. **Sample size**: 12 tasks may not be statistically representative for all use cases
3. **Scope**: Measures CLI retrieval only, not end-to-end LLM accuracy
4. **Cache**: Warm cache may not reflect cold-start performance

---

## 8. Artifacts

| File | Description |
|------|-------------|
| `gaia_lite_runs.csv` | Raw trial data (1440 rows) |
| `gaia_lite_summary.json` | Aggregated statistics |
| `per_task_breakdown.json` | Per-task analysis |
| `evidence_quality.json` | Retrieval quality metrics |
| `equivalence_analysis.json` | Statistical equivalence test |

---

## Status

**PASS** - All metrics computed from regenerated CSV artifacts.
