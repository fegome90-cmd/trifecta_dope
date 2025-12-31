### Example 3: Architecture Query → Alias Match

**Task**: "overview of the clean architecture layers"

| Before (T9) | After (T9.2) |
|-------------|--------------|
| selected_feature: `null` | selected_feature: `arch_overview` |
| plan_hit: `false` | plan_hit: `true` |
| selected_by: `fallback` | selected_by: `alias` |
| chunks: `[]` | chunks: `["prime:*", "agent:*"]` |
| paths: `["README.md", "skill.md"]` | paths: `["README.md", "_ctx/generated/repo_map.md"]` |
| trigger: N/A | trigger: "architecture layers" (2 terms matched) |

---
