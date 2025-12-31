## Rollback Plan

If something breaks:
```
1. Revert validators.py creation
2. Revert imports in scripts/ and tests/
3. Revert file_system.py changes
4. Run: uv run trifecta ctx sync --segment .
5. Restore original state

Risk: LOW (changes are isolated, no data loss)
```

---
