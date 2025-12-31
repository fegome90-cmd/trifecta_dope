### Example 4: GetChunkUseCase (was fallback, now alias)
**Task**: "locate the GetChunkUseCase implementation"

| Before (T9.2.1) | After (T9.3) |
|------------------|---------------|
| selected_feature: `null` | selected_feature: `get_chunk_use_case` |
| selected_by: `fallback` | selected_by: `alias` |
| match_terms_count: 0 | match_terms_count: 2 |
| chunks: `[]` | chunks: `["skill:*", "agent:*"]` |
| paths: entrypoints | paths: `["src/application/search_get_usecases.py"]` |
