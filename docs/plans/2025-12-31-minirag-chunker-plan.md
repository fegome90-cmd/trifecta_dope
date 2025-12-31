# Mini-RAG Chunker Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a local Markdown-aware chunker that generates coherent chunks into `.mini-rag/chunks/` and wires it into the Mini‑RAG indexing flow.

**Architecture:** Pure parsing/chunking functions in `scripts/minirag_chunker.py`, with a small CLI wrapper to read config and emit chunk files + a manifest. Mini‑RAG’s indexer continues to read plain `.md` files via `docs_glob` pointing at the generated chunks.

**Tech Stack:** Python 3.12, pytest, PyYAML, standard library (`hashlib`, `argparse`, `pathlib`).

---

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

Run: `uv run pytest tests/unit/test_minirag_chunker.py::test_normalize_removes_frontmatter_preserves_fence -v`  
Expected: FAIL with `ModuleNotFoundError` or missing functions.

**Step 3: Write minimal implementation**

Skip (implementation in Task 2).

**Step 4: Run test to verify it passes**

Skip.

**Step 5: Commit**

Skip.

---

### Task 2: Implement core chunker functions (parse, chunk, normalize, hash)

**Files:**
- Create: `scripts/minirag_chunker.py`

**Step 1: Write the failing test**

Skip (already written).

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_minirag_chunker.py::test_chunk_markdown_respects_headings_and_fences -v`  
Expected: FAIL with missing functions.

**Step 3: Write minimal implementation**

```python
from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

import yaml


@dataclass(frozen=True)
class Block:
    kind: str  # heading | paragraph | fence
    text: str
    heading_level: Optional[int] = None
    heading_text: Optional[str] = None


@dataclass(frozen=True)
class ChunkRules:
    chunk_size: int
    section_max_chars: int
    overlap_pct: float


@dataclass(frozen=True)
class Chunk:
    text: str
    source_path: str
    title_path: List[str]
    char_count: int
    chunk_hash: str
    doc: str


