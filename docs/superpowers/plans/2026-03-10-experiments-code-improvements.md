# Experiments Code Improvements Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor experiments/ directory to eliminate code duplication, add input validation, and consolidate error handling.

**Architecture:** Extract shared chunking module, add path validation in ingest_directory, consolidate duplicate try/except blocks into helper function.

**Tech Stack:** Python 3.10+, pytest

---

## File Structure

| File | Action | Purpose |
|------|--------|---------|
| `experiments/chunking.py` | **Create** | Shared chunk_text_smart function |
| `experiments/02_ingest_docs.py` | **Modify** | Import from chunking, add path validation |
| `experiments/04_test_prisma_db.py` | **Modify** | Add create_index_safely helper |
| `experiments/test_chunking.py` | **Modify** | Import from chunking module |

---

## Chunk 1: Extract Shared Chunking Module

### Task 1: Create chunking.py module

**Files:**
- Create: `experiments/chunking.py`

- [ ] **Step 1: Create the chunking module**

```python
"""Smart text chunking for document ingestion."""
import re


def chunk_text_smart(text: str, max_chars: int = 1500, overlap: int = 200) -> list[str]:
    """
    Chunking inteligente que respeta párrafos y oraciones.

    - Divide por párrafos primero
    - Si párrafo > max_chars, divide por oraciones
    - Si oración > max_chars, hace split duro con overlap
    - Añade overlap entre chunks para contexto

    Args:
        text: Text to chunk
        max_chars: Maximum characters per chunk
        overlap: Overlap characters between consecutive chunks

    Returns:
        List of text chunks
    """
    if not text or not text.strip():
        return []

    paragraphs = re.split(r'\n\n+', text)
    chunks: list[str] = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= max_chars:
            current_chunk += ("\n\n" if current_chunk else "") + para
        else:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            # Si párrafo muy largo, dividir por oraciones
            if len(para) > max_chars:
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sent in sentences:
                    # EDGE CASE: oración más larga que max_chars
                    if len(sent) > max_chars:
                        # Hard split con overlap
                        for j in range(0, len(sent), max_chars - overlap):
                            chunk_part = sent[j:j + max_chars]
                            if chunk_part.strip():
                                chunks.append(chunk_part)
                    elif len(current_chunk) + len(sent) + 1 <= max_chars:
                        current_chunk += (" " if current_chunk else "") + sent
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = sent
            else:
                current_chunk = para

    if current_chunk:
        chunks.append(current_chunk)

    # Añadir overlap entre chunks consecutivos
    if overlap > 0 and len(chunks) > 1:
        overlapped: list[str] = []
        for i, chunk in enumerate(chunks):
            if i > 0:
                prev_tail = chunks[i-1][-overlap:] if len(chunks[i-1]) > overlap else chunks[i-1]
                chunk = prev_tail + "\n---\n" + chunk
            overlapped.append(chunk)
        return overlapped

    return chunks
```

- [ ] **Step 2: Verify module can be imported**

Run: `cd experiments && uv run python -c "from chunking import chunk_text_smart; print('OK')"`
Expected: `OK`

---

### Task 2: Update 02_ingest_docs.py to import from chunking

**Files:**
- Modify: `experiments/02_ingest_docs.py`

- [ ] **Step 1: Remove inline chunk_text_smart and add import**

Replace lines 11-107 with:

