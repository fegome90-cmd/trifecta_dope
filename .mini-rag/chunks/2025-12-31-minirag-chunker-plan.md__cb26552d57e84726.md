**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_minirag_chunker.py::test_chunk_markdown_respects_headings_and_fences -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/minirag_chunker.py tests/unit/test_minirag_chunker.py
git commit -m "feat: add markdown-aware chunker core"
```

---
