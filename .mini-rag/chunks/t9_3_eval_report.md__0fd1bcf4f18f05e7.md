### Example 1: Token counting (was fallback, now alias)
**Task**: "can you show me the token counting logic"

| Before (T9.2.1) | After (T9.3) |
|------------------|---------------|
| selected_feature: `null` | selected_feature: `token_estimation` |
| selected_by: `fallback` | selected_by: `alias` |
| match_terms_count: 0 | match_terms_count: 2 |
| chunks: `[]` | chunks: `["skill:*", "agent:*"]` |
| paths: entrypoints | paths: `["src/infrastructure/telemetry.py"]` |
