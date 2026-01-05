#### ast hover (LSP)

```bash
$ uv run trifecta ast hover src/application/context_service.py -l 50 -c 15 2>&1
{
  "status": "ok",
  "kind": "skeleton",
  "data": {
    "uri": "src/application/context_service.py",
    "range": {
      "start_line": 1,
      "end_line": 10
    },
    "children": [],
    "truncated": false
  },
  "refs": [],
  "errors": [],
  "next_actions": []
}
```
