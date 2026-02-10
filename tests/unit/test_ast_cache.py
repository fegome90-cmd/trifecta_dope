"""Unit tests for ast_cache module."""

from src.domain.ast_cache import InMemoryLRUCache, SQLiteCache


def test_hit_rate_validation():
    """Verify hit_rate is clamped to 0-100% range."""
    cache = InMemoryLRUCache()

    # Test edge cases - should be within 0.0 to 1.0 range
    stats = cache.stats()
    assert 0.0 <= stats.hit_rate <= 1.0, f"hit_rate {stats.hit_rate} out of range [0.0, 1.0]"

    # Test with some operations
    cache.set("key1", {"data": "value1"})
    cache.get("key1")  # hit
    cache.get("key2")  # miss

    stats = cache.stats()
    assert 0.0 <= stats.hit_rate <= 1.0, f"hit_rate {stats.hit_rate} out of range [0.0, 1.0]"


def test_hit_rate_with_sqlite_cache(tmp_path):
    """Verify hit_rate is clamped to 0-100% range for SQLiteCache."""
    db_path = tmp_path / "test.db"
    cache = SQLiteCache(db_path)

    # Test edge cases
    stats = cache.stats()
    assert 0.0 <= stats.hit_rate <= 1.0, f"hit_rate {stats.hit_rate} out of range [0.0, 1.0]"

    # Test with some operations
    cache.set("key1", {"data": "value1"})
    cache.get("key1")  # hit
    cache.get("key2")  # miss

    stats = cache.stats()
    assert 0.0 <= stats.hit_rate <= 1.0, f"hit_rate {stats.hit_rate} out of range [0.0, 1.0]"


def test_hit_rate_empty_cache():
    """Verify hit_rate is 0.0 for empty cache."""
    cache = InMemoryLRUCache()
    stats = cache.stats()

    # Empty cache should have 0.0 hit rate
    assert stats.hit_rate == 0.0, f"Empty cache should have hit_rate=0.0, got {stats.hit_rate}"
    assert stats.hits == 0
    assert stats.misses == 0
