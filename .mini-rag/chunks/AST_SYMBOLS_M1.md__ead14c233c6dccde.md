### Example 1: Query existing module

```bash
$ trifecta ast symbols "sym://python/mod/src.domain.result" --segment .
{
  "status": "ok",
  "segment_root": "/path/to/project",
  "file_rel": "src/domain/result.py",
  "symbols": [
    {"kind": "class", "name": "Ok", "line": 5},
    {"kind": "class", "name": "Err", "line": 15}
  ]
}
```