def normalize_markdown(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                text = "\n".join(lines[i + 1 :])
                break
    return text.strip() + "\n"


def parse_markdown(md: str) -> List[Block]:
    blocks: List[Block] = []
    buf: List[str] = []
    in_fence = False
    fence_marker: Optional[str] = None

    def flush_paragraph() -> None:
        nonlocal buf
        if buf:
            blocks.append(Block(kind="paragraph", text="".join(buf)))
            buf = []

    for line in md.splitlines(keepends=True):
        stripped = line.lstrip()
        is_fence = stripped.startswith("```") or stripped.startswith("~~~")
        if is_fence:
            marker = stripped[:3]
            if not in_fence:
                flush_paragraph()
                in_fence = True
                fence_marker = marker
                buf = [line]
                continue
            if fence_marker is None or marker == fence_marker:
                buf.append(line)
                blocks.append(Block(kind="fence", text="".join(buf)))
                buf = []
                in_fence = False
                fence_marker = None
                continue

        if in_fence:
            buf.append(line)
            continue

        if stripped.startswith("#"):
            flush_paragraph()
            level = len(stripped.split(" ", 1)[0])
            heading_text = stripped[level:].strip()
            blocks.append(
                Block(kind="heading", text=line, heading_level=level, heading_text=heading_text)
            )
            continue

        if stripped.strip() == "":
            buf.append(line)
            flush_paragraph()
            continue

        buf.append(line)

    flush_paragraph()
    return blocks


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _split_paragraphs(blocks: Sequence[Block]) -> List[str]:
    paragraphs: List[str] = []
    for block in blocks:
        if block.kind == "heading":
            paragraphs.append(block.text)
            continue
        paragraphs.append(block.text)
    return paragraphs


def chunk_blocks(blocks: Sequence[Block], rules: ChunkRules, source_path: str) -> List[Chunk]:
    chunks: List[Chunk] = []
    seen_hashes: set[str] = set()
    title_path: List[str] = []
    section_blocks: List[Block] = []

    def flush_section() -> None:
        nonlocal section_blocks, chunks
        if not section_blocks:
            return
        section_text = "".join(b.text for b in section_blocks)
        if len(section_text) <= rules.section_max_chars:
            _append_chunk(section_text)
        else:
            _append_fallback(section_blocks)
        section_blocks = []

    def _append_chunk(text: str) -> None:
        normalized = text.strip() + "\n"
        chunk_hash = _hash_text(normalized)
        if chunk_hash in seen_hashes:
            return
        seen_hashes.add(chunk_hash)
        doc = os.path.basename(source_path)
        chunks.append(
            Chunk(
                text=normalized,
                source_path=source_path,
                title_path=list(title_path),
                char_count=len(normalized),
                chunk_hash=chunk_hash,
                doc=doc,
            )
        )

    def _append_fallback(section: Sequence[Block]) -> None:
        paragraphs = _split_paragraphs(section)
        buffer: List[str] = []
        buffer_len = 0
        for para in paragraphs:
            if len(para) > rules.chunk_size:
                if buffer:
                    _append_chunk("".join(buffer))
                    buffer = []
                    buffer_len = 0
                _split_large_paragraph(para)
                continue
            if buffer_len + len(para) > rules.chunk_size and buffer:
                _append_chunk("".join(buffer))
                buffer = []
                buffer_len = 0
            buffer.append(para)
            buffer_len += len(para)
        if buffer:
            _append_chunk("".join(buffer))

    def _split_large_paragraph(text: str) -> None:
        overlap = max(1, int(rules.chunk_size * min(rules.overlap_pct, 0.05)))
        step = max(1, rules.chunk_size - overlap)
        start = 0
        while start < len(text):
            end = min(start + rules.chunk_size, len(text))
            _append_chunk(text[start:end])
            if end >= len(text):
                break
            start += step

    for block in blocks:
        if block.kind == "heading" and block.heading_level is not None:
            flush_section()
            level = min(block.heading_level, 3)
            title_path = title_path[: level - 1]
            title_path.append(block.heading_text or "")
            section_blocks.append(block)
            continue
        section_blocks.append(block)

    flush_section()
    return chunks


def chunk_markdown(text: str, rules: ChunkRules, source_path: str) -> List[Chunk]:
    normalized = normalize_markdown(text)
    blocks = parse_markdown(normalized)
    return chunk_blocks(blocks, rules, source_path)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_minirag_chunker.py::test_chunk_markdown_respects_headings_and_fences -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/minirag_chunker.py tests/unit/test_minirag_chunker.py
git commit -m "feat: add markdown-aware chunker core"
```

---

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

Run: `uv run pytest tests/unit/test_minirag_chunker.py::test_dedup_and_manifest -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/minirag_chunker.py tests/unit/test_minirag_chunker.py
git commit -m "feat: write chunk files and manifest"
```

---

### Task 5: Add CLI entrypoint to generate chunks from config

**Files:**
- Modify: `scripts/minirag_chunker.py`

**Step 1: Write the failing test**

Skip (smoke test via manual run).

**Step 2: Run test to verify it fails**

Run: `uv run python scripts/minirag_chunker.py --config .mini-rag/config.yaml`  
Expected: FAIL (no CLI / config handling).

**Step 3: Write minimal implementation**

```python
def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def iter_source_files(config: dict) -> Iterable[Path]:
    chunking = config.get("chunking", {})
    source_globs = chunking.get("source_globs", [])
    for pattern in source_globs:
        for path in Path(".").glob(pattern):
            if path.is_file():
                yield path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", default=".mini-rag/chunks")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    chunking = config.get("chunking", {})
    rules = ChunkRules(
        chunk_size=int(chunking.get("chunk_size", 800)),
        section_max_chars=int(chunking.get("section_max_chars", 1400)),
        overlap_pct=float(chunking.get("overlap_pct", 0.05)),
    )
    chunks: List[Chunk] = []
    for file_path in iter_source_files(config):
        if file_path.suffix.lower() not in {".md", ".markdown", ".txt"}:
            continue
        text = file_path.read_text(encoding="utf-8")
        chunks.extend(chunk_markdown(text, rules, str(file_path)))

    write_chunks(chunks, Path(args.output_dir))


if __name__ == "__main__":
    main()
```

**Step 4: Run test to verify it passes**

Run: `uv run python scripts/minirag_chunker.py --config .mini-rag/config.yaml`  
Expected: Writes `.mini-rag/chunks/*.md` and `.mini-rag/chunks/manifest.jsonl`.

**Step 5: Commit**

```bash
git add scripts/minirag_chunker.py
git commit -m "feat: add chunker CLI to generate chunks"
```

---

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
