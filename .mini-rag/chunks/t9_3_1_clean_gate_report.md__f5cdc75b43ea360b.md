### Raw Output

```
================================================================================
EVALUATION REPORT: ctx.plan
================================================================================
Dataset: /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/docs/plans/t9_plan_eval_tasks_v2_l1.md
Dataset SHA256: fa60cff2fccb4cb1
Dataset mtime: 2025-12-31T13:19:44.799964
Segment: .
Total tasks: 10

Distribution (MUST SUM TO 10):
  feature:  10 (100.0%)
  alias:    0 (0.0%)
  fallback: 0 (0.0%)
  ─────────────────────────────
  total:    10 (100.0%)

Computed Rates:
  feature_hit_rate:       100.0%
  alias_hit_rate:         0.0%
  fallback_rate:          0.0%
  true_zero_guidance_rate: 0.0%

Examples (hits with selected_feature):
  1. [feature] 'feature:observability_telemetry show me hit rate'
     → observability_telemetry (6 chunks, 3 paths)
  2. [feature] 'feature:context_pack explain the build process'
     → context_pack (6 chunks, 2 paths)
  3. [feature] 'feature:cli_commands list all typer commands'
     → cli_commands (2 chunks, 1 paths)

✅ GO (Gate-L1): All criteria passed
   ✓ feature_hit_rate 100.0% >= 95%
   ✓ fallback_rate 0.0% <= 5%
   ✓ true_zero_guidance_rate 0.0% = 0%
```
