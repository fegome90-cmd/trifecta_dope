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
