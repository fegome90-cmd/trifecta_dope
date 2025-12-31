### Task 7: Full verification

**Files:**
- None

**Step 1: Run full test suite**

Run: `uv run pytest tests/unit/test_minirag_chunker.py -v`  
Expected: PASS

**Step 2: Run end-to-end indexing**

Run: `make minirag-index`  
Expected: Mini‑RAG indexes `.mini-rag/chunks/**/*.md` and reports chunk count.

**Step 3: Commit**

Skip (already committed per task).
