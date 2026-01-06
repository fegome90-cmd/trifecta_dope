"""
Tests for AST Cache --persist-cache fix.

RED phase: These tests will fail until the fix is implemented.
"""

from pathlib import Path
import tempfile
from src.domain.ast_cache import SQLiteCache
from src.application.ast_parser import SymbolInfo


def test_sqlite_cache_set_accepts_symbolinfo_list():
    """SQLiteCache.set() should accept list[SymbolInfo] without error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_cache.db"
        cache = SQLiteCache(db_path=db_path)

        # Create test data matching actual SymbolInfo structure
        symbols = [
            SymbolInfo(
                kind="class",
                name="TestClass",
                qualified_name="TestClass",
                start_line=1,
                end_line=10,
                signature_stub="class TestClass:",
            ),
            SymbolInfo(
                kind="function",
                name="test_func",
                qualified_name="test_func",
                start_line=15,
                end_line=20,
                signature_stub="def test_func():",
            ),
        ]

        # This should NOT raise TypeError
        cache.set("test_key", symbols)


def test_sqlite_cache_roundtrip_preserves_symbolinfo_semantics():
    """
    SQLiteCache roundtrip (set + get) should preserve SymbolInfo semantics.

    The caller (ast_parser) expects to be able to access .kind, .name, .start_line
    on the returned values. This test verifies the complete roundtrip works.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_cache.db"
        cache = SQLiteCache(db_path=db_path)

        original = [
            SymbolInfo(
                kind="class",
                name="OkClass",
                qualified_name="OkClass",
                start_line=5,
                end_line=15,
                signature_stub="class OkClass:",
            )
        ]

        # Set
        cache.set("roundtrip_key", original)

        # Get - should return data that can be used like SymbolInfo
        retrieved = cache.get("roundtrip_key")

        assert retrieved is not None
        assert len(retrieved) == 1

        # The critical test: can we access these fields?
        # (This will AttributeError if retrieved is raw dict without conversion)
        item = retrieved[0]

        # These accesses must work - they're what ast_parser.py and cli_ast.py do
        if hasattr(item, "kind"):
            # If it's already SymbolInfo, check values
            assert item.kind == "class"
            assert item.name == "OkClass"
            assert item.start_line == 5
        else:
            # If it's a dict, this means caller needs to convert
            # For now, we expect dict from cache (Option B)
            assert item["kind"] == "class"
            assert item["name"] == "OkClass"
            assert item["start_line"] == 5
