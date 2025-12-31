# T9.3.5 Evaluation Report: Scoring Fix (NO new triggers)

**Date**: 2025-12-31
**Mode**: L2 Specificity Ranking + Single-Word Clamp (NO new triggers)

---

## Executive Summary

| Gate | Status | accuracy_top1 | fallback_rate | alias_rate | nl_trigger_rate |
|------|--------|---------------|---------------|------------|-----------------|
| **Core Gate-NL** | ❌ **NO-GO** | 70.0% | 22.5% >= 20% ❌ | 35.0% <= 70% ✅ | 42.5% |

**Overall Decision**: ❌ **T9.3.5 NO-GO** — fallback rate regressed and accuracy dropped.

**Key Outcomes**:
- Single-word clamp applied (Task #25 "telemetry" now falls back as expected)
- L2 specificity ranking in place (score, specificity, priority)
- **symbol_surface regressed**: TP=2 → 0 (Tasks #17, #35 now fallback)

**Constraints Adhered To**:
- NO new nl_triggers added
- NO aliases.yaml edits
- NO dataset changes
- NO threshold changes
- NO embeddings/stemming

---

## Commands Executed (Reproducible)

```bash
# 1. Apply L2 specificity ranking + single-word clamp
# Modified: src/application/plan_use_case.py
# - Sort by (score, specificity, priority)
# - Clamp top single-word trigger if no support terms
# - Expose l2_blocked + l2_block_reason for telemetry

# 2. Run evaluation
cd /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/t9-3-5-audit-fix
uv run trifecta ctx eval-plan -s . --dataset docs/plans/t9_plan_eval_tasks_v2_nl.md
```

---

## NL Evaluation Results (T9.3.5)

### Raw Output

```
================================================================================
EVALUATION REPORT: ctx.plan
================================================================================
Dataset: /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/t9-3-5-audit-fix/docs/plans/t9_plan_eval_tasks_v2_nl.md
Dataset SHA256: 610e7bc4ebf14ad2
Dataset mtime: 2025-12-31T14:57:19.475178
Segment: .
Total tasks: 40

Distribution (MUST SUM TO 40):
  feature (L1):   0 (0.0%)
  nl_trigger (L2): 17 (42.5%)
  alias (L3):      14 (35.0%)
  fallback (L4):   9 (22.5%)
  ─────────────────────────────
  total:          40 (100.0%)

Computed Rates:
  feature_hit_rate:       0.0%
  nl_trigger_hit_rate:    42.5%
  alias_hit_rate:         35.0%
  fallback_rate:          22.5%
  true_zero_guidance_rate: 0.0%
  plan_accuracy_top1:     70.0% (28/40 correct)

Top Missed Tasks (fallback): 9 total
  1. how is the Telemetry class constructed
  2. the thing for loading context
  3. how does it work
  4. telemetry
  5. where to find code
  6. architecture
  7. implement something
  8. telemetry architecture overview
  9. symbols in the telemetry module and their relationships

Examples (hits with selected_feature):
  1. [nl_trigger] 'can you show me the token counting logic'
     → token_estimation (2 chunks, 0 paths)
  2. [nl_trigger] 'where would i find stats about search performance'
     → observability_telemetry (3 chunks, 0 paths)
  3. [alias] 'explain how primes organize the reading list'
     → prime_indexing (3 chunks, 0 paths)

❌ NO-GO (Gate-NL): Some criteria failed
   ✗ fallback_rate 22.5% >= 20%
   ✗ feature_hit_rate 0.0% < 10% (informative)

Passed criteria:
   ✓ true_zero_guidance_rate 0.0% = 0%
   ✓ alias_hit_rate 35.0% <= 70%
```

### NL Metrics Table

| Metric | Before | After | Delta | Target (Core Gate-NL) | Status |
|--------|--------|-------|-------|------------------------|--------|
| plan_accuracy_top1 | 72.5% | **70.0%** | -2.5% | N/A | ❌ Regression |
| nl_trigger_hit_rate | 50.0% | **42.5%** | -7.5% | N/A | ℹ️ Changed |
| alias_hit_rate | 35.0% | **35.0%** | 0.0% | <= 70% | ✅ **PASS** |
| fallback_rate | 15.0% | **22.5%** | +7.5% | < 20% | ❌ **FAIL** |
| true_zero_guidance_rate | 0.0% | 0.0% | — | = 0% | ✅ **PASS** |
| feature_hit_rate | 0.0% | 0.0% | — | >= 10% (informative) | ✗ Below |

### NL Distribution Table

| Outcome | Before | After | Delta |
|---------|--------|-------|-------|
| nl_trigger (L2) | 20 | 17 | -3 |
| alias (L3) | 14 | 14 | 0 |
| fallback (L4) | 6 | 9 | +3 |
| **TOTAL** | **40** | **40** | — |

---

## Changes Made (T9.3.5)

### 1. L2 Ranking Change: Specificity Before Priority

**File**: `src/application/plan_use_case.py`

**Change**:
```python
# Sort by (score desc, specificity desc, priority desc)
filtered_candidates.sort(key=lambda x: (x[2], x[5], x[3]), reverse=True)
```

**Why**: Longer NL triggers should outrank single-word triggers at the same score.

### 2. Single-Word Clamp: Missing Support Terms

**File**: `src/application/plan_use_case.py`

**Rule**:
```python
if best_is_single_word and not best_support_terms_present:
    return None, None, "weak_single_word_trigger", 0, None, debug_info
```

**Support Terms**:
```
{stats, metrics, events, event, latency, p95, p99, throughput,
 perf, performance, jsonl, events.jsonl, telemetry}
```

**Impact**: Single-word queries like "telemetry" now fall back when no support terms appear.

### 3. Telemetry Fields

**File**: `src/application/plan_use_case.py`

**New Fields**:
- `l2_blocked`
- `l2_block_reason`

These are included in telemetry for clamp/tie outcomes.

---

## Before/After Comparison

### Confusion Summary (After)

- symbol_surface: **TP=0, FN=2** (Tasks #17, #35 now fallback)
- observability_telemetry: **TP=5, FP=5** (precision 0.50)
- fallback: **TP=6, FP=3**

See `docs/plans/t9_3_5_confusions.md` for full metrics.

---

## Focused Examples

### 1. Single-Word Query (Expected observability_telemetry)

#### Task #25: "telemetry"

| Version | Got | selected_by | warning | Status |
|---------|-----|-------------|---------|--------|
| Before | observability_telemetry | nl_trigger | None | ❌ Wrong |
| After | fallback | fallback | weak_single_word_trigger | ✅ **Clamped** |

**Why**: Single-word trigger blocked due to missing support terms.

### 2. Telemetry-Class Queries (Expected symbol_surface)

#### Task #17: "how is the Telemetry class constructed"

| Version | Got | selected_by | Status |
|---------|-----|-------------|--------|
| Before | observability_telemetry | nl_trigger | ❌ Wrong |
| After | fallback | fallback | ❌ Regression |

#### Task #35: "symbols in the telemetry module and their relationships"

| Version | Got | selected_by | Status |
|---------|-----|-------------|--------|
| Before | observability_telemetry | nl_trigger | ❌ Wrong |
| After | fallback | fallback | ❌ Regression |

**Why**: Single-word telemetry trigger is clamped; no higher-specificity match exists in current nl_triggers.

---

## Gate Status

| Gate | Decision | Reasoning |
|------|----------|-----------|
| **Core Gate-NL** | ❌ **NO-GO** | fallback 22.5% >= 20% (fail), alias 35.0% <= 70% (pass), true_zero 0% (pass) |

**Overall Assessment**: T9.3.5 clamp behavior is explicit and telemetry fields are present, but eval metrics regressed.

---

## Deliverables

### 1. Confusion Report

Updated: `docs/plans/t9_3_5_confusions.md`

### 2. Eval Output

Saved to: `tmp_plan_test/t9_3_5_after.txt`
