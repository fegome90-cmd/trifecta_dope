### Example 1: From Fallback → Alias Match

**Task**: "how does the context pack build process work?"

| Before (T9) | After (T9.2) |
|-------------|--------------|
| selected_feature: `null` | selected_feature: `context_pack` |
| plan_hit: `false` | plan_hit: `true` |
| selected_by: `fallback` | selected_by: `alias` |
| chunks: `[]` | chunks: `["skill:*", "prime:*", "agent:*"]` |
| paths: `["README.md", "skill.md"]` | paths: `["src/application/use_cases.py", "src/domain/context_models.py"]` |
| trigger: N/A | trigger: "context pack build" (3 terms matched) |
