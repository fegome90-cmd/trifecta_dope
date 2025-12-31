# Desde la raíz del proyecto
make minirag-setup MINIRAG_SOURCE=~/Developer/Minirag
make minirag-chunk
make minirag-index
```
```

**Step 4: Run test to verify it passes**

Run: `make minirag-chunk`  
Expected: `.mini-rag/chunks/manifest.jsonl` created, chunk files generated.

**Step 5: Commit**

```bash
git add Makefile .mini-rag/config.yaml README.md
git commit -m "feat: wire local chunker into mini-rag workflow"
```

---
