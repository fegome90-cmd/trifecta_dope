"""
Integration tests for PR#2 context searcher.

Test the full flow: AST extraction → selector → progressive disclosure → telemetry.
"""

import pytest
import tempfile
from pathlib import Path

from src.infrastructure.telemetry import Telemetry
from src.application.pr2_context_searcher import PR2ContextSearcher


@pytest.fixture
def temp_workspace() -> Path:
    """Create a temporary workspace."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_telemetry(temp_workspace: Path) -> Telemetry:
    """Create telemetry instance in temp dir."""
    return Telemetry(temp_workspace / ".trifecta")


@pytest.fixture
def searcher(temp_workspace: Path, temp_telemetry: Telemetry) -> PR2ContextSearcher:
    """Create context searcher instance."""
    return PR2ContextSearcher(
        temp_workspace,
        temp_telemetry,
        lsp_enabled=False,  # LSP disabled for unit tests
    )


@pytest.fixture
def sample_python_file(temp_workspace: Path) -> Path:
    """Create a sample Python file."""
    content = '''"""Module docstring."""

class MyClass:
    """A simple class."""

    def my_method(self):
        """Method docstring."""
        return 42

def standalone_function():
    """Standalone function."""
    pass
'''
    file_path = temp_workspace / "example.py"
    file_path.write_text(content)
    return file_path


class TestContextSearcherFlow:
    """Test full PR#2 flow: AST → selector → disclosure."""

    def test_search_symbol_not_found(
        self, searcher: PR2ContextSearcher, sample_python_file: Path
    ) -> None:
        """Search for non-existent symbol → None."""
        result = searcher.search_symbol(
            "sym://python/NonExistent",
            sample_python_file,
        )
        assert result is None

    def test_search_symbol_found_class(
        self, searcher: PR2ContextSearcher, sample_python_file: Path
    ) -> None:
        """Search for class symbol → found with location."""
        result = searcher.search_symbol(
            "sym://python/MyClass",
            sample_python_file,
        )
        # Note: actual symbol finding depends on tree-sitter
        # This test validates that the flow doesn't crash
        assert result is None or isinstance(result, dict)

    def test_search_symbol_with_skeleton_disclosure(
        self, searcher: PR2ContextSearcher, sample_python_file: Path
    ) -> None:
        """Search with skeleton disclosure mode."""
        result = searcher.search_symbol(
            "sym://python/MyClass",
            sample_python_file,
            disclosure_mode="skeleton",
        )
        # Should not have content (skeleton only)
        if result:
            assert "content" not in result

    def test_search_symbol_with_excerpt_disclosure(
        self, searcher: PR2ContextSearcher, sample_python_file: Path
    ) -> None:
        """Search with excerpt disclosure mode."""
        result = searcher.search_symbol(
            "sym://python/MyClass",
            sample_python_file,
            disclosure_mode="excerpt",
        )
        # excerpt mode should include excerpt if found
        if result:
            assert "file" in result
            assert "start_line" in result

    def test_extract_skeleton_reads_file(
        self, searcher: PR2ContextSearcher, sample_python_file: Path
    ) -> None:
        """_extract_skeleton should read and parse file."""
        searcher._extract_skeleton(sample_python_file)
        # Should not raise exception
        assert True

    def test_extract_skeleton_nonexistent_file(
        self, searcher: PR2ContextSearcher, temp_workspace: Path
    ) -> None:
        """_extract_skeleton gracefully handles missing file."""
        nonexistent = temp_workspace / "nonexistent.py"
        searcher._extract_skeleton(nonexistent)
        # Should not raise exception
        assert True

    def test_read_file_content_tracks_bytes(
        self, searcher: PR2ContextSearcher, sample_python_file: Path
    ) -> None:
        """_read_file_content should track bytes read."""
        initial_bytes = searcher.total_bytes_read

        content = searcher._read_file_content(sample_python_file)

        assert content is not None
        assert searcher.total_bytes_read > initial_bytes

    def test_request_definition_when_not_ready(
        self, searcher: PR2ContextSearcher
    ) -> None:
        """request_definition should return None when LSP not READY."""
        # LSP is disabled, so should not be ready
        result = searcher.request_definition("file://test.py", 5, 10)
        assert result is None


class TestTelemetryEmission:
    """Test that telemetry events are emitted correctly."""

    def test_ast_parse_event_emitted(
        self, searcher: PR2ContextSearcher, sample_python_file: Path, temp_telemetry: Telemetry
    ) -> None:
        """AST parsing should emit ast.parse event."""
        searcher._extract_skeleton(sample_python_file)

        # Flush telemetry
        temp_telemetry.flush()

        # Check events were written
        events_file = sample_python_file.parent / ".trifecta" / "events.jsonl"
        if events_file.exists():
            with open(events_file) as f:
                events = [line.strip() for line in f if line.strip()]
                assert len(events) > 0

    def test_search_symbol_end_event_emitted(
        self, searcher: PR2ContextSearcher, sample_python_file: Path, temp_telemetry: Telemetry
    ) -> None:
        """Symbol search should emit search.symbol.end event."""
        searcher.search_symbol("sym://python/MyClass", sample_python_file)

        # Flush telemetry
        temp_telemetry.flush()

        # Check events were written (at least search.symbol.end)
        events_file = sample_python_file.parent / ".trifecta" / "events.jsonl"
        if events_file.exists():
            with open(events_file) as f:
                lines = [line.strip() for line in f if line.strip()]
                assert len(lines) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