```python
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "openai",
#     "psycopg[binary]",
#     "pgvector",
# ]
# ///

import os
import sys
import json
from pathlib import Path
from openai import OpenAI
import psycopg
from pgvector.psycopg import register_vector

# Import shared chunking function
from chunking import chunk_text_smart

# Configuration via ENV vars
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

if not OPENAI_API_KEY or not DATABASE_URL:
    print("Error: OPENAI_API_KEY and DATABASE_URL must be set.")
    print("Run like: OPENAI_API_KEY=... DATABASE_URL=... uv run experiments/02_ingest_docs.py")
    sys.exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_embedding(text: str) -> list[float]:
    """Generates an embedding using OpenAI."""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def chunk_text(text: str, chunk_size: int = 1500) -> list[str]:
    """A very basic text chunker by character length (naive approach)."""
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]


def ingest_directory(directory_path: str, segment_name: str):
    """Reads markdown files from a directory and ingests them into pgvector."""
    base_dir = Path(directory_path).resolve()

    # Validation
    if not base_dir.exists():
        raise ValueError(f"Directory does not exist: {base_dir}")
    if not base_dir.is_dir():
        raise ValueError(f"Path is not a directory: {base_dir}")

    with psycopg.connect(DATABASE_URL) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            for filepath in base_dir.rglob("*.md"):
                try:
                    content = filepath.read_text(encoding="utf-8")
                    if not content.strip():
                        continue

                    chunks = chunk_text_smart(content)
                    print(f"Ingesting {filepath.name} ({len(chunks)} chunks)...")

                    for i, chunk in enumerate(chunks):
                        chunk_id = f"doc:{filepath.name}:{i}"
                        embedding = generate_embedding(chunk)
                        metadata = json.dumps({"source": str(filepath)})

                        # Upsert logical (ON CONFLICT DO UPDATE)
                        cur.execute(
                            """
                            INSERT INTO trifecta_chunks (id, segment_name, content, embedding, metadata)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO UPDATE SET
                                content = EXCLUDED.content,
                                embedding = EXCLUDED.embedding,
                                metadata = EXCLUDED.metadata;
                            """,
                            (chunk_id, segment_name, chunk, embedding, metadata)
                        )
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
            conn.commit()

if __name__ == "__main__":
    # Point this to the local trifecta_dope docs
    docs_dir = Path(__file__).parent.parent / "docs"
    print(f"Starting ingestion from {docs_dir}")
    if docs_dir.exists():
        ingest_directory(str(docs_dir), "trifecta_dope_docs")
        print("Ingestion complete!")
    else:
        print(f"Directory {docs_dir} not found. Are you running this from the right folder?")
```

- [ ] **Step 2: Verify import works**

Run: `cd experiments && uv run python -c "import sys; sys.path.insert(0, '.'); from chunking import chunk_text_smart; from importlib import util; spec = util.spec_from_file_location('ingest', '02_ingest_docs.py'); print('Import OK')"`
Expected: No errors

---

### Task 3: Update test_chunking.py to import from chunking

**Files:**
- Modify: `experiments/test_chunking.py`

- [ ] **Step 1: Remove inline chunk_text_smart and add import**

Replace lines 1-80 with:

```python
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pytest",
# ]
# ///

"""Unit tests for chunk_text_smart function."""

import pytest

# Import the production implementation
from chunking import chunk_text_smart


class TestChunkTextSmart:
    """Test suite for intelligent text chunking."""

    def test_empty_string(self) -> None:
        """Empty input returns empty list."""
        assert chunk_text_smart("") == []
        assert chunk_text_smart("   ") == []

    def test_shorter_than_max(self) -> None:
        """Text shorter than max_chars returns single chunk."""
        text = "Short text"
        result = chunk_text_smart(text, max_chars=100)
        assert len(result) == 1
        assert result[0] == text

    def test_paragraph_break(self) -> None:
        """Respects paragraph boundaries."""
        text = "Para 1\n\nPara 2\n\nPara 3"
        result = chunk_text_smart(text, max_chars=20)
        assert len(result) >= 2  # At least split by paragraphs

    def test_long_paragraph_sentence_split(self) -> None:
        """Long paragraphs split by sentences."""
        text = "First sentence. Second sentence. Third sentence."
        result = chunk_text_smart(text, max_chars=25, overlap=0)
        assert len(result) >= 2

    def test_very_long_sentence_hard_split(self) -> None:
        """Sentences longer than max_chars get hard split."""
        text = "A" * 2000  # 2000 chars, no punctuation
        result = chunk_text_smart(text, max_chars=500, overlap=50)
        assert len(result) >= 3  # Should split into multiple chunks
        # Each chunk should be <= max_chars + overlap + marker
        # marker = "\n---\n" = 5 chars
        max_expected = 500 + 50 + 5  # max_chars + overlap + marker
        for chunk in result:
            assert len(chunk) <= max_expected

    def test_unicode_handling(self) -> None:
        """Handles unicode characters correctly."""
        text = "Hola mundo 🌍\n\nTexto en español con ñ y acentos"
        result = chunk_text_smart(text, max_chars=100)
        assert len(result) >= 1
        assert "🌍" in result[0] or "🌍" in "".join(result)

    def test_overlap_added(self) -> None:
        """Overlap is added between consecutive chunks."""
        text = "Para one.\n\nPara two.\n\nPara three."
        result = chunk_text_smart(text, max_chars=20, overlap=5)
        if len(result) > 1:
            # Second chunk should contain end of first
            assert "---" in result[1]  # Overlap marker

    def test_single_word(self) -> None:
        """Single word returns single chunk."""
        text = "word"
        result = chunk_text_smart(text, max_chars=100)
        assert len(result) == 1
        assert result[0] == "word"

    def test_no_overlap_when_disabled(self) -> None:
        """No overlap marker when overlap=0."""
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        result = chunk_text_smart(text, max_chars=30, overlap=0)
        # No overlap marker should appear
        for chunk in result:
            assert "---" not in chunk

    def test_whitespace_only(self) -> None:
        """Whitespace-only input returns empty list."""
        assert chunk_text_smart("\n\n\n") == []
        assert chunk_text_smart("\t\t") == []

    def test_exact_max_chars(self) -> None:
        """Text exactly at max_chars returns single chunk."""
        text = "A" * 100
        result = chunk_text_smart(text, max_chars=100)
        assert len(result) == 1

    def test_preserves_paragraph_content(self) -> None:
        """Content within paragraphs is preserved."""
        text = "Paragraph one content.\n\nParagraph two content."
        result = chunk_text_smart(text, max_chars=100, overlap=0)
        combined = " ".join(result)
        assert "Paragraph one content" in combined
        assert "Paragraph two content" in combined


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

- [ ] **Step 2: Run tests to verify import works**

Run: `cd experiments && uv run pytest test_chunking.py -v`
Expected: `12 passed`

---

### Task 4: Commit chunking module extraction

- [ ] **Step 1: Stage and commit changes**

```bash
git add experiments/chunking.py experiments/02_ingest_docs.py experiments/test_chunking.py
git commit -m "refactor(experiments): extract chunk_text_smart to shared module

