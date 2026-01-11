## A) Contract Summary

1. **Naming Contract (3+1):** `skill.md` + `_ctx/{agent,prime,session}_{segment_id}.md`
2. **Segment ID:** `normalize_segment_id(raw): strip() → spaces→- → [^a-zA-Z0-9_-]→_ → lower() → fallback "segment"`
3. **Gates:** validate_segment_structure, validate_segment_fp, validate_agents_constitution, scan_legacy
4. **Result Monad:** Business logic returns `Ok[T] | Err[E]`
5. **try/except:** Only at boundaries (FS/JSON) → deterministic Err
6. **Legacy:** ZERO debt (`docs/legacy_manifest.json = []`)

---
