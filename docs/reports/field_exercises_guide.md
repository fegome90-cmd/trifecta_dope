# Field Exercises Evaluation - Continuous Improvement Guide

## Overview

Field Exercises is a **living evaluation system** designed to track search quality metrics over time. Each evaluation run is versioned and documented, creating a scientific record of system evolution.

## Quick Reference

**Current Version**: Run 1 (v1) - Baseline  
**Latest SHA**: `8570e18`  
**Status**: ✅ PASS (0% zero-hit rate vs 30% threshold)

## File Structure

```
eval/
├── field_exercises_v1.yaml          # Dataset (versioned per major changes)
└── scripts/
    └── run_field_exercises_ab.py    # Evaluation runner

docs/reports/
├── field_exercises_scientific_analysis.md  # Main living document (updated each run)
├── field_exercises_changelog.md            # Version history and trends
└── field_exercises_v1_results.md           # Raw results (auto-generated)

_ctx/logs/
├── field_ex_off.log                 # Evidence (OFF mode)
└── field_ex_on.log                  # Evidence (ON mode)
```

## When to Run a New Evaluation

**Required Triggers** (must re-evaluate):
1. Linter configuration changes (anchors, aliases)
2. Major dataset expansion (>20% new queries)
3. Search algorithm modifications

**Optional Triggers** (should re-evaluate):
4. Quarterly health checks
5. Before production releases
6. After significant index updates

## How to Run

### Step 1: Validate Dataset
```bash
cd /path/to/trifecta_dope
uv run python eval/scripts/run_field_exercises_ab.py --validate
```

### Step 2: Execute A/B Evaluation
```bash
# OFF mode (control)
uv run python eval/scripts/run_field_exercises_ab.py --mode off --output _ctx/logs/field_ex_off.log

# ON mode (treatment)
uv run python eval/scripts/run_field_exercises_ab.py --mode on --output _ctx/logs/field_ex_on.log
```

### Step 3: Generate Report
```bash
uv run python eval/scripts/run_field_exercises_ab.py --generate-report
# Outputs: docs/reports/field_exercises_v1_results.md
```

### Step 4: Update Scientific Analysis

**Manual Steps**:
1. Open `docs/reports/field_exercises_scientific_analysis.md`
2. Update results in Abstract (section: Results)
3. Update Section 3 (Results) with new metrics
4. Update diagrams if structure changed
5. Add new findings to Section 4 (Discussion)
6. Update trend analysis if comparing to previous runs

### Step 5: Update Changelog

1. Open `docs/reports/field_exercises_changelog.md`
2. Add new run entry using template (see file)
3. Update trend tables (zero-hit, avg hits, anchor usage)

### Step 6: Commit Evidence

```bash
git add eval/ docs/reports/field_exercises_* _ctx/logs/field_ex_*.log
git commit -m "eval: Field Exercises Run X - [brief summary]

Results:
- Zero-hit: X% (OFF) vs Y% (ON)
- Avg hits: X vs Y (Δ +Z)
- Gate: PASS/FAIL

Key findings: [1-2 sentences]"
```

## Interpreting Results

### Quality Gate

**Threshold**: Zero-hit rate ON < 30%

- **PASS**: System is production-ready
- **FAIL**: Investigate root cause (missing content, linter bugs, dataset issues)

### Effect Size (Cohen's d)

| Value | Interpretation |
|-------|----------------|
| < 0.2 | Negligible |
| 0.2-0.5 | Small |
| 0.5-0.8 | Medium |
| > 0.8 | Large |

**Actionable**: Only effect sizes > 0.5 warrant deployment decisions

### Trend Analysis

Compare current run to previous runs:
- **Zero-hit rate**: Should remain stable or decrease
- **Avg hits**: Increases acceptable if precision maintained
- **Anchor usage**: Target 20-30% (sweet spot)

## Common Scenarios

### Scenario 1: Zero-hit rate increased

**Possible Causes**:
- New queries added (harder test cases)
- Index content removed/changed
- Linter regression

**Actions**:
1. Compare query distribution (technical/conceptual/discovery)
2. Check index size delta
3. Review recent linter commits

### Scenario 2: Anchor usage dropped

**Possible Causes**:
- Anchor config made more conservative
- Queries already well-formed (less need for expansion)
- Detection heuristic undercounting

**Actions**:
1. Add explicit anchor expansion logging (not heuristic)
2. Audit anchor triggers vs dataset
3. Consider increasing expansion aggressiveness

### Scenario 3: Hit count decreased

**Possible Causes**:
- Search limit reduced (max hits per query)
- Index pruned (old content removed)
- Query normalization changed

**Actions**:
1. Check if limit was changed (currently 10)
2. Compare index size
3. Inspect specific queries with largest deltas

## Best Practices

### Dataset Maintenance

- **Version the dataset** when >10% of queries change
- **Keep queries realistic** (based on actual developer needs)
- **Balance categories** (30% technical, 30% conceptual, 40% discovery)

### Evidence Preservation

- **Never overwrite logs** - use versioned names (field_ex_*_v2.log)
- **Commit immediately** after evaluation
- **Link SHA in changelog** for reproducibility

### Scientific Rigor

- **Pre-register hypotheses** in changelog
- **Report all results** (even null findings)
- **Document limitations** (sample size, bias, threats to validity)

## Troubleshooting

### Evaluation fails with "Hash mismatch"

**Fix**: Context pack out of sync
```bash
uv run trifecta ctx sync --segment .
```

### Results differ from last run (same dataset)

**Causes**:
- Index updated (new content indexed)
- Search algorithm changed
- Random tie-breaking (if scores equal)

**Verify**:
```bash
git diff HEAD~1 src/application/search_*.py
```

### Gate fails unexpectedly

**Immediate Actions**:
1. Check logs for systemic failures (all queries failing)
2. Verify linter is active (`TRIFECTA_LINT=1` set)
3. Inspect zero-hit queries manually

**Root Cause Analysis**:
- Re-run single query with verbose output
- Check if issue is query-specific or systemic

## Future Enhancements

- [ ] Automated reporting (CI/CD integration)
- [ ] Multi-repository evaluation
- [ ] Real user query dataset (production sampling)
- [ ] Precision metrics (not just recall)
- [ ] Statistical significance testing (larger N)

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-06  
**Maintained By**: Trifecta Development Team
