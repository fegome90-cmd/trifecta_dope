### Phase 3: Fix Deduplication (10 min)

```
src/infrastructure/file_system.py:
  
  ADD at top level:
  ┌──────────────────────────────────────────────────────┐
  │ REFERENCE_EXCLUSION = {                              │
  │     "skill.md",         # Already indexed as primary  │
  │     "_ctx/session_*.md",  # Append-only, not indexed │
  │ }                                                    │
  └──────────────────────────────────────────────────────┘
  
  MODIFY in scan_files():
  ┌──────────────────────────────────────────────────────┐
  │ if file.name in REFERENCE_EXCLUSION:                 │
  │     continue  # Skip reference indexing              │
  └──────────────────────────────────────────────────────┘
```
