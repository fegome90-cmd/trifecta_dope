"""Regression tests for full-text search in ContextService."""

from pathlib import Path

import pytest

from src.application.context_service import ContextService
from src.domain.context_models import ContextChunk, ContextIndexEntry, ContextPack


SEARCH_TERM = "needleword"
TRUNCATED_PREVIEW = "# Skill Preview\n\n" + ("x" * 80) + "..."


def _write_pack(segment: Path, pack: ContextPack) -> None:
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir()
    (ctx_dir / "context_pack.json").write_text(pack.model_dump_json(indent=2))


def test_search_finds_keyword_beyond_truncated_preview(tmp_path: Path) -> None:
    """A keyword outside preview must still be found via full chunk text."""
    chunk_text = "x" * 260 + f" {SEARCH_TERM} appears after the preview boundary."
    pack = ContextPack(
        segment="test",
        chunks=[
            ContextChunk(
                id="skill:deep-match",
                doc="skill",
                title_path=["skill.md"],
                text=chunk_text,
                char_count=len(chunk_text),
                token_est=len(chunk_text) // 4,
                source_path="skill.md",
            )
        ],
        index=[
            ContextIndexEntry(
                id="skill:deep-match",
                title_path_norm="skill.md",
                preview=TRUNCATED_PREVIEW,
                token_est=len(chunk_text) // 4,
            )
        ],
    )
    _write_pack(tmp_path, pack)

    result = ContextService(tmp_path).search(SEARCH_TERM, k=5)

    assert [hit.id for hit in result.hits] == ["skill:deep-match"]


def test_search_matches_chunk_text_not_preview_content(tmp_path: Path) -> None:
    """Search must use chunk.text as authority, not preview text."""
    deep_text = "x" * 260 + f" {SEARCH_TERM} lives only in the chunk body."
    misleading_preview = f"Preview mentions {SEARCH_TERM}, but chunk text does not."
    preview_only_text = "This chunk body never includes the search term."
    pack = ContextPack(
        segment="test",
        chunks=[
            ContextChunk(
                id="skill:deep-match",
                doc="skill",
                title_path=["deep.md"],
                text=deep_text,
                char_count=len(deep_text),
                token_est=len(deep_text) // 4,
                source_path="deep.md",
            ),
            ContextChunk(
                id="skill:preview-only",
                doc="skill",
                title_path=["preview.md"],
                text=preview_only_text,
                char_count=len(preview_only_text),
                token_est=len(preview_only_text) // 4,
                source_path="preview.md",
            ),
        ],
        index=[
            ContextIndexEntry(
                id="skill:deep-match",
                title_path_norm="deep.md",
                preview=TRUNCATED_PREVIEW,
                token_est=len(deep_text) // 4,
            ),
            ContextIndexEntry(
                id="skill:preview-only",
                title_path_norm="preview.md",
                preview=misleading_preview,
                token_est=11,
            ),
        ],
    )
    _write_pack(tmp_path, pack)

    result = ContextService(tmp_path).search(SEARCH_TERM, k=10)

    assert [hit.id for hit in result.hits] == ["skill:deep-match"]


def test_search_keeps_preview_as_display_surface(tmp_path: Path) -> None:
    """Returned preview stays truncated even when search matched deep text."""
    chunk_text = "x" * 260 + f" {SEARCH_TERM} appears after the preview boundary."
    pack = ContextPack(
        segment="test",
        chunks=[
            ContextChunk(
                id="skill:deep-match",
                doc="skill",
                title_path=["skill.md"],
                text=chunk_text,
                char_count=len(chunk_text),
                token_est=len(chunk_text) // 4,
                source_path="skill.md",
            )
        ],
        index=[
            ContextIndexEntry(
                id="skill:deep-match",
                title_path_norm="skill.md",
                preview=TRUNCATED_PREVIEW,
                token_est=len(chunk_text) // 4,
            )
        ],
    )
    _write_pack(tmp_path, pack)

    result = ContextService(tmp_path).search(SEARCH_TERM, k=5)

    assert len(result.hits) == 1
    assert result.hits[0].preview == TRUNCATED_PREVIEW
    assert SEARCH_TERM not in result.hits[0].preview


def test_search_raises_for_missing_chunk_reference(tmp_path: Path) -> None:
    """Search should fail closed when index entries reference missing chunks."""
    pack = ContextPack(
        segment="test",
        chunks=[],
        index=[
            ContextIndexEntry(
                id="skill:missing-chunk",
                title_path_norm="missing.md",
                preview=TRUNCATED_PREVIEW,
                token_est=1,
            )
        ],
    )
    _write_pack(tmp_path, pack)

    with pytest.raises(RuntimeError, match="missing chunk id 'skill:missing-chunk'"):
        ContextService(tmp_path).search("missing", k=5)
