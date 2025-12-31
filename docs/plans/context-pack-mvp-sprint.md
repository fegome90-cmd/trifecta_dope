# Context Pack MVP Sprint Plan

**Date:** 2025-12-31  
**Status:** READY FOR EXECUTION

---

## A) Contract Summary

1. **Naming Contract (3+1):** `skill.md` + `_ctx/{agent,prime,session}_{segment_id}.md`
2. **Segment ID:** `normalize_segment_id(raw): strip() → spaces→- → [^a-zA-Z0-9_-]→_ → lower() → fallback "segment"`
3. **Gates:** validate_segment_structure, validate_segment_fp, validate_agents_constitution, scan_legacy
4. **Result Monad:** Business logic returns `Ok[T] | Err[E]`
5. **try/except:** Only at boundaries (FS/JSON) → deterministic Err
6. **Legacy:** ZERO debt (`docs/legacy_manifest.json = []`)

---

## B) Schema v1

```json
{
  "schema_version": 1,
  "segment_id": "debug_terminal",
  "created_at": "2025-12-31T15:00:00Z",
  "source_files": [
    {"path": "skill.md", "sha256": "abc...", "chars": 2500}
  ],
  "digest": [
    {"doc": "skill", "chunk_id": "skill:a1b2c3d4e5", "summary": "Core rules..."}
  ],
  "index": [
    {"id": "skill:a1b2c3d4e5", "doc": "skill", "title": "Core Rules", "token_est": 625}
  ],
  "chunks": [
    {"id": "skill:a1b2c3d4e5", "doc": "skill", "title": "Core Rules", "text": "# Core...", "token_est": 625}
  ]
}
```

**ID Format:** `{doc}:{sha256(text)[:10]}`  
**Errors:** `"Context pack not found at {path}"`, `"Context pack is invalid JSON"`, `"Chunk not found: {id}"`

---

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

## D) Exit Criteria

- [ ] Schema uses `segment_id`, no `mtime`
- [ ] Chunk IDs: `{doc}:{sha256(text)[:10]}`
- [ ] Digest: ≤2 chunks, ≤2000 tokens
- [ ] Search: score-based ranking (title=2, summary=1)
- [ ] Error strings exact and deterministic
- [ ] 140+ tests pass
- [ ] Zero legacy debt
- [ ] E2E: build→search→get verified
