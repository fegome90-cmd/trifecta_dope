```python
"""Unit tests for SymbolResolver module path resolution."""
import pytest
from pathlib import Path
from src.application.symbol_selector import SymbolResolver, SymbolQuery, SkeletonMapBuilder


def test_symbol_resolver_converts_dots_to_slashes(tmp_path):
    """SymbolResolver should convert module dots to path slashes."""
    # Create a nested module structure
    (tmp_path / "src" / "infrastructure").mkdir(parents=True)
    (tmp_path / "src" / "infrastructure" / "telemetry.py").write_text("# test")

    resolver = SymbolResolver(builder=SkeletonMapBuilder(), root=tmp_path)
    query = SymbolQuery(kind="mod", path="src.infrastructure.telemetry")

    result = resolver.resolve(query)

    assert result.is_ok(), f"Expected Ok, got Err: {result}"
    candidate = result.unwrap()
    assert candidate.file_rel == "src/infrastructure/telemetry.py"


def test_symbol_resolver_handles_init_packages(tmp_path):
    """SymbolResolver should find __init__.py for package imports."""
    # Create a package with __init__.py
    (tmp_path / "src" / "domain").mkdir(parents=True)
    (tmp_path / "src" / "domain" / "__init__.py").write_text("# pkg")

    resolver = SymbolResolver(builder=SkeletonMapBuilder(), root=tmp_path)
    query = SymbolQuery(kind="mod", path="src.domain")

    result = resolver.resolve(query)

    assert result.is_ok(), f"Expected Ok, got Err: {result}"
    candidate
