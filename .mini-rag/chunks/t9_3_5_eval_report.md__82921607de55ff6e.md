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
