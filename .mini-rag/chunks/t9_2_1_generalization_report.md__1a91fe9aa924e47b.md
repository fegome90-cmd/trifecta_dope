### Example 5: Edge case hit
**Task**: "telemetry architecture overview"

| Field | Value |
|-------|-------|
| selected_feature | `arch_overview` |
| selected_by | `alias` |
| match_terms_count | 2 |
| matched_trigger | "repo architecture" (matches "architecture" + "telemetry" as generic terms) |
| chunks | `["prime:*", "agent:*"]` |
| paths | `["README.md", "_ctx/generated/repo_map.md"]` |

**Note**: This matched via "architecture" keyword, but "telemetry" was ignored. Shows multi-concept queries can match partially.

---
