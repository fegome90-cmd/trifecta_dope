### Telemetry Events (Always log)

```python
# ast_lsp.py
telemetry.event(
    "ast.parse",
    {"file": file_path, "lang": "python"},
    {"skeleton_size": len(skeleton.json), "reduction_ratio": 0.02},
    duration_ms=42
)

telemetry.event(
    "lsp.definition",
    {"symbol": symbol_name},
    {"resolved": True, "file": target_file},
    duration_ms=150
)

telemetry.event(
    "selector.resolve",
    {"symbol_query": "sym://python/src.domain.models/Config"},
    {"success": True, "ambiguous": False, "matches": 1},
    duration_ms=5
)
```

---
