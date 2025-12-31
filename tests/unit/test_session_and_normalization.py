"""Tests for session append command and query normalization."""

import json
from pathlib import Path

from src.application.query_normalizer import QueryNormalizer


def test_normalization_splits_tokens(tmp_path: Path) -> None:
    """Verify that normalization splits on separators (snake-case/kebab-case)."""
    normalizer = QueryNormalizer()

    # Test snake_case
    tokens = normalizer.tokenize("ast_parser")
    assert "ast" in tokens
    assert "parser" in tokens

    # Test kebab-case
    tokens = normalizer.tokenize("tree-sitter")
    assert "tree" in tokens
    assert "sitter" in tokens

    # Test mixed
    tokens = normalizer.tokenize("ast-parser_v2.0")
    assert "ast" in tokens
    assert "parser" in tokens
    assert "v2" in tokens
    assert "0" not in tokens  # Single char removed

    # Test dedupe
    tokens = normalizer.tokenize("test test parser")
    assert tokens.count("test") == 1  # Deduped
    assert "parser" in tokens


def test_session_append_creates_file(tmp_path: Path) -> None:
    """Verify that session append creates file with correct structure."""
    from unittest.mock import patch

    from src.infrastructure.cli import session_append

    segment = tmp_path / "test_segment"
    segment.mkdir()

    # Mock typer.echo to capture output
    with patch("typer.echo") as mock_echo:
        session_append(
            segment=str(segment),
            summary="Initial setup",
            files="file1.py,file2.py",
            commands="ctx sync",
        )
        assert mock_echo.called

    session_file = segment / "_ctx" / "session_test_segment.md"
    assert session_file.exists()

    content = session_file.read_text()
    assert "# Session Log - test_segment" in content
    assert "## History" in content
    assert "Initial setup" in content
    assert "file1.py" in content
    assert "ctx sync" in content


def test_session_append_appends_second_entry(tmp_path: Path) -> None:
    """Verify that session append appends to existing file."""
    from unittest.mock import patch

    from src.infrastructure.cli import session_append

    segment = tmp_path / "test_segment"
    segment.mkdir()

    # First entry
    with patch("typer.echo"):
        session_append(
            segment=str(segment), summary="First entry", files="file1.py", commands="ctx sync"
        )

    # Second entry
    with patch("typer.echo"):
        session_append(
            segment=str(segment), summary="Second entry", files="file2.py", commands="ctx search"
        )

    session_file = segment / "_ctx" / "session_test_segment.md"
    content = session_file.read_text()

    # Both entries should be present
    assert "First entry" in content
    assert "Second entry" in content
    assert content.count("##") >= 3  # Header + 2 entries


def test_session_append_includes_pack_sha_when_present(tmp_path: Path) -> None:
    """Verify that session append includes pack_sha when context_pack.json exists."""
    from unittest.mock import patch

    from src.infrastructure.cli import session_append

    segment = tmp_path / "test_segment"
    ctx_dir = segment / "_ctx"
    ctx_dir.mkdir(parents=True)

    # Create a context_pack.json
    pack = {"schema_version": 1, "chunks": []}
    (ctx_dir / "context_pack.json").write_text(json.dumps(pack))

    with patch("typer.echo"):
        session_append(segment=str(segment), summary="With pack", files="", commands="")

    session_file = ctx_dir / "session_test_segment.md"
    content = session_file.read_text()

    assert "Pack SHA" in content
    assert "`" in content  # SHA should be in code block


def test_missing_aliases_file_is_ok(tmp_path: Path) -> None:
    """Verify that missing aliases.yaml doesn't break search."""
    from src.infrastructure.alias_loader import AliasLoader

    segment = tmp_path / "test_segment"
    segment.mkdir()

    loader = AliasLoader(segment)
    aliases = loader.load()

    # Should return empty dict, not error
    assert aliases == {}
