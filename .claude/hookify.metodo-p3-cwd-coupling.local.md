---
name: metodo-p3-cwd-coupling
enabled: true
event: bash
pattern: (cd\s+\.\.|cd\s+[^/]|Path\.cwd\(\)|os\.getcwd\(\)|Path\(\)\.resolve\(\))
action: warn
---

🟠 **P3 VIOLATION DETECTED: CWD/Path Coupling**

Using relative paths or current working directory assumptions.

**Why this is risky:**
- Fails in different execution contexts
- Breaks when run from other directories
- Non-deterministic behavior

**Fix pattern:**
```python
# ❌ Instead of: Path.cwd() / "file.txt"
# ✅ Use: segment_root / "file.txt"

# ❌ Instead of: cd .. && run
# ✅ Use: explicit absolute paths
```

**This violation will be logged to Obsidian on next sync.**
