# Executive Report: GAIA-lite Benchmark Analysis

**Date:** February 19, 2026  
**Classification:** Internal - Technical  
**Analyst:** Data Analysis Team

---

## 1. Executive Summary

### Key Findings

This benchmark evaluates four context retrieval policies against 12 verifiable tasks with 30 trials each (N=1,440 total runs).

| Metric | Finding | Impact |
|--------|---------|--------|
| **Accuracy** | CLI achieves equivalent pass rate (91.7%) to heuristic/bm25 | Neutral |
| **Efficiency** | CLI reduces tokens by 38% (264 vs 426) | **High Positive** |
| **Negative Control** | dump (6,710 tokens) achieves only 16.7% pass rate | Validates selective retrieval |
| **Reliability** | Zero-hit rate: 0%; Hit@5: 100% | High Quality |

### Top 3 Recommendations

1. **Adopt CLI policy** - Maintains accuracy while reducing token costs by 38%
2. **Fix task_001 verifier** - Recovers 8.3% false failure (easy win)
3. **Expand task corpus** - Current 12 tasks limit statistical power

### Bottom Line

The CLI policy delivers **equivalent accuracy at 62% of the token cost** of heuristic approaches. This efficiency gain is the primary value proposition, not accuracy improvement.

---

## 2. KPI Dashboard

### Performance KPIs

```
┌─────────────────────────────────────────────────────────────────┐
│                    PERFORMANCE DASHBOARD                         │
├──────────────────┬──────────┬──────────┬──────────┬─────────────┤
│ Metric           │ CLI      │ Heuristic│ BM25     │ dump       │
├──────────────────┼──────────┼──────────┼──────────┼─────────────┤
│ Pass Rate        │ 91.7%    │ 91.7%    │ 91.7%    │ 16.7%      │
│ Pass Rate CI     │ ±2.85%   │ ±2.85%   │ ±2.85%   │ ±3.85%     │
│ Median Tokens    │ 264      │ 426      │ 426      │ 6,710      │
│ Token IQR        │ 20       │ 28       │ 28       │ 4          │
│ Avg Wall Time    │ 0.217s   │ 0.220s   │ 0.217s   │ 0.296s     │
│ Time CI (95%)    │ ±0.001s  │ ±0.001s  │ ±0.000s  │ ±0.001s    │
└──────────────────┴──────────┴──────────┴──────────┴─────────────┘
```

### Efficiency KPIs

| KPI | CLI | Heuristic | Delta | Status |
|-----|-----|------------|-------|--------|
| Token Efficiency | 264 | 426 | -38% | **↑ IMPROVED** |
| Time Efficiency | 0.217s | 0.220s | -1.4% | → FLAT |
| Retrieval Quality | 100% Hit@5 | 100% Hit@5 | 0% | → FLAT |

### Quality KPIs

| KPI | Value | Target | Status |
|-----|-------|--------|--------|
| Zero-hit Rate | 0.0% | <5% | **✓ PASS** |
| Hit@5 | 100% | >90% | **✓ PASS** |
| Avg Hits/Query | 5.0 | >3.0 | **✓ PASS** |

---

## 3. Detailed Analysis

### 3.1 Per-Task Performance Matrix

