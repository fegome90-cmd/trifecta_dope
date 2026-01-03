---
name: metodo-p1-stringly-typed
enabled: true
event: all
pattern: (in\s+str\(|isinstance\(str,|"Expected.*not found"|TypeError.*str|\.endswith\(|\.startswith\(|if\s+".*"\s+in)
action: warn
---

🔴 **P1 VIOLATION DETECTED: Stringly-Typed Contract**

You're using string matching for error classification or type checking. This violates ADR-001 P1 pattern.

**Why this is risky:**
- Brittle parsing under refactors
- Type errors can silently become uncatchable
- Error handling becomes fragile

**Fix pattern:**
```python
# ❌ Instead of: if "file not found" in str(e)
# ✅ Use: if isinstance(e, FileNotFoundError)

# ❌ Instead of: if error_str.startswith("E:")
# ✅ Use: match/error type based handling
```

**This violation will be logged to Obsidian on next sync.**
