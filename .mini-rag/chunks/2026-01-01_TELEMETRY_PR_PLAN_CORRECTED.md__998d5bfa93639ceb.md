#### Definition of Done (Ticket 2.1)

- [ ] Tree-sitter Python parser installed: `pip install tree-sitter==0.22.6 tree-sitter-python==0.23.2` (pinned to stable release, not experimental 0.25)
- [ ] Dependencies added to pyproject.toml: `tree-sitter = "~0.22.6"`, `tree-sitter-python = "~0.23.2"`
- [ ] Version rationale documented: 0.23.x is latest stable; 0.25.x requires TS 0.24+ (breaking changes)
- [ ] `SkeletonMapBuilder.parse_python()` uses perf_counter_ns for timing
- [ ] SHA-256 hash computed for cache invalidation
- [ ] Cache hit/miss tracked with `ast_cache_hit_count`, `ast_cache_miss_count`
- [ ] All file paths logged as relative (via `_relpath()`)
- [ ] No file content logged (only sizes, hashes, line counts)
- [ ] Unit test: `test_skeleton_parse_timing` (verify monotonic)
- [ ] Unit test: `test_cache_invalidation` (hash-based)
- [ ] Unit test: `test_path_redaction` (relative paths only)
- [ ] Integration test: parse 50 files in <5s
- [ ] Mypy clean

---
