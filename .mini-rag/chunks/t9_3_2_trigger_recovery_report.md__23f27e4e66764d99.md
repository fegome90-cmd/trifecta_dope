```
================================================================================
EVALUATION REPORT: ctx.plan
================================================================================
Dataset: /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/docs/plans/t9_plan_eval_tasks_v2_nl.md
Dataset SHA256: d30f37eab3dd8b56
Dataset mtime: 2025-12-31T13:53:30.489353
Segment: .
Total tasks: 40

Distribution (MUST SUM TO 40):
  feature (L1):   0 (0.0%)
  nl_trigger (L2): 8 (20.0%)
  alias (L3):      24 (60.0%)
  fallback (L4):   8 (20.0%)
  ─────────────────────────────
  total:          40 (100.0%)

Computed Rates:
  feature_hit_rate:       0.0%
  nl_trigger_hit_rate:    20.0%
  alias_hit_rate:         60.0%
  fallback_rate:          20.0%
  true_zero_guidance_rate: 0.0%
  plan_accuracy_top1:     57.5% (23/40 correct)

Top Missed Tasks (fallback): 8 total
  1. list all typer commands available
  2. the thing for loading context
  3. how does it work
  4. telemetry
  5. where to find code
  6. architecture
  7. implement something
  8. telemetry architecture overview

Examples (hits with selected_feature):
  1. [nl_trigger] 'can you show me the token counting logic'
     → token_estimation (4 chunks, 1 paths)
  2. [nl_trigger] 'where would i find stats about search performance'
     → observability_telemetry (6 chunks, 3 paths)
  3. [alias] 'explain how primes organize the rea
