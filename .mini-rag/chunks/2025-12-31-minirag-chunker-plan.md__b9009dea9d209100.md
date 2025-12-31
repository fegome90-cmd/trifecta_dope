### Task 5: Add CLI entrypoint to generate chunks from config

**Files:**
- Modify: `scripts/minirag_chunker.py`

**Step 1: Write the failing test**

Skip (smoke test via manual run).

**Step 2: Run test to verify it fails**

Run: `uv run python scripts/minirag_chunker.py --config .mini-rag/config.yaml`  
Expected: FAIL (no CLI / config handling).

**Step 3: Write minimal implementation**
