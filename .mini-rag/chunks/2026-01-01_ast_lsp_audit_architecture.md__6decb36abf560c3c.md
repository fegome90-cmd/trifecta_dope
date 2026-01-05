### 4.2 Response Structure
```json
{
  "status": "ok",  // or "error" IF AND ONLY IF errors is not empty
  "kind": "skeleton | snippet | hover",
  "data": {
    "uri": "sym://python/type/foo/bar",
    "range": { "start_line": 10, "end_line": 25 },
    "content": "def bar():\n    pass",
    "signature": "def bar() -> None",
    "children": ["baz", "qux"]
  },
  "refs": [
    { "kind": "definition", "uri": "sym://python/mod/other" }
  ],
  "errors": [],
  "next_actions": [
    "ast snippet sym://python/type/foo/bar"
  ]
}
```

---
