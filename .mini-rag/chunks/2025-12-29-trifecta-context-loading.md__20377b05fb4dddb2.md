### Macro: `trifecta load` (fallback)

```bash
# Load es un macro que hace search + get
trifecta load --segment debug-terminal --task "implement DT2-S1"

# Internamente:
# 1. ids = ctx.search(segment, task, k=5)
# 2. chunks = ctx.get(segment, ids, mode="raw")
# 3. print(format_evidence(chunks))
```

---
