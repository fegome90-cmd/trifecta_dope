"""
Tests que verifican que las correcciones del sistema de cache de AST funcionan correctamente.

Estos tests verifican que los problemas identificados en el análisis profundo han sido corregidos:
1. Cache hit/miss ahora se reporta correctamente (telemetría fija)
2. Distintos builders comparten cache (DI)
3. Claves de cache tienen formato versionable
4. build() retorna ParseResult con status de cache
"""

from pathlib import Path
from src.application.ast_parser import SkeletonMapBuilder, ParseResult
from src.domain.ast_cache import NullCache, InMemoryLRUCache


def test_cache_hit_miss_reported_correctly() -> None:
    """
    Test que verifica que cache hit/miss se reporta correctamente.
    
    Después del fix, SkeletonMapBuilder.build() retorna ParseResult
    con status "hit", "miss" o "error".
    """
    cache = InMemoryLRUCache(max_entries=100, max_bytes=1000)
    builder = SkeletonMapBuilder(cache=cache, segment_id=".")
    file_path = Path("test.py")
    content = "def test(): pass"
    
    # Primer parseo (debería ser miss)
    result1 = builder.build(file_path, content)
    assert isinstance(result1, ParseResult), f"Expected ParseResult, got {type(result1)}"
    assert result1.status == "miss", f"Expected status 'miss', got '{result1.status}'"
    assert result1.cache_key is not None, "cache_key should not be None"
    
    # Segundo parseo (debería ser hit con cache)
    result2 = builder.build(file_path, content)
    assert isinstance(result2, ParseResult), f"Expected ParseResult, got {type(result2)}"
    assert result2.status == "hit", f"Expected status 'hit', got '{result2.status}'"
    assert result2.cache_key == result1.cache_key, "cache_key should be same"
    
    # Ambos deberían tener los mismos símbolos
    assert result1.symbols == result2.symbols, "Symbols should be same"
    
    # Verificar estadísticas de cache
    stats = cache.stats()
    assert stats.hits == 1, f"Expected 1 hit, got {stats.hits}"
    assert stats.misses == 1, f"Expected 1 miss, got {stats.misses}"


def test_different_builders_share_cache() -> None:
    """
    Test que verifica que distintos builders comparten cache.
    
    Después del fix, cuando se inyecta el mismo cache en ambos builders,
    ambos comparten el cache.
    """
    cache = InMemoryLRUCache(max_entries=100, max_bytes=1000)
    builder1 = SkeletonMapBuilder(cache=cache, segment_id=".")
    builder2 = SkeletonMapBuilder(cache=cache, segment_id=".")
    file_path = Path("test.py")
    content = "def test(): pass"
    
    # Primer parseo con builder1 (debería ser miss)
    result1 = builder1.build(file_path, content)
    assert isinstance(result1, ParseResult), f"Expected ParseResult, got {type(result1)}"
    assert result1.status == "miss", f"Expected status 'miss', got '{result1.status}'"
    
    # Segundo parseo con builder2 (debería ser hit con cache compartido)
    result2 = builder2.build(file_path, content)
    assert isinstance(result2, ParseResult), f"Expected ParseResult, got {type(result2)}"
    assert result2.status == "hit", f"Expected status 'hit', got '{result2.status}'"
    
    # Con el mismo cache, ambos deberían tener los mismos símbolos
    assert result1.symbols == result2.symbols, "Symbols should be same with shared cache"
    
    # Verificar que el cache tiene 1 hit y 1 miss
    stats = cache.stats()
    assert stats.hits == 1, f"Expected 1 hit, got {stats.hits}"
    assert stats.misses == 1, f"Expected 1 miss, got {stats.misses}"


def test_cache_key_format_versionable() -> None:
    """
    Test que verifica que el formato de clave de cache es versionable.
    
    Después del fix, SkeletonMapBuilder tiene un método _make_cache_key()
    con formato versionable: {segment_id}:{file_rel}:{content_sha256_16}:{cache_version}
    """
    builder = SkeletonMapBuilder(cache=NullCache(), segment_id=".")
    
    # Verificar que existe el método _make_cache_key
    assert hasattr(builder, "_make_cache_key"), \
        "SkeletonMapBuilder should have _make_cache_key after fix"
    
    # Verificar que hay versión del formato de cache
    assert hasattr(builder, "CACHE_VERSION"), \
        "SkeletonMapBuilder should have CACHE_VERSION after fix"
    
    # Verificar formato de clave
    file_path = Path("test.py")
    content = "def test(): pass"
    cache_key = builder._make_cache_key(str(file_path), content)
    
    # Formato esperado: {segment_id}:{file_rel}:{content_sha256_16}:{cache_version}
    parts = cache_key.split(":")
    assert len(parts) == 4, f"Expected 4 parts in cache_key, got {len(parts)}"
    assert parts[0] == ".", f"Expected segment_id '.', got '{parts[0]}'"
    assert parts[1] == str(file_path), f"Expected file_rel '{file_path}', got '{parts[1]}'"
    assert len(parts[2]) == 16, f"Expected 16-char hash, got {len(parts[2])}"
    assert parts[3] == str(builder.CACHE_VERSION), \
        f"Expected version '{builder.CACHE_VERSION}', got '{parts[3]}'"


def test_parse_result_structure() -> None:
    """
    Test que verifica que build() retorna ParseResult con status de cache.
    
    Después del fix, build() retorna ParseResult con símbolos, status
    y cache_key.
    """
    builder = SkeletonMapBuilder(cache=NullCache())
    file_path = Path("test.py")
    content = "def test(): pass"
    
    result = builder.build(file_path, content)
    
    # Después del fix, result es ParseResult
    assert isinstance(result, ParseResult), f"Expected ParseResult, got {type(result)}"
    
    # Verificar que tiene atributos de ParseResult
    assert hasattr(result, "status"), "Result should have status attribute"
    assert hasattr(result, "cache_key"), "Result should have cache_key attribute"
    assert hasattr(result, "symbols"), "Result should have symbols attribute"
    
    # Verificar tipos
    assert isinstance(result.status, str), f"status should be str, got {type(result.status)}"
    assert isinstance(result.cache_key, str), f"cache_key should be str, got {type(result.cache_key)}"
    assert isinstance(result.symbols, list), f"symbols should be list, got {type(result.symbols)}"
    
    # Verificar valores
    assert result.status in ("hit", "miss", "error"), \
        f"status should be 'hit', 'miss' or 'error', got '{result.status}'"
    assert len(result.cache_key) > 0, "cache_key should not be empty"


def test_cache_error_handling() -> None:
    """
    Test que verifica que los errores de cache se manejan correctamente.
    """
    cache = InMemoryLRUCache(max_entries=100, max_bytes=1000)
    builder = SkeletonMapBuilder(cache=cache, segment_id=".")
    file_path = Path("test.py")
    
    # Contenido con error de sintaxis
    content = "def test(: pass"
    
    result = builder.build(file_path, content)
    
    # Verificar que el error se maneja correctamente
    assert isinstance(result, ParseResult), f"Expected ParseResult, got {type(result)}"
    assert result.status == "error", f"Expected status 'error', got '{result.status}'"
    assert result.symbols == [], "Symbols should be empty on syntax error"
    
    # Verificar que el error se cachea (fail-closed)
    result2 = builder.build(file_path, content)
    assert result2.status == "hit", "Error should be cached"
    assert result2.symbols == [], "Cached error should have empty symbols"
