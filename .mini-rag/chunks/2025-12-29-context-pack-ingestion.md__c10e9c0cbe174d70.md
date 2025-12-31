## Critical Fixes Applied

| # | Issue | Fix |
|---|-------|-----|
| 1 | Digest quality | Scoring system instead of first-N chars |
| 2 | ID instability | Normalized hash instead of sequential |
| 3 | Code fence corruption | State machine tracking `in_fence` |
| 4 | Missing metadata | Added source_path, char_count, line_count, etc. |
| 5 | Runtime O(n) lookup | Prepared for SQLite in Phase 2 |
| 6 | No contract | Schema versioning + manifest |

---
