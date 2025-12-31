### Example 1: Hit with alias match
**Task**: "where would i find stats about search performance"

| Field | Value |
|-------|-------|
| selected_feature | `observability_telemetry` |
| selected_by | `alias` |
| match_terms_count | 2 |
| matched_trigger | "hit rate" (trigger phrase) |
| chunks | `["skill:*", "agent:*", "ref:RELEASE_NOTES_v1.md"]` |
| paths | `["README.md", "RELEASE_NOTES_v1.md", "src/infrastructure/telemetry.py"]` |
| why | L2: Alias match via 'hit rate' (2 terms) |
