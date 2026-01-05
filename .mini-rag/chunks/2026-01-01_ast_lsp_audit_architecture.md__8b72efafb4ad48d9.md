### 3.4 Errors & Ambiguity
If `path/to/file` matches multiple files (e.g., `utils.py` and `pkg/utils.py` for input `utils`), return `AMBIGUOUS_SYMBOL`.

**Ambiguous Candidate Format**:
```json
{
  "sym": "sym://python/mod/utils",
  "candidates": [
    { "sym": "sym://python/mod/root/utils", "file_rel": "root/utils.py", "kind": "mod" },
    { "sym": "sym://python/mod/pkg/utils", "file_rel": "pkg/utils.py", "kind": "mod" }
  ]
}
```

---
