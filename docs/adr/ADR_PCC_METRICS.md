# ADR: PCC (Path Correctness Checker) Metrics

**Status:** Accepted
**Date:** 2025-12-31
**Context:** Tool-calling evaluation with Trifecta ctx.plan

---

## Scope

This ADR defines metrics for evaluating Programmatic Context Calling (PCC) for tool-calling operations in Trifecta. These metrics assess path correctness, fallback behavior, and guardrails effectiveness when using skill/prime/agent contexts.

## Metrics Definitions

### 1. Path Correctness (`path_correct`)

**Definition:** The predicted feature matches the expected feature AND at least one predicted path is in the expected paths list from PRIME `index.feature_map`.

**Formula:**
```
path_correct = (
    expected_feature != "fallback" AND
    predicted_feature == expected_feature AND
    any(predicted_path in expected_paths)
)
```

**Rationale:** Path correctness is critical for tool-calling. Selecting the right feature but pointing to the wrong files results in broken context and failed operations.

### 2. False Fallback (`false_fallback`)

**Definition:** The system selected fallback mode when a feature-based selection was expected (i.e., expected_feature != "fallback" and selected_by == "fallback").

**Formula:**
```
false_fallback = (expected_feature != "fallback" AND selected_by == "fallback")
```

**Rationale:** False fallbacks indicate the system failed to match a known feature when it should have. This is a quality regression - we fell back to generic context when specific context was available.

### 3. Safe Fallback (`safe_fallback`)

**Definition:** The system correctly selected fallback mode when no specific feature was expected (i.e., expected_feature == "fallback" and selected_by == "fallback").

**Formula:**
```
safe_fallback = (expected_feature == "fallback" AND selected_by == "fallback")
```

**Rationale:** Safe fallbacks indicate proper behavior for out-of-domain or general queries where no specific feature applies.

### 4. Determinism (Future)

**Note:** Determinism metrics are not yet implemented but should track:
- Same task → same paths across multiple runs
- Same task → same feature selection across multiple runs
- Impact of tie-breaking rules (tie→fallback, etc.)

## Data Sources

### 1. Evaluation Dataset

**Location:** `docs/plans/t9_plan_eval_tasks.md` (or custom dataset)

**Format:**
```
1. "task description" | expected_feature_id | notes
```

**Purpose:** Provides ground truth expected features for each task.

### 2. PRIME `index.feature_map`

**Location:** `_ctx/prime_*.md` → `### index.feature_map` table

**Format:**
```markdown
| Feature | Chunk IDs | Paths | Keywords |
|---------|-----------|-------|----------|
| telemetry | `skill:*` | `src/infrastructure/telemetry.py` | telemetry |
```

**Purpose:** Maps feature IDs to expected file paths for path correctness validation.

### 3. eval-plan Output

**Command:** `trifecta ctx eval-plan --segment <segment> --dataset <dataset>`

**Relevant Fields:**
- `selected_by`: Mechanism used (feature, nl_trigger, alias, fallback)
- `selected_feature`: Feature ID selected (if any)
- `paths`: List of file paths returned
- `chunk_ids`: List of chunk IDs returned

**Purpose:** Provides system predictions for comparison against ground truth.

## Guardrails

### 1. Tie-Breaking Rule: Tie → Fallback

**Rule:** When multiple features have equal scores, prefer fallback to avoid arbitrary selection.

**Implementation:** Ties are resolved by selecting "fallback" as `selected_by`.

**Rationale:** Deterministic behavior is preferable to random selection. Fallback provides a safe default when confidence is equal.

### 2. True Zero Guidance (`true_zero_guidance_rate`)

**Definition:** Returns empty results (0 chunks, 0 paths, 0 next_steps) - a bug condition.

**Formula:**
```
true_zero_guidance = (chunks_count == 0 AND paths_count == 0 AND next_steps_count == 0)
```

**Guardrail:** `true_zero_guidance_rate` MUST be 0%.

**Rationale:** Empty results are never correct - they break workflows and indicate a bug in the planning logic.

## Metric Aggregation

### Per-Task Evaluation

For each task in the dataset:

```python
evaluate_pcc(
    expected_feature=<from dataset>,
    predicted_feature=<from eval-plan result>,
    predicted_paths=<from eval-plan result>,
    feature_map=<from PRIME>,
    selected_by=<from eval-plan result>
)
# Returns: {path_correct, false_fallback, safe_fallback}
```

### Summary Metrics

```python
summarize_pcc(rows)
# Returns: {
#   path_correct_count,
#   false_fallback_count,
#   safe_fallback_count
# }
```

## Output Format

The `eval-plan` command outputs PCC metrics in a dedicated section:

```
PCC Metrics:
  path_correct_count:    15
  false_fallback_count:  2
  safe_fallback_count:   3
```

## Success Criteria

- **Path Correctness:** > 90% of feature-based tasks should have correct paths
- **False Fallbacks:** < 10% of feature-based tasks should fall back incorrectly
- **True Zero Guidance:** 0% (must be zero)

## Future Extensions

1. **Tool Correctness:** Verify selected tools match expected tools (not just paths)
2. **Instruction Correctness:** Verify generated instructions match expected patterns
3. **Latency Metrics:** Track per-feature latency for optimization
4. **Coverage Analysis:** Identify under-tested features in the dataset

## References

- T9 Plan Evaluation Specification
- PRIME Schema Documentation
- eval-plan Implementation (`src/infrastructure/cli.py`)
- PCC Metrics Implementation (`src/application/pcc_metrics.py`)
