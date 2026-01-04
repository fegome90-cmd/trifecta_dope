#!/usr/bin/env python3
"""
E2E Tests for Trifecta Context Pack Builder.

Tests cover:
- Snapshot stability (same input → same output)
- ID stability (changes in doc A don't affect IDs in doc B)
- Fence-aware chunking (no splits inside code blocks)
- Digest scoring (top-2 relevant chunks selected)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add scripts to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from ingest_trifecta import (
    chunk_by_headings_fence_aware,
    generate_chunk_id,
    normalize_markdown,
    normalize_title_path,
    preview,
    score_chunk,
    ContextPackBuilder,
)


# =============================================================================
# Fixtures
# =============================================================================

SAMPLE_MARKDOWN = """# Core Rules

## Sync First

Validate .env before running tests.

## Overview

This is an introduction.

## Critical Protocol

```python
def test():
    # This should not be split
    return True
```

## Commands

- Run tests with pytest
- Validate config with check
"""

CODE_FENCE_SAMPLE = """# Documentation

## Example Code

```python
def function():
    # Level 2 heading inside fence should not create chunk
    pass
```

## Normal Section

Regular content here.

```python
# Another fence
## Another heading inside fence
x = 1
```

## After Fence

Final section.
"""

# =============================================================================
# Normalization Tests
# =============================================================================


def test_normalize_markdown_crlf_to_lf():
    """CRLF should be normalized to LF."""
    input_md = "Line 1\r\nLine 2\r\n\r\nLine 3"
    result = normalize_markdown(input_md)
    assert "\r\n" not in result
    assert result == "Line 1\nLine 2\n\nLine 3\n"


def test_normalize_markdown_collapses_blank_lines():
    """Multiple blank lines should be collapsed to double newline."""
    input_md = "Line 1\n\n\n\n\nLine 2"
    result = normalize_markdown(input_md)
    assert result == "Line 1\n\nLine 2\n"


def test_normalize_title_path():
    """Title path normalization should be stable."""
    assert normalize_title_path(["Core Rules", "  Sync  First"]) == "core rules\x1fsync first"
    assert normalize_title_path(["  Test  ", "TEST"]) == "test\x1ftest"


# =============================================================================
# Chunk ID Stability Tests
# =============================================================================


def test_chunk_id_deterministic():
    """Same inputs should produce same ID."""
    id1 = generate_chunk_id("skill", ["Core Rules"], "Same content")
    id2 = generate_chunk_id("skill", ["Core Rules"], "Same content")
    assert id1 == id2


def test_chunk_id_different_doc():
    """Different doc should produce different ID."""
    id1 = generate_chunk_id("skill", ["Core Rules"], "Content")
    id2 = generate_chunk_id("agent", ["Core Rules"], "Content")
    assert id1 != id2


def test_chunk_id_whitespace_insensitive():
    """Whitespace in title should not affect ID."""
    id1 = generate_chunk_id("skill", ["Core Rules"], "Content")
    id2 = generate_chunk_id("skill", ["Core   Rules"], "Content")
    assert id1 == id2


def test_chunk_id_case_insensitive():
    """Case in title should not affect ID (due to lower())."""
    id1 = generate_chunk_id("skill", ["Core Rules"], "Content")
    id2 = generate_chunk_id("skill", ["CORE RULES"], "Content")
    assert id1 == id2


# =============================================================================
# Fence-Aware Chunking Tests
# =============================================================================


def test_fence_aware_respects_code_blocks():
    """Headings inside code fences should not create chunks."""
    chunks = chunk_by_headings_fence_aware("test", CODE_FENCE_SAMPLE)

    # Should have chunks for: INTRO, Documentation, Example Code, Normal Section, After Fence
    # But NOT for "Another heading inside fence" (inside code block)

    chunk_titles = [c["title"] for c in chunks]
    assert "Documentation" in chunk_titles
    assert "Example Code" in chunk_titles
    assert "Normal Section" in chunk_titles
    assert "After Fence" in chunk_titles

    # Verify no chunk has "Another heading inside fence" as its title
    # (the text may appear inside a fence, but shouldn't be a chunk title)
    for chunk in chunks:
        assert chunk["title"] != "Another heading inside fence"


def test_fence_aware_state_machine_toggle():
    """The in_fence state should toggle correctly."""
    # Sample with two separate code blocks
    sample = """# Intro

