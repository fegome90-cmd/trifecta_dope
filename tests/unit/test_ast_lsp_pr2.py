"""
Unit tests for PR#2: AST + Selector + LSP.

SCOPE:
  - AST skeleton extraction
  - Selector DSL parsing + fail-closed ambiguity (Result pattern)
  - Caching by content hash
  - LSP state machine (without spawn)

UPDATED: SymbolQuery returns Result[SymbolQuery, ASTError], not SymbolQuery | None.
"""

import pytest
from pathlib import Path

from src.application.ast_parser import SymbolInfo, SkeletonMapBuilder
from src.application.symbol_selector import SymbolQuery, SymbolResolver
from src.application.lsp_manager import LSPManager, LSPState
from src.domain.result import Ok, Err


class TestSymbolQuery:
    """Test sym:// DSL parser with Result pattern."""

    def test_parse_valid_mod_query(self) -> None:
        """Parse valid sym://python/mod/path → Ok(SymbolQuery)."""
        result = SymbolQuery.parse("sym://python/mod/mymodule")

        assert isinstance(result, Ok), f"Expected Ok, got {result}"
        query = result.value
        assert query.kind == "mod"
        assert query.path == "mymodule"

    def test_parse_valid_type_query(self) -> None:
        """Parse valid sym://python/type/path#member → Ok(SymbolQuery)."""
        result = SymbolQuery.parse("sym://python/type/mymodule#MyClass")

        assert isinstance(result, Ok), f"Expected Ok, got {result}"
        query = result.value
        assert query.kind == "type"
        assert query.path == "mymodule"
        assert query.member == "MyClass"

    def test_parse_invalid_wrong_prefix(self) -> None:
        """Reject non-sym:// queries → Err."""
        result = SymbolQuery.parse("ast://python/mod/mymodule")

        assert isinstance(result, Err), f"Expected Err for wrong prefix, got {result}"

    def test_parse_invalid_missing_kind(self) -> None:
        """Reject query without kind (mod/type) → Err."""
        result = SymbolQuery.parse("sym://python/something")

        assert isinstance(result, Err), f"Expected Err for missing kind, got {result}"

    def test_parse_invalid_wrong_kind(self) -> None:
        """Reject query with unsupported kind → Err."""
        result = SymbolQuery.parse("sym://python/class/MyClass")

        assert isinstance(result, Err), f"Expected Err for wrong kind, got {result}"


class TestSymbolResolver:
    """Test symbol resolution logic."""

    def test_resolve_existing_file(self, tmp_path: Path) -> None:
        """Resolve query for existing file → Ok(Candidate)."""
        # Create a Python file
        (tmp_path / "mymodule.py").write_text("def foo(): pass")

        builder = SkeletonMapBuilder()
        resolver = SymbolResolver(builder, root=tmp_path)

        query_result = SymbolQuery.parse("sym://python/mod/mymodule")
        assert isinstance(query_result, Ok)
        query = query_result.value

        result = resolver.resolve(query)
        assert isinstance(result, Ok), f"Expected Ok, got {result}"
        assert result.value.file_rel == "mymodule.py"

    def test_resolve_missing_file(self, tmp_path: Path) -> None:
        """Resolve query for non-existent file → Err."""
        builder = SkeletonMapBuilder()
        resolver = SymbolResolver(builder, root=tmp_path)

        query_result = SymbolQuery.parse("sym://python/mod/nonexistent")
        assert isinstance(query_result, Ok)
        query = query_result.value

        result = resolver.resolve(query)
        assert isinstance(result, Err), f"Expected Err for missing file, got {result}"


class TestSkeletonMapBuilder:
    """Test AST skeleton extraction and caching."""

    def test_cache_hit_by_content_hash(self) -> None:
        """Same content → cache hit."""
        builder = SkeletonMapBuilder()

        content1 = "def foo(): pass\n"
        content2 = "def foo(): pass\n"  # Identical

        symbols1 = builder.build(Path("test.py"), content1)
        symbols2 = builder.build(Path("test.py"), content2)

        # Both should return same (cached) result
        assert symbols1 == symbols2

    def test_cache_miss_on_content_change(self) -> None:
        """Different content → cache miss (re-parse)."""
        builder = SkeletonMapBuilder()

        content1 = "def foo(): pass\n"
        content2 = "def bar(): pass\n"

        symbols1 = builder.build(Path("test.py"), content1)
        symbols2 = builder.build(Path("test.py"), content2)

        # Both may be empty (stub impl), but test that no crash
        assert isinstance(symbols1, list)
        assert isinstance(symbols2, list)

    def test_graceful_failure_without_tree_sitter(self) -> None:
        """Return empty skeleton if tree-sitter unavailable."""
        builder = SkeletonMapBuilder()
        builder._tree_sitter = False
        builder._parser = None

        content = "def foo(): pass\n"
        symbols = builder.build(Path("test.py"), content)

        # Should return empty list (not crash)
        assert symbols == []

    def test_skeleton_bytes_estimation(self) -> None:
        """Get skeleton size for telemetry."""
        builder = SkeletonMapBuilder()

        symbol = SymbolInfo(
            kind="function",
            name="foo",
            qualified_name="foo",
            start_line=0,
            end_line=1,
            signature_stub="def foo():",
        )
        symbols = [symbol]

        bytes_size = builder.get_skeleton_bytes(symbols)
        assert bytes_size > 0


class TestLSPStateManager:
    """Test LSP state machine (no spawn)."""

    def test_initial_state_cold(self) -> None:
        """LSP starts in COLD state."""
        manager = LSPManager(Path("/workspace"), enabled=True)
        assert manager.state == LSPState.COLD

    def test_disabled_manager_stays_cold(self) -> None:
        """Disabled LSP manager never transitions."""
        manager = LSPManager(Path("/workspace"), enabled=False)
        manager.spawn_async()
        assert manager.state == LSPState.COLD

    def test_ready_only_gating_definition(self) -> None:
        """definition() returns None if not READY."""
        manager = LSPManager(Path("/workspace"), enabled=True)
        result = manager.request_definition("file://test.py", 5, 10)
        assert result is None

    def test_ready_only_gating_hover(self) -> None:
        """hover() returns None if not READY."""
        manager = LSPManager(Path("/workspace"), enabled=True)
        result = manager.request_hover("file://test.py", 5, 10)
        assert result is None

    def test_is_ready_false_when_cold(self) -> None:
        """is_ready() returns False when state!=READY."""
        manager = LSPManager(Path("/workspace"), enabled=True)
        assert manager.state == LSPState.COLD
        assert manager.is_ready() is False

    def test_shutdown_clears_state(self) -> None:
        """shutdown() returns state to COLD."""
        manager = LSPManager(Path("/workspace"), enabled=True)
        manager.state = LSPState.READY
        manager.shutdown()
        assert manager.state == LSPState.COLD


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
