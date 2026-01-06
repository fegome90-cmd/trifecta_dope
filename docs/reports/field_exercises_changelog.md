# Field Exercises - Scientific Analysis Changelog

**Living Document**: This file tracks all iterations of the Field Exercises evaluation, maintaining a scientific record of system evolution and performance trends.

---

## Evaluation History

### Run 1 (v1) - 2026-01-06 - Baseline A/B Study

**SHA**: `8570e18`  
**Dataset**: 20 queries (6 technical, 6 conceptual, 8 discovery)  
**Conditions**: OFF (--no-lint) vs ON (TRIFECTA_LINT=1)

**Key Results**:
- Zero-hit rate: 0% (OFF) vs 0% (ON)
- Avg hits: 9.30 (OFF) vs 9.40 (ON) → Δ +0.10 (+1.1%)
- Anchor usage: 2/20 (10%)
- Gate: ✅ PASS (0% < 30%)

**Statistical**:
- Cohen's d: 0.125 (negligible effect)
- Perfect recall in both groups (ceiling effect)

**Findings**:
- System operates at optimal recall on well-indexed content
- Linter shows marginal improvement (+1.1%)
- Low anchor expansion (10%) → conservative configuration or well-formed queries

**Recommendations for Next Run**:
1. Expand dataset to N=50-100 queries
2. Add precision metrics (relevance scoring)
3. Include known zero-hit queries (negative cases)
4. Measure anchor expansion with explicit logging (not heuristic)

---

### Run 2 (v2) - [Pending]

**Planned Changes**:
- Increase N to 50 queries
- Add negative test cases (queries expected to fail)
- Implement precision@K metric
- Add explicit anchor expansion telemetry

**Hypotheses to Test**:
- H1: Larger sample reveals statistically significant linter impact
- H2: Anchor expansion aids negative cases more than positive cases
- H3: Precision@3 > Precision@10 (quality vs quantity trade-off)

---

## Versioning Protocol

### When to Create a New Run

Trigger a new evaluation run when:
1. **Linter Config Changes**: Anchor/alias definitions modified
2. **Dataset Expansion**: New queries added or categories rebalanced
3. **Index Changes**: Context pack content substantially updated (>20% delta)
4. **Algorithm Changes**: Query normalization or search logic modified
5. **Periodic Reviews**: Quarterly health checks (even if no changes)

### How to Update This Document

```bash
# 1. Run evaluation
uv run python eval/scripts/run_field_exercises_ab.py --mode off --output _ctx/logs/field_ex_off_v2.log
uv run python eval/scripts/run_field_exercises_ab.py --mode on --output _ctx/logs/field_ex_on_v2.log
uv run python eval/scripts/run_field_exercises_ab.py --generate-report

# 2. Update main analysis doc
# - Add new run section to field_exercises_scientific_analysis.md
# - Update diagrams with latest data
# - Compare trends vs previous runs

# 3. Update this changelog
# - Copy template below
# - Fill in results
# - Add SHA and date

# 4. Commit
git add docs/reports/field_exercises_* _ctx/logs/field_ex_*_v2.log
git commit -m "eval: Field Exercises Run 2 - [brief summary]"
```

### Changelog Entry Template

```markdown
### Run X (vX) - YYYY-MM-DD - [Brief Title]

**SHA**: `xxxxxxx`  
**Dataset**: N queries (breakdown)  
**Conditions**: [describe A/B groups]

**Key Results**:
- Zero-hit rate: X% (OFF) vs Y% (ON)
- Avg hits: X (OFF) vs Y (ON) → Δ +Z
- Anchor usage: X/N (Z%)
- Gate: PASS/FAIL

**Statistical**:
- Cohen's d: X.XXX (interpretation)
- [Other relevant stats]

**Findings**:
- [Main observations]
- [Key insights]
- [Unexpected results]

**Recommendations for Next Run**:
1. [Action 1]
2. [Action 2]

---
```

---

## Trend Analysis (Cross-Run Comparisons)

### Zero-Hit Rate Trend

| Run | Dataset N | OFF | ON | Delta | Status |
|-----|-----------|-----|----|----|--------|
| v1 | 20 | 0.0% | 0.0% | 0.0% | ✅ PASS |
| v2 | [planned] | - | - | - | - |

**Target**: Maintain < 30% across all runs

### Average Hits Trend

| Run | OFF | ON | Δ (Absolute) | Δ (Relative) | Cohen's d |
|-----|-----|----|----|----|----|
| v1 | 9.30 | 9.40 | +0.10 | +1.1% | 0.125 |
| v2 | - | - | - | - | - |

**Target**: Δ > 5% (meaningful improvement) or maintain ceiling performance

### Anchor Expansion Trend

| Run | Usage Count | Usage Rate | Notes |
|-----|-------------|------------|-------|
| v1 | 2/20 | 10% | Heuristic detection |
| v2 | - | - | - |

**Target**: Increase to 20-30% (optimal utilization) without degrading precision

---

## Meta-Analysis Notes

### Limitations Across Runs

1. **Within-Subjects Design**: All runs use same queries for OFF/ON (no randomization)
2. **Single Codebase**: Limited to trifecta_dope repository
3. **Synthetic Dataset**: Not real user queries (may not reflect production distribution)

### Future Methodological Improvements

- [ ] Add between-subjects design (different queries for OFF/ON)
- [ ] Multi-repository evaluation (generalizability)
- [ ] Production A/B testing (real user queries)
- [ ] Longitudinal study (track same queries over time)

---

## References

- **Main Analysis**: [field_exercises_scientific_analysis.md](./field_exercises_scientific_analysis.md)
- **Dataset**: [eval/field_exercises_v1.yaml](../../eval/field_exercises_v1.yaml)
- **Runner**: [eval/scripts/run_field_exercises_ab.py](../../eval/scripts/run_field_exercises_ab.py)
- **Evidence Logs**: `_ctx/logs/field_ex_*.log`

---

**Last Updated**: 2026-01-06  
**Maintainer**: Trifecta Development Team  
**Status**: Active (Run 1 complete, Run 2 planned)
