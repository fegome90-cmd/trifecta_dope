```
================================================================================
EVALUATION REPORT: ctx.plan
================================================================================
Dataset: /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/docs/plans/t9_plan_eval_tasks_v2_nl.md
Dataset SHA256: 610e7bc4ebf14ad2
Dataset mtime: 2025-12-31T14:10:24.794518
Segment: .
Total tasks: 40

Distribution (MUST SUM TO 40):
  feature (L1):   0 (0.0%)
  nl_trigger (L2): 22 (55.0%)
  alias (L3):      12 (30.0%)
  fallback (L4):   6 (15.0%)
  ─────────────────────────────
  total:          40 (100.0%)

Computed Rates:
  feature_hit_rate:       0.0%
  nl_trigger_hit_rate:    55.0%
  alias_hit_rate:         30.0%
  fallback_rate:          15.0%
  true_zero_guidance_rate: 0.0%
  plan_accuracy_top1:     77.5% (31/40 correct)

Top Missed Tasks (fallback): 6 total
  1. the thing for loading context
  2. how does it work
  3. where to find code
  4. architecture
  5. implement something
  6. telemetry architecture overview

Examples (hits with selected_feature):
  1. [nl_trigger] 'can you show me the token counting logic'
     → token_estimation (2 chunks, 0 paths)
  2. [nl_trigger] 'where would i find stats about search performance'
     → observability_telemetry (3 chunks, 0 paths)
  3. [alias] 'explain how primes organize the reading list'
     → prime_indexing (3 chunks, 0 paths)