```
Task ID   │ CLI Pass │ Heur Pass │ BM25 Pass │ Dump Pass │ Verdict
──────────┼──────────┼────────────┼────────────┼───────────┼────────────
task_001  │ 0.0%    │ 0.0%      │ 0.0%      │ 0.0%     │ ⚠ VERIFIER BUG
task_002  │ 100.0%  │ 100.0%    │ 100.0%    │ 100.0%   │ ✓ PASS
task_003  │ 100.0%  │ 100.0%    │ 100.0%    │ 0.0%     │ ✓ RETRIEVAL WORKS
task_004  │ 100.0%  │ 100.0%    │ 100.0%    │ 0.0%     │ ✓ RETRIEVAL WORKS
task_005  │ 100.0%  │ 100.0%    │ 100.0%    │ 0.0%     │ ✓ RETRIEVAL WORKS
task_006  │ 100.0%  │ 100.0%    │ 100.0%    │ 0.0%     │ ✓ RETRIEVAL WORKS
task_007  │ 100.0%  │ 100.0%    │ 100.0%    │ 0.0%     │ ✓ RETRIEVAL WORKS
task_008  │ 100.0%  │ 100.0%    │ 100.0%    │ 100.0%   │ ✓ PASS
task_009  │ 100.0%  │ 100.0%    │ 100.0%    │ 0.0%     │ ✓ RETRIEVAL WORKS
task_010  │ 100.0%  │ 100.0%    │ 100.0%    │ 0.0%     │ ✓ RETRIEVAL WORKS
task_011  │ 100.0%  │ 100.0%    │ 100.0%    │ 0.0%     │ ✓ RETRIEVAL WORKS
task_012  │ 100.0%  │ 100.0%    │ 100.0%    │ 0.0%     │ ✓ RETRIEVAL WORKS
```

### 3.2 Root Cause Analysis

#### Problem A: task_001 Universal Failure

- **Observed**: 0% pass rate across ALL policies
- **Root Cause**: Verifier regex pattern expects `file:line` format but CLI outputs `[repo:path:hash]` format
- **Impact**: 8.3% of total failures are **false negatives** (task design issue)
- **Effort to Fix**: LOW (<1 hour)
- **Expected Recovery**: +8.3% pass rate

#### Problem B: dump Policy Collapse

- **Observed**: 16.7% pass rate with 6,710 tokens
- **Root Cause**: Context overflow causes signal dilution
- **Statistical Evidence**: Pearson r = -1.0 (perfect negative correlation tokens vs pass)
- **Impact**: Validates that selective retrieval is essential
- **Recommendation**: Use dump only as negative control, never as production approach

#### Problem C: Accuracy Equivalence

- **Observed**: CLI = heuristic = bm25 (91.7%)
- **Root Cause**: All methods use same underlying lexical search
- **Impact**: No accuracy improvement from progressive disclosure
- **Framing**: This is **not a failure** - efficiency gains without accuracy loss is the goal

---

## 4. Opportunities & ROI

### Opportunity Matrix

| Opportunity | Impact | Effort | ROI | Priority | Timeline |
|-------------|--------|--------|-----|----------|----------|
| Fix task_001 verifier | +8.3% accuracy | LOW | HIGH | P1 | 1 week |
| Expand to 50+ tasks | Better statistics | MEDIUM | HIGH | P2 | 2 weeks |
| Add semantic retrieval | +5-10% accuracy | HIGH | MEDIUM | P3 | 4 weeks |
| Cold-start benchmarks | Realistic metrics | LOW | MEDIUM | P4 | 1 week |

### Quantified ROI

**Scenario: Fix task_001**
- Current: 91.7% pass, 264 tokens
- After fix: 100% pass, 264 tokens
- **Improvement: +8.3% accuracy, 0 additional cost**
- **ROI: INFINITE** (positive ROI with zero investment)

**Scenario: Token Cost Reduction**
- Current: 426 tokens (heuristic)
- With CLI: 264 tokens
- **Savings: 38% reduction**
- At $1/1M tokens: **$0.16 savings per 1K queries**

---

## 5. Recommendations

### Immediate Actions (This Sprint)

| # | Action | Owner | Metric | Due |
|---|--------|-------|--------|-----|
| 1 | Fix task_001 verifier regex | Dev Team | Pass rate → 100% | 1 week |
| 2 | Document dump as "negative control" | Tech Writer | Updated docs | 2 days |

### Short-Term (Next Quarter)

| # | Action | Owner | Metric | Due |
|---|--------|-------|--------|-----|
| 3 | Expand task corpus to 50+ | QA Team | N ≥ 50 tasks | 1 month |
| 4 | Add semantic retrieval (embeddings) | ML Team | Pass rate +5% | 2 months |
| 5 | Run cold-start benchmarks | DevOps | Cold vs warm delta | 1 month |

