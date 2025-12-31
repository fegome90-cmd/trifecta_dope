### Task 1: Add unit tests for normalization and heading/fence chunking

**Files:**
- Create: `tests/unit/test_minirag_chunker.py`

**Step 1: Write the failing test**

```python
from scripts.minirag_chunker import chunk_markdown, normalize_markdown, ChunkRules


def test_normalize_removes_frontmatter_preserves_fence():
    raw = (
        "---\n"
        "title: Test\n"
        "tags: [a, b]\n"
        "---\n"
        "\n"
        "Intro\n"
        "```python\n"
        "print('hi')\n"
        "```\n"
    )
    normalized = normalize_markdown(raw)
    assert "title: Test" not in normalized
    assert "```python" in normalized
    assert "print('hi')" in normalized


def test_chunk_markdown_respects_headings_and_fences():
    md = (
        "# Title\n"
        "Intro line\n"
        "```bash\n"
        "echo hello\n"
        "```\n"
        "## Section A\n"
        "A1\n"
        "A2\n"
        "## Section B\n"
        "B1\n"
    )
    rules = ChunkRules(chunk_size=120, section_max_chars=200, overlap_pct=0.05)
    chunks = chunk_markdown(md, rules, source_path="docs/sample.md")
    assert len(chunks) == 3
    assert chunks[0].text.startswith("# Title")
    assert "```bash" in chunks[0].text
    assert "## Section A" in chunks[1].text
    assert "## Section B" in chunks[2].text
```

**Step 2: Run test to verify it fails**
