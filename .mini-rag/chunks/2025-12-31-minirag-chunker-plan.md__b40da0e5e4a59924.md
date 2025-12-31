### Task 3: Add tests for dedup + manifest writing

**Files:**
- Modify: `tests/unit/test_minirag_chunker.py`

**Step 1: Write the failing test**

```python
from scripts.minirag_chunker import write_chunks, Chunk


def test_dedup_and_manifest(tmp_path):
    chunks = [
        Chunk(
            text="Same\n",
            source_path="docs/a.md",
            title_path=["A"],
            char_count=5,
            chunk_hash="abc123",
            doc="a.md",
        ),
        Chunk(
            text="Same\n",
            source_path="docs/b.md",
            title_path=["B"],
            char_count=5,
            chunk_hash="abc123",
            doc="b.md",
        ),
    ]
    manifest_path = write_chunks(chunks, tmp_path)
    chunk_files = list(tmp_path.glob("*.md"))
    assert len(chunk_files) == 1
    manifest = manifest_path.read_text()
    assert "abc123" in manifest
    assert "docs/a.md" in manifest
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_minirag_chunker.py::test_dedup_and_manifest -v`  
Expected: FAIL with `AttributeError` or missing `write_chunks`.

**Step 3: Write minimal implementation**

Skip (implementation in Task 4).

**Step 4: Run test to verify it passes**

Skip.

**Step 5: Commit**

Skip.

---
