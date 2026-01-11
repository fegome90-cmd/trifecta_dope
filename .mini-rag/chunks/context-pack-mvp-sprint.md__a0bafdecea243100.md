## C) Sprint Plan

| Task | Goal | Files | Acceptance |
|:---|:---|:---|:---|
| T1 | Define schema | `src/domain/models.py` | Frozen dataclasses, segment_id field, no mtime |
| T2 | Whole-file chunking | `src/application/chunking.py` | Stable IDs, summary (200 chars) |
| T3 | Build context pack | `src/application/use_cases.py` | Valid JSON, digest ≤2000 tokens, ≤2 chunks |
| T4 | Token budget | `src/application/use_cases.py` | Digest truncated deterministically |
| T5 | ctx search | `src/application/search_get_usecases.py` | Score: title=2, summary=1, top-3, tie-break id asc |
| T6 | ctx get | `src/application/search_get_usecases.py` | Returns text or exact error string |
| T7 | CLI commands | `src/infrastructure/cli.py` | JSON output, exit code 1 on error |
| T8 | E2E verification | N/A | build→search→get works, all gates pass |

---
