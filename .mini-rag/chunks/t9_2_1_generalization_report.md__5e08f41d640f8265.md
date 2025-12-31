### Example 3: Miss due to phrasing
**Task**: "can you show me the token counting logic"

| Field | Value |
|-------|-------|
| selected_feature | `null` |
| selected_by | `fallback` |
| match_terms_count | 0 |
| matched_trigger | `null` |
| chunks | `[]` |
| paths | `["README.md", "skill.md", ...]` (entrypoints) |
| why | L3: No feature match, using entrypoints |

**Root cause**: Trigger "token tracking" doesn't match "token counting logic"
