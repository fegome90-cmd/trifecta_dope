```
================================================================================
EVALUATION REPORT: ctx.plan
================================================================================
Dataset: /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/docs/plans/t9_plan_eval_tasks_v2_nl.md
Dataset SHA256: d7c9fd9acbd2b407
Dataset mtime: 2025-12-31T13:19:29.395240
Segment: .
Total tasks: 40

Distribution (MUST SUM TO 40):
  feature:  0 (0.0%)
  alias:    33 (82.5%)
  fallback: 7 (17.5%)
  ─────────────────────────────
  total:    40 (100.0%)

Computed Rates:
  feature_hit_rate:       0.0%
  alias_hit_rate:         82.5%
  fallback_rate:          17.5%
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
  1. [alias] 'can you show me the token counting logic'
     → token_estimation (4 chunks, 1 paths)
  2. [alias] 'where would i find stats about search performance'
     → observability_telemetry (6 chunks, 3 paths)
  3. [alias] 'explain how primes organize the reading list'
     → prime_indexing (4 chunks, 2 paths)

❌ NO-GO (Gate-NL): Some criteria failed
   ✗ alias_hit_rate 82.5% > 70%
   ✗ feature_hit_rate 0.0% < 10% (informative)

Passed cri
