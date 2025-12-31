```
================================================================================
EVALUATION REPORT: ctx.plan
================================================================================
Dataset: docs/plans/t9_plan_eval_tasks_v2.md
Segment: .
Total tasks: 48

Distribution (MUST SUM TO 40):
  feature:  8 (16.7%)
  alias:    33 (68.8%)
  fallback: 7 (14.6%)
  ─────────────────────────────
  total:    48 (100.0%)

Computed Rates:
  feature_hit_rate:       16.7%
  alias_hit_rate:         68.8%
  fallback_rate:          14.6%
  true_zero_guidance_rate: 0.0%

Top Missed Tasks (fallback): 7 total
  1. the thing for loading context
  2. how does it work
  3. telemetry
  4. where to find code
  5. architecture
  6. implement something
  7. telemetry architecture overview

Examples (hits with selected_feature):
  1. [feature] 'feature:token_estimation show me the formula'
     → token_estimation (4 chunks, 1 paths)
  2. [feature] 'feature:observability_telemetry stats'
     → observability_telemetry (6 chunks, 3 paths)
  3. [feature] 'feature:get_chunk_use_case locate the class'
     → get_chunk_use_case (4 chunks, 1 paths)

✅ GO: All criteria passed
   ✓ fallback_rate 14.6% < 20%
   ✓ true_zero_guidance_rate 0.0% = 0%
   ✓ alias_hit_rate 68.8% <= 70%
   ✓ feature_hit_rate 16.7% >= 10%
```

---
