### Solution (Minimal)

**Option A: Exclude rule (Simplest)**
- Add `skill.md` to exclusion list for reference indexing
- Keep primary `skill` chunk only
- Impact: -1.7K tokens, cleaner index

```python
# src/infrastructure/file_system.py

REFERENCE_EXCLUSION = {
    "skill.md",  # Already indexed as primary 'skill' doc
    "_ctx/session_*.md",  # Session is append-only, not indexed as ref
}

# In scan_files():
if file.name in REFERENCE_EXCLUSION:
    continue  # Skip reference indexing
```

**Option B: Merge rule (Better)**
- Detect duplicate content (SHA256)
- Keep highest-priority version (skill > ref)
- Impact: Same as A, but handles future duplicates

**Recommendation**: **Option A** (MVP scope, less code).
