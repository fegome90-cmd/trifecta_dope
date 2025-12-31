### Task 4: Implement chunk writing + manifest

**Files:**
- Modify: `scripts/minirag_chunker.py`

**Step 1: Write the failing test**

Skip (already written).

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_minirag_chunker.py::test_dedup_and_manifest -v`  
Expected: FAIL with missing `write_chunks`.

**Step 3: Write minimal implementation**

```python
def write_chunks(chunks: Sequence[Chunk], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.jsonl"
    seen_hashes: set[str] = set()
    with manifest_path.open("w", encoding="utf-8") as manifest:
        for chunk in chunks:
            if chunk.chunk_hash in seen_hashes:
                continue
            seen_hashes.add(chunk.chunk_hash)
            filename = f"{chunk.doc}__{chunk.chunk_hash}.md"
            (output_dir / filename).write_text(chunk.text, encoding="utf-8")
            record = {
                "hash": chunk.chunk_hash,
                "doc": chunk.doc,
                "title_path": chunk.title_path,
                "source_path": chunk.source_path,
                "char_count": chunk.char_count,
            }
            manifest.write(json.dumps(record, ensure_ascii=True) + "\n")
    return manifest_path
```

**Step 4: Run test to verify it passes**
