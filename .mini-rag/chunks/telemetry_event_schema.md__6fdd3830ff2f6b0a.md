### 1. AST Events

| Event Type | Fields | Example |
|------------|--------|---------|
| `ast.parse` | `file` (relative), `status`, `functions_count`, `classes_count` | `{"cmd": "ast.parse", "args": {"file": "src/domain/models.py"}, "result": {"status": "ok", "functions": 3, "classes": 2}, "timing_ms": 45, "x": {"skeleton_bytes": 512, "reduction_ratio": 0.08, "cache_hit": false}}` |
