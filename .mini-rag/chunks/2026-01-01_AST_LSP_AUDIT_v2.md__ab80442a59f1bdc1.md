### T1: AST Skeleton Map + Tree-sitter Integration (4 días)

**Deliverables:**
1. `src/infrastructure/ast_lsp.py`: SkeletonMapBuilder class
2. `tests/unit/test_ast_skeleton.py`: 8 unit tests
3. `tests/fixtures/mini_repo/`: Test fixture with 3 functions, 1 class
4. Benchmark script: Parse 5k files in <5s async

**Definition of Done:**
- [ ] Tree-sitter-python installed and working
- [ ] `parse_python(code: str) → SkeletonMap` extracts functions + classes
- [ ] `compute_structural_hash()` is stable (body change ≠ hash change)
- [ ] Cache (file_sha-keyed) implemented
- [ ] 8 unit tests with >85% coverage
- [ ] Skeleton size <10% of source (100:1 reduction)
- [ ] Single-file parse latency <50ms (measured with timeit)
- [ ] Benchmark: 5k files in <5s (async)

**Tests (Specific):**
```
test_skeleton_parse_function_basic
test_skeleton_parse_class_with_methods
test_skeleton_error_recovery_incomplete_code
test_structural_hash_stable_on_body_change
test_cache_hit_on_unmodified_file
test_cache_miss_on_content_change
test_skeleton_size_reduction_100_to_1
test_bench_parse_5k_files_async
```

**Metrics:**
- `ast_parse_count`: Increment per parse
- `ast_parse_latency_ms`: Record p50/p95/max
- `skeleton_cache_hit_rate`: hits / (hits + misses)

**Rollback Plan:**
- If Tree-sitter parse >100ms per file: Implement async batch parsing
- If cache thrashing: Switch to LRU with 100-file limit

---
