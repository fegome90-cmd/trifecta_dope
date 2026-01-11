### Extra Fields Namespace

All additional fields MUST be placed under the `x` namespace to prevent future collisions:

```json
{
  "cmd": "lsp.spawn",
  "x": {
    "lsp_state": "WARMING",
    "spawn_method": "subprocess"
  }
}
```

---
