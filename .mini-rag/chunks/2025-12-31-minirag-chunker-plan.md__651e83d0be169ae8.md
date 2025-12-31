Run: `uv run python scripts/minirag_chunker.py --config .mini-rag/config.yaml`  
Expected: Writes `.mini-rag/chunks/*.md` and `.mini-rag/chunks/manifest.jsonl`.

**Step 5: Commit**

```bash
git add scripts/minirag_chunker.py
git commit -m "feat: add chunker CLI to generate chunks"
```

---
