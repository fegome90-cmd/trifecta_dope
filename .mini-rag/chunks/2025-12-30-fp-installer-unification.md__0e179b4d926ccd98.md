### Task 4: Full validation run

**Files:**
- None (verification)

**Step 1: Run targeted tests**

Run: `uv run pytest tests/unit/test_validators.py tests/installer_test.py -v`
Expected: PASS

**Step 2: Run optional gates**

Run: `uv run ruff check .`
Expected: PASS

**Step 3: Commit (if needed)**

```bash
git add -A
git commit -m "chore: validate fp installer changes"
```