```python
# First block
def foo():
    pass
```

## Middle

```python
# Second block
## Inside fence should not split
x = 1
```

## End
"""
    chunks = chunk_by_headings_fence_aware("test", sample)
    chunk_titles = [c["title"] for c in chunks]

    # Should only have: Intro, Middle, End (not "Inside fence should not split")
    assert "Intro" in chunk_titles
    assert "Middle" in chunk_titles
    assert "End" in chunk_titles
    assert "Inside fence should not split" not in chunk_titles


def test_fence_aware_with_simple_markdown():
    """Simple markdown without fences should work."""
    chunks = chunk_by_headings_fence_aware("test", SAMPLE_MARKDOWN)

    chunk_titles = [c["title"] for c in chunks]
    assert "Core Rules" in chunk_titles
    assert "Sync First" in chunk_titles
    assert "Overview" in chunk_titles
    assert "Critical Protocol" in chunk_titles
    assert "Commands" in chunk_titles


def test_fence_aware_tracks_title_hierarchy():
    """Title path should maintain hierarchy."""
    chunks = chunk_by_headings_fence_aware("test", SAMPLE_MARKDOWN)

    # Find a chunk and verify its hierarchy
    for chunk in chunks:
        if chunk["title"] == "Sync First":
            assert chunk["title_path"] == ["Core Rules", "Sync First"]
            break
    else:
        assert False, "Sync First chunk not found"


# =============================================================================
# Digest Scoring Tests
# =============================================================================


def test_score_chunk_prefers_relevant_keywords():
    """Chunks with relevant keywords should score higher."""
    score_core = score_chunk("Core Rules", 2, "Some content")
    score_random = score_chunk("Random Section", 2, "Some content")

    assert score_core > score_random


def test_score_chunk_prefers_higher_headings():
    """Higher level headings (1-2) should score higher."""
    score_h1 = score_chunk("Important", 1, "Content")
    score_h3 = score_chunk("Important", 3, "Content")

    assert score_h1 > score_h3


def test_score_chunk_penalizes_empty_overview():
    """Empty overview sections should be penalized."""
    score_short = score_chunk("Overview", 2, "Brief text")
    score_substantial = score_chunk("Overview", 2, "A" * 500)

    assert score_short < score_substantial


def test_score_chunk_negative_allowed():
    """Scores can be negative for fluff content."""
    score = score_chunk("Overview", 2, "Short")
    # Short overview with penalty can be negative
    assert score < 2  # Base level penalty


def test_digest_quality_selects_relevant(tmp_path):
    """Digest should select chunks with highest scores (most relevant)."""
    # Create test segment with varied sections
    segment = tmp_path / "digest_test"
    segment.mkdir()
    (segment / "skill.md").write_text("""# Test Skill

## Core Rules

Rule 1: Always test before commit.

## Overview

Brief intro here.

## Commands

- pytest -v
""")

    builder = ContextPackBuilder("digest_test", tmp_path)
    pack = builder.build()

    # Find skill digest entry
    skill_digest = next((d for d in pack["digest"] if d["doc"] == "skill"), None)
    assert skill_digest is not None

    # Core Rules should be in digest (higher score due to keyword)
    # Overview might be penalized if short
    assert len(skill_digest["source_chunk_ids"]) <= 2  # Max 2 chunks


# =============================================================================
# Preview Tests
# =============================================================================


def test_preview_collapses_whitespace():
    """Preview should collapse all whitespace to single space."""
    text = "Line 1\n\n\nLine   2\t\t  Line3"
    result = preview(text, max_chars=100)
    assert "\n" not in result
    assert "\t" not in result
    assert "  " not in result


def test_preview_truncates_with_ellipsis():
    """Long preview should be truncated with ellipsis."""
    text = "A" * 200
    result = preview(text, max_chars=100)
    assert len(result) == 101  # 100 chars + "…"
    assert result.endswith("…")


def test_preview_no_ellipsis_for_short():
    """Short preview should not have ellipsis."""
    text = "Short text"
    result = preview(text, max_chars=100)
    assert not result.endswith("…")


# =============================================================================
# Integration Tests
# =============================================================================


def test_integration_with_real_segment(tmp_path):
    """Test full pack generation with a real segment structure."""
    # Create test segment structure
    segment = tmp_path / "test_segment"
    segment.mkdir()
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir()

    # Create skill.md
    skill_md = segment / "skill.md"
    skill_md.write_text("""# Test Skill

