### Before v1.1 (Naive)
```python
# Filename-based exclusion (BROKEN for nested files)
REFERENCE_EXCLUSION = {"skill.md"}
if name in REFERENCE_EXCLUSION:
    continue  # ❌ Excludes docs/library/skill.md incorrectly
```
