### 6. Expected Feature Labels (NL Dataset)

**File**: `docs/plans/t9_plan_eval_tasks_v2_nl.md`

**New Format**:
```markdown
# Format: task_id | task_string | expected_feature_id | notes

1. "can you show me the token counting logic" | token_estimation | L2 match via "token counting"
2. "where would i find stats about search performance" | observability_telemetry | L2 match via "search performance"
...
21. "the thing for loading context" | fallback | No trigger match
...
```
