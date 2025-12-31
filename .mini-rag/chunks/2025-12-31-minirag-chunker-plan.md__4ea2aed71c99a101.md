Run: `uv run pytest tests/unit/test_minirag_chunker.py::test_dedup_and_manifest -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/minirag_chunker.py tests/unit/test_minirag_chunker.py
git commit -m "feat: write chunk files and manifest"
```

---
