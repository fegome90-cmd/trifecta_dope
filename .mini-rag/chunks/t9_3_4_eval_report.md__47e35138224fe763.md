### Key Code Diff (aliases.yaml)

```diff
  symbol_surface:
    priority: 2
    nl_triggers:
      - "symbol extraction"
      - "symbol references"
      - "definition lookup"
      - "function implementation"
      - "class initialization"
+     - "telemetry class"

  context_pack:
    priority: 3
    nl_triggers:
      - "context pack build"
      - "validate context"
      - "context pack sync"
      - "context pack status"
+     - "build command"
+     - "ctx validate"
```

---
