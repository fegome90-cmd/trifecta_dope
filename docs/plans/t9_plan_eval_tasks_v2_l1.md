# T9.3.1 Plan Evaluation Dataset v2 - L1 (Explicit Feature Selection)

**Purpose**: Test explicit feature:<id> syntax for feature_hit_rate metric
**Date**: 2025-12-31
**Total Tasks**: 10
**Mode**: L1-only - EVERY task MUST contain "feature:<id>" with valid id

---

## L1 Explicit Feature Queries (10)

Test explicit feature:<id> syntax for feature_hit_rate metric.

<!-- Task IDs: T9V2L1-001 to T9V2L1-010 -->

1. "feature:observability_telemetry show me hit rate"
2. "feature:context_pack explain the build process"
3. "feature:cli_commands list all typer commands"
4. "feature:search show the SearchUseCase class"
5. "feature:stats explain zero-hits analysis"
6. "feature:arch_overview describe the clean architecture layers"
7. "feature:token_estimation show me the formula"
8. "feature:prime_indexing explain the reading list"
9. "feature:chunk_retrieval_flow how does it work"
10. "feature:get_chunk_use_case locate the class"

---

## Dataset Identity (Anti-Gaming)

- **Type**: L1-only (explicit feature: prefix required)
- **Total tasks**: 10
- **Stable IDs**: T9V2L1-001 to T9V2L1-010
- **No mixing**: Natural language queries are in separate dataset (t9_plan_eval_tasks_v2_nl.md)
- **Feature coverage**: 10 distinct features from aliases.yaml

---

## L1 Syntax Rules

Each task follows the pattern:
- `feature:<feature_id> <natural language query>`

Where `<feature_id>` must be a valid feature ID defined in aliases.yaml:
- observability_telemetry
- context_pack
- cli_commands
- search
- stats
- arch_overview
- token_estimation
- prime_indexing
- chunk_retrieval_flow
- get_chunk_use_case

The L1 matcher in ctx.plan will:
1. Extract the feature_id from the task
2. Verify it exists in aliases.yaml (fail-closed)
3. Return the bundle for that feature directly
4. Set selected_by = "feature"
