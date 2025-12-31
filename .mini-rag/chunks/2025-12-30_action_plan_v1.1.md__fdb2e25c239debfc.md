### Implementation
1. Edit [src/infrastructure/file_system.py](src/infrastructure/file_system.py) → Add exclusion list
2. Run `uv run trifecta ctx sync --segment .`
3. Verify: `uv run trifecta ctx validate --segment .` → Should show -1 chunk, same content

---
