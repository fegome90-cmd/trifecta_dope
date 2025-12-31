### Example 2: From Miss → Alias Match

**Task**: "where are the CLI commands defined?"

| Before (T9) | After (T9.2) |
|-------------|--------------|
| selected_feature: `null` | selected_feature: `cli_commands` |
| plan_hit: `false` | plan_hit: `true` |
| selected_by: `fallback` | selected_by: `alias` |
| chunks: `[]` | chunks: `["skill:*"]` |
| paths: `["README.md", "skill.md"]` | paths: `["src/infrastructure/cli.py"]` |
| trigger: N/A | trigger: "cli commands defined" (2 terms matched) |
