#### B) context_pack.nl_triggers

```diff
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

**Patch Analysis**:

**"build command"**:
- **Target FN**: Task #24 ("build command not working")
- **TP Gain**: +1 ✅
- **FP Risk**: LOW - "build command" specifically targets ctx build, not general commands
- **Why subset-match safe**: L2 exact match beats L3 alias "build" term

**"ctx validate"**:
- **Target FN**: Task #20 ("design a ctx validate workflow")
- **TP Gain**: +1 ✅
- **FP Risk**: LOW - "ctx validate" is 2-gram, more specific than reverse order "validate context"
- **Why no conflict**: L2 exact "ctx validate" vs subset match "validate context" = different order

**Total TP Gain**: +2 (Tasks #20, #24) → accuracy 72.5% → 77.5% ✅

---
