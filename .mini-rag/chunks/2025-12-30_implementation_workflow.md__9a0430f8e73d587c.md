### Phase 4: Validation & Testing (25 min)

```
1. Sync context pack:
   $ uv run trifecta ctx sync --segment .
   
   Expected: 6 chunks (was 7), -1.7K tokens, PASS validation

2. Run unit tests:
   $ uv run pytest tests/installer_test.py -v
   
   Expected: All PASS (imports now clean)

3. Type checking:
   $ uv run mypy src/ --strict
   
   Expected: All PASS (validators.py properly typed)

4. Linting:
   $ uv run ruff check .
   
   Expected: All PASS (clean imports, no sys.path hacks)

5. Context validation:
   $ uv run trifecta ctx validate --segment .
   
   Expected: PASS (no duplicates, all chunks valid)
```

---