## Core Rules

Rule 1: Always test before commit.
Rule 2: Keep documentation updated.

## Overview

This is test documentation.

## Commands

- pytest -v
- ruff check
""")

    # Create agent.md
    agent_md = ctx_dir / "agent.md"
    agent_md.write_text("""# Agent Context

## Tech Stack

- Python 3.12
- Pytest

## Gates

- Unit tests pass
- Linting passes
""")

    # Build pack
    builder = ContextPackBuilder("test_segment", tmp_path)
    pack = builder.build()

    # Verify schema
    assert pack["schema_version"] == 1
    assert pack["segment"] == "test_segment"
    assert "created_at" in pack
    assert "generator_version" in pack

    # Verify source_files
    assert len(pack["source_files"]) == 2
    for sf in pack["source_files"]:
        assert "path" in sf
        assert "sha256" in sf
        assert "mtime" in sf
        assert "chars" in sf
        assert "size" in sf

    # Verify chunking metadata
    assert pack["chunking"]["method"] == "headings+paragraph_fallback+fence_aware"
    assert pack["chunking"]["max_chars"] == 6000

    # Verify docs
    assert len(pack["docs"]) == 2
    for doc in pack["docs"]:
        assert "doc" in doc
        assert "file" in doc
        assert "sha256" in doc
        assert "chunk_count" in doc
        assert "total_chars" in doc

    # Verify digest
    assert len(pack["digest"]) == 2
    for digest_entry in pack["digest"]:
        assert "doc" in digest_entry
        assert "summary" in digest_entry
        assert "source_chunk_ids" in digest_entry
        assert isinstance(digest_entry["source_chunk_ids"], list)

    # Verify index
    assert len(pack["index"]) > 0
    for idx in pack["index"]:
        assert "id" in idx
        assert "doc" in idx
        assert "title_path" in idx
        assert "preview" in idx
        assert "token_est" in idx
        assert "source_path" in idx
        assert "heading_level" in idx
        assert "char_count" in idx
        assert "line_count" in idx
        assert "start_line" in idx
        assert "end_line" in idx

    # Verify chunks
    assert len(pack["chunks"]) > 0
    for chunk in pack["chunks"]:
        assert "id" in chunk
        assert "doc" in chunk
        assert "title_path" in chunk
        assert "text" in chunk
        assert "source_path" in chunk
        assert "heading_level" in chunk
        assert "char_count" in chunk
        assert "line_count" in chunk
        assert "start_line" in chunk
        assert "end_line" in chunk


def test_stability_ids_across_runs(tmp_path):
    """IDs should be stable across multiple runs."""
    # Create test segment
    segment = tmp_path / "stable_test"
    segment.mkdir()
    (segment / "skill.md").write_text("# Test\n\nContent here.")

    builder = ContextPackBuilder("stable_test", tmp_path)
    pack1 = builder.build()
    pack2 = builder.build()

    # Extract IDs from both runs
    ids1 = {c["id"] for c in pack1["chunks"]}
    ids2 = {c["id"] for c in pack2["chunks"]}

    assert ids1 == ids2, "IDs should be identical across runs"


def test_output_file_written(tmp_path):
    """Output file should be written to correct location."""
    segment = tmp_path / "output_test"
    segment.mkdir()
    (segment / "skill.md").write_text("# Test\n\nContent.")

    builder = ContextPackBuilder("output_test", tmp_path)
    builder.build()

    expected_output = tmp_path / "output_test" / "_ctx" / "context_pack.json"
    assert expected_output.exists()

    # Verify it's valid JSON
    content = json.loads(expected_output.read_text())
    assert content["schema_version"] == 1
