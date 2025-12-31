from pathlib import Path

from scripts.minirag_chunker import (
    Chunk,
    ChunkRules,
    chunk_markdown,
    normalize_markdown,
    write_chunks,
)


def test_normalize_removes_frontmatter_preserves_fence() -> None:
    raw = "---\ntitle: Test\ntags: [a, b]\n---\n\nIntro\n```python\nprint('hi')\n```\n"
    normalized = normalize_markdown(raw)
    assert "title: Test" not in normalized
    assert "```python" in normalized
    assert "print('hi')" in normalized


def test_chunk_markdown_respects_headings_and_fences() -> None:
    md = "# Title\nIntro line\n```bash\necho hello\n```\n## Section A\nA1\nA2\n## Section B\nB1\n"
    rules = ChunkRules(chunk_size=120, section_max_chars=200, overlap_pct=0.05)
    chunks = chunk_markdown(md, rules, source_path="docs/sample.md")
    assert len(chunks) == 3
    assert chunks[0].text.startswith("# Title")
    assert "```bash" in chunks[0].text
    assert "## Section A" in chunks[1].text
    assert "## Section B" in chunks[2].text


def test_dedup_and_manifest(tmp_path: Path) -> None:
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
    manifest = manifest_path.read_text(encoding="utf-8")
    assert "abc123" in manifest
    assert "docs/a.md" in manifest