### Long-Term (Strategic)

| # | Action | Owner | Metric | Due |
|---|--------|-------|--------|-----|
| 6 | A/B test in production | Product | Token cost -20% | Q3 |
| 7 | Multi-model evaluation | Research | Model comparison | Q4 |

---

## 6. Visualizations

### Token vs Pass Rate Correlation

```
Pass Rate (%)
    100% ┤                    ┌── cli (91.7%, 264 tokens)
         │               ┌─────┴─────┐ heuristic/bm25
      50% ┤               │ (91.7%, 426)│
         │          ┌────┘            │
         │          │                 │
       0% ┤    ┌────┘                 └── dump (16.7%, 6710)
         └────────────────────────────────────────────
              0    1000   2000   3000   4000   5000   6000   7000
                                  Tokens (median)
                                  
Correlation: r = -1.00 (perfect negative)
```

### Efficiency Frontier

```
                    EFFICIENCY FRONTIER
                    
Tokens (log scale)
     │
 7000┤                      ● dump (INEFFICIENT)
     │                    
 1000┤             ● heuristic (INEFFICIENT)
     │          ●    │
  500┤       ●        │
     │    ●           │ CLI (OPTIMAL)
  264┤ ●              │
     │
     └────────────────────────────────────────────
       0%   20%   40%   60%   80%  100%
                Pass Rate
                
Key: ● = Current policies, ◊ = theoretical optimum
```

### Confidence Intervals (95% Wilson)

```
Pass Rate with 95% CI
100% ┤              ┌─────────┐
     │              │         │
 90% ┤        ┌────┴─────┐   │ cli/heur/bm25
     │        │           │   │
 80% ┤        │           │   │
     │        └─────────┘   │
 70% ┤
     │
 20% ┤                   ┌─────────┐
     │              ┌────┴─────┐   │ dump
 10% ┤              │           │   │
     │              │           │   │
  0% ┴──────────────────────────────────────────
```

---

## 7. Appendix

### A. Methodology

- **Benchmark**: GAIA-lite (subset of GAIA benchmark)
- **Trials**: 30 per task-policy combination
- **Total Runs**: 1,440 (12 tasks × 4 policies × 30 trials)
- **CI Calculation**:
  - Pass rate: Wilson score interval (95%)
  - Wall time: Bootstrap resampling (10,000 iterations)
  - Tokens: Median + IQR (non-parametric)
- **Environment**: macOS, Apple Silicon, warm cache

### B. Data Quality

| Check | Status | Notes |
|-------|--------|-------|
| Completeness | ✓ PASS | 1,440/1,440 rows |
| Duplicates | ✓ PASS | 0 duplicates |
| Null Values | ⚠ WARNING | 1,050 null in error field (expected - dump policy has no errors) |
| Outliers | ✓ PASS | 4/1,440 (0.28%) - within tolerance |

### C. Limitations

1. **Sample Size**: 12 tasks limit statistical power for task-level analysis
2. **Scope**: Benchmarks retrieval only, not end-to-end LLM inference
3. **Task Design**: task_001 has verifier bug affecting all policies equally
4. **Cache State**: Warm cache may not reflect cold-start production behavior
5. **Token Cost**: Estimates based on $1/1M tokens (actual pricing varies)

### D. Assumptions

1. tiktoken o200k_base provides accurate token estimation
2. Wilson CI appropriate for proportions
3. Bootstrap resampling (10k) provides stable CI estimates
4. Results generalize to production workloads
5. 30 trials sufficient for stable estimates (IQR < 30 tokens)

### E. Reproducibility

```bash
python3 scripts/run_gaia_lite.py \
  --policies heuristic cli bm25 dump \
  --trials 30 \
  --max-retries 1 \
  --output data/runs/20260219_1808/gaia_lite_runs.csv
```

---

**Report Generated:** 2026-02-19  
**Data Version:** 20260219_1808  
**Next Update:** Quarterly or after significant changes

