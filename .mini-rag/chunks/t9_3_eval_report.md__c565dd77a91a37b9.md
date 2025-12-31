### Example 3: Chunk retrieval (was fallback, now alias)
**Task**: "walk through the chunk retrieval flow"

| Before (T9.2.1) | After (T9.3) |
|------------------|---------------|
| selected_feature: `null` | selected_feature: `chunk_retrieval_flow` |
| selected_by: `fallback` | selected_by: `alias` |
| match_terms_count: 0 | match_terms_count: 2 |
| chunks: `[]` | chunks: `["skill:*", "agent:*"]` |
| paths: entrypoints | paths: `["src/application/search_get_usecases.py"]` |
