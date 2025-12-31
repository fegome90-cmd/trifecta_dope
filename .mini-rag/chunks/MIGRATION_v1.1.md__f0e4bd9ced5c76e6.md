### After v1.1 (Path-Aware)
```python
# Path-based exclusion using resolve()
primary_skill_path = target_path / "skill.md"
excluded_paths = {primary_skill_path.resolve()}

for name, path in refs.items():
    if path.resolve() in excluded_paths:
        continue  # ✅ Only excludes root skill.md
```

**Impact**:
- Root `skill.md` deduplicated ✅
- Nested `library/python/skill.md` indexed as `ref:` ✅
- Context pack: 6 chunks (was 7), -646 tokens saved

---
