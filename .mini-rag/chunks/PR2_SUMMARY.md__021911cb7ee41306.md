### Sample last_run.json (sanitized)

```json
{
  "run_id": "run_1767250969",
  "ts": "2026-01-01T07:02:49Z",
  "ast": {
    "ast_parse_count": 1,
    "ast_cache_hit_count": 0,
    "ast_cache_miss_count": 1,
    "ast_cache_hit_rate": 0.0
  },
  "lsp": {
    "lsp_spawn_count": 0,
    "lsp_ready_count": 0,
    "lsp_failed_count": 0,
    "lsp_fallback_count": 0,
    "lsp_ready_rate": 0.0,
    "lsp_fallback_rate": 0.0
  },
  "file_read": {
    "skeleton_bytes": 0,
    "excerpt_bytes": 0,
    "raw_bytes": 0,
    "total_bytes": 0
  },
  "telemetry_drops": {
    "lock_skipped": 0,
    "attempted": 2,
    "written": 2,
    "drop_rate": 0.0
  }
}
```

**Key observations:**
- ✅ `x` namespace used for all extras (no collision with reserved keys)
- ✅ Relative paths only (no absolute paths leaked)
- ✅ Content hash (SHA-256, 8 chars) for privacy
- ✅ AST/LSP counters initialized (even if 0)
- ✅ Drop rate tracked (0.0% in this run)

---
