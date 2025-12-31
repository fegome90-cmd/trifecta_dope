### Task 6: Wire Makefile + config + docs

**Files:**
- Modify: `Makefile`
- Modify: `.mini-rag/config.yaml`
- Modify: `README.md`

**Step 1: Write the failing test**

Skip (config/manual check).

**Step 2: Run test to verify it fails**

Run: `make minirag-chunk`  
Expected: FAIL (target missing).

**Step 3: Write minimal implementation**

```make
minirag-chunk:
	@echo "Chunking docs for Mini-RAG..."
	. .venv/bin/activate && python scripts/minirag_chunker.py --config .mini-rag/config.yaml

minirag-index:
	@echo "Indexing Mini-RAG documents..."
	@$(MAKE) minirag-chunk
	. .venv/bin/activate && mini-rag index
```

```yaml
docs_glob:
  - .mini-rag/chunks/**/*.md
  - knowledge/**/*.pdf
chunking:
  chunk_size: 800
  chunk_overlap: 200
  section_max_chars: 1400
  overlap_pct: 0.05
  source_globs:
    - docs/**/*.md
    - knowledge/**/*.md
    - knowledge/**/*.txt
```

```md
### Setup (solo para desarrollo del CLI)

```bash