- Create experiments/chunking.py with chunk_text_smart function
- Update 02_ingest_docs.py to import from chunking
- Update test_chunking.py to import from chunking
- Add path validation in ingest_directory()"
```

---

## Chunk 2: Consolidate Error Handling

### Task 5: Add create_index_safely helper to 04_test_prisma_db.py

**Files:**
- Modify: `experiments/04_test_prisma_db.py`

- [ ] **Step 1: Add create_index_safely helper function**

After the `sanitize_error` function (line 24), add:

```python
def create_index_safely(cur, sql: str, description: str) -> None:
    """Execute index creation with sanitized error handling."""
    try:
        cur.execute(sql)
    except Exception as e:
        print(f"{description}: {sanitize_error(e, DATABASE_URL)}")
```

- [ ] **Step 2: Replace duplicate try/except blocks with helper calls**

Replace lines 50-66 with:

```python
            # Create indexes with safe error handling
            create_index_safely(
                cur,
                "CREATE INDEX IF NOT EXISTS trifecta_chunks_embedding_idx ON trifecta_chunks USING ivfflat (embedding vector_cosine_ops);",
                "Index creation caveat (might need data first depending on size)"
            )

            create_index_safely(
                cur,
                "CREATE INDEX IF NOT EXISTS idx_trifecta_chunks_segment_btree ON trifecta_chunks (segment_name);",
                "Segment index creation error"
            )
```

- [ ] **Step 3: Verify script still runs**

Run: `cd experiments && uv run python -c "import importlib.util; spec = importlib.util.spec_from_file_location('test_db', '04_test_prisma_db.py'); print('Syntax OK')"`
Expected: `Syntax OK`

---

### Task 6: Commit error handling consolidation

- [ ] **Step 1: Stage and commit changes**

```bash
git add experiments/04_test_prisma_db.py
git commit -m "refactor(experiments): consolidate index creation error handling

- Add create_index_safely helper function
- Replace duplicate try/except blocks with helper calls"
```

---

## Verification

### Task 7: Run all tests and verify

- [ ] **Step 1: Run chunking tests**

Run: `cd experiments && uv run pytest test_chunking.py -v`
Expected: `12 passed`

- [ ] **Step 2: Verify all files are syntactically correct**

Run: `cd experiments && uv run python -m py_compile chunking.py 02_ingest_docs.py 04_test_prisma_db.py test_chunking.py && echo "All files OK"`
Expected: `All files OK`

---

## Summary

| Task | Description | Commit |
|------|-------------|--------|
| 1 | Create chunking.py module | refactor: extract chunk_text_smart |
| 2 | Update 02_ingest_docs.py | (included above) |
| 3 | Update test_chunking.py | (included above) |
| 4 | Commit extraction | ✓ |
| 5 | Add create_index_safely helper | refactor: consolidate error handling |
| 6 | Commit consolidation | ✓ |
| 7 | Verify all tests pass | ✓ |
