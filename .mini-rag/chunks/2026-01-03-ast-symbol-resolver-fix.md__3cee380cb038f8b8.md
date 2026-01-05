### Step 2: Run test to verify it fails

```bash
uv run pytest tests/unit/test_symbol_selector_resolve.py -v
```

Expected: FAIL with "Expected Ok, got Err" (FILE_NOT_FOUND)
