# T9.3.6 Clamp Calibration + Stabilization (Router v1)

## Clamp Impact Report

**Baseline**: T9.3.4 (`5a14a45`)  
**Current**: T9.3.5 (`da63c7b`)  
**Dataset**: `docs/plans/t9_plan_eval_tasks_v2_nl.md` (SHA256 `610e7bc4ebf14ad2178d8c60d0362f813fccab84fba031beb01dddd983636084`)

### Per-Task Transitions (Changed Tasks Only)

| Task ID | Task | Expected | Baseline (T9.3.4) | Current (T9.3.5) | Transition | Was FP Before? | False Fallback Now? |
|--------:|------|----------|------------------|------------------|------------|----------------|---------------------|
| 17 | how is the Telemetry class constructed | symbol_surface | observability_telemetry | symbol_surface | nl_trigger->nl_trigger | yes | no |
| 20 | design a ctx validate workflow | context_pack | observability_telemetry | context_pack | alias->nl_trigger | yes | no |
| 24 | build command not working | context_pack | cli_commands | context_pack | alias->nl_trigger | yes | no |
| 25 | telemetry | observability_telemetry | observability_telemetry | fallback | nl_trigger->fallback | no | yes |
| 35 | symbols in the telemetry module and their relationships | symbol_surface | observability_telemetry | fallback | nl_trigger->fallback | yes | yes |

### Metrics Summary

- FP_reduction = 2 (baseline 8 -> current 6)
- Fallback_increase = 2 (baseline 6 -> current 8)
- FalseFallback_increase = 2
- Net_impact = 0 (FP_reduction 2 - FalseFallback_increase 2)

**Telemetry-specific**:
- observability_telemetry FP baseline: 7
- observability_telemetry FP current: 4

### Evidence (Literal Outputs)

Baseline (T9.3.4):
```
================================================================================
EVALUATION REPORT: ctx.plan
================================================================================

Dataset: /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/t9-3-6-clamp-calibration/docs/plans/t9_plan_eval_tasks_v2_nl.md
Dataset SHA256: 610e7bc4ebf14ad2
Dataset mtime: 2025-12-31T16:45:52.336923
Segment: .
Total tasks: 40

Distribution (MUST SUM TO 40):
  feature (L1):   0 (0.0%)
  nl_trigger (L2): 20 (50.0%)
  alias (L3):      14 (35.0%)
  fallback (L4):   6 (15.0%)
  ─────────────────────────────
  total:          40 (100.0%)

Computed Rates:
  feature_hit_rate:       0.0%
  nl_trigger_hit_rate:    50.0%
  alias_hit_rate:         35.0%
  fallback_rate:          15.0%
  true_zero_guidance_rate: 0.0%
  plan_accuracy_top1:     72.5% (29/40 correct)

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

❌ NO-GO (Gate-NL): Some criteria failed
   ✗ feature_hit_rate 0.0% < 10% (informative)

Passed criteria:
   ✓ fallback_rate 15.0% < 20%
   ✓ true_zero_guidance_rate 0.0% = 0%
   ✓ alias_hit_rate 35.0% <= 70%
```

Current (T9.3.5):
```
================================================================================
EVALUATION REPORT: ctx.plan
================================================================================

Dataset: /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/t9-3-6-clamp-calibration/docs/plans/t9_plan_eval_tasks_v2_nl.md
Dataset SHA256: 610e7bc4ebf14ad2
Dataset mtime: 2025-12-31T16:45:52.336923
Segment: .
Total tasks: 40

Distribution (MUST SUM TO 40):
  feature (L1):   0 (0.0%)
  nl_trigger (L2): 20 (50.0%)
  alias (L3):      12 (30.0%)
  fallback (L4):   8 (20.0%)
  ─────────────────────────────
  total:          40 (100.0%)

Computed Rates:
  feature_hit_rate:       0.0%
  nl_trigger_hit_rate:    50.0%
  alias_hit_rate:         30.0%
  fallback_rate:          20.0%
  true_zero_guidance_rate: 0.0%
  plan_accuracy_top1:     77.5% (31/40 correct)

Top Missed Tasks (fallback): 8 total
  1. the thing for loading context
  2. how does it work
  3. telemetry
  4. where to find code
  5. architecture
  6. implement something
  7. telemetry architecture overview
  8. symbols in the telemetry module and their relationships

Examples (hits with selected_feature):
  1. [nl_trigger] 'can you show me the token counting logic'
     → token_estimation (2 chunks, 0 paths)
  2. [nl_trigger] 'where would i find stats about search performance'
     → observability_telemetry (3 chunks, 0 paths)
  3. [alias] 'explain how primes organize the reading list'
     → prime_indexing (3 chunks, 0 paths)

❌ NO-GO (Gate-NL): Some criteria failed
   ✗ fallback_rate 20.0% >= 20%
   ✗ feature_hit_rate 0.0% < 10% (informative)

Passed criteria:
   ✓ true_zero_guidance_rate 0.0% = 0%
   ✓ alias_hit_rate 30.0% <= 70%
```

---

## Re-eval Output (T9.3.6)

```
================================================================================
EVALUATION REPORT: ctx.plan
================================================================================

Dataset: /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/t9-3-6-clamp-calibration/docs/plans/t9_plan_eval_tasks_v2_nl.md
Dataset SHA256: 610e7bc4ebf14ad2
Dataset mtime: 2025-12-31T16:45:52.336923
Segment: .
Total tasks: 40

Distribution (MUST SUM TO 40):
  feature (L1):   0 (0.0%)
  nl_trigger (L2): 19 (47.5%)
  alias (L3):      12 (30.0%)
  fallback (L4):   9 (22.5%)
  ─────────────────────────────
  total:          40 (100.0%)

Computed Rates:
  feature_hit_rate:       0.0%
  nl_trigger_hit_rate:    47.5%
  alias_hit_rate:         30.0%
  fallback_rate:          22.5%
  true_zero_guidance_rate: 0.0%
  plan_accuracy_top1:     75.0% (30/40 correct)

Top Missed Tasks (fallback): 9 total
  1. the thing for loading context
  2. how does it work
  3. telemetry
  4. where to find code
  5. architecture
  6. implement something
  7. telemetry architecture overview
  8. symbols in the telemetry module and their relationships
  9. explain the event flow from cli to telemetry to reports

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
   ✓ alias_hit_rate 30.0% <= 70%
```

### Before/After Metrics (T9.3.5 -> T9.3.6)

| Metric | T9.3.5 | T9.3.6 | Target | Status |
|--------|--------|--------|--------|--------|
| plan_accuracy_top1 | 77.5% | 75.0% | >= 80% | ❌ | 
| fallback_rate | 20.0% | 22.5% | <= 20% | ❌ |
| nl_trigger_hit_rate | 50.0% | 47.5% | >= 55% | ❌ |
| alias_hit_rate | 30.0% | 30.0% | <= 70% | ✅ |
| true_zero_guidance_rate | 0.0% | 0.0% | = 0% | ✅ |

### Observability Telemetry Metrics

- TP: 4
- FP: 4
- FN: 3
- Precision: 0.50

**FP Guardrail**: T9.3.6 FP=4 (no increase vs T9.3.5 baseline FP=4).
