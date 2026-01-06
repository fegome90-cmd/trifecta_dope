import pytest
import sqlite3
import json
import time
from pathlib import Path
from src.domain.ast_cache import SQLiteCache, CacheEntry
from src.application.ast_parser import SkeletonMapBuilder


# Fixture pointing to the minimal file
@pytest.fixture
def minimal_file(tmp_path):
    f = tmp_path / "minimal.py"
    f.write_text("""
def hello():
    print("Hello World")

class Foo:
    def bar(self):
        return 42
""")
    return f


def test_sqlite_cache_roundtrip_determinism(tmp_path):
    """
    RED TEST: Verify SQLiteCache can persist and retrieve AST data deterministically.
    """
    db_path = tmp_path / "cache.db"
    cache = SQLiteCache(db_path=db_path)

    key = "test_key_v1"
    value = {"symbols": [{"name": "hello", "kind": "function"}]}

    # 1. Write
    cache.set(key, value)

    # 2. Close and Reopen (simulate new process)
    # SQLiteCache doesn't have explicit close, but we create new instance
    cache2 = SQLiteCache(db_path=db_path)

    # 3. Read
    retrieved = cache2.get(key)

    assert retrieved is not None, "Cache miss after persistence roundtrip"
    assert retrieved == value, f"Value mismatch: {retrieved} != {value}"

    # 4. Verify DB file structure (Contract)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT key, value FROM cache WHERE key=?", (key,))
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == key
        assert json.loads(row[1]) == value


def test_skeleton_builder_persistence_cross_run(tmp_path, minimal_file):
    """
    RED TEST: Verify SkeletonMapBuilder actually uses the cache cross-run.
    We simulate this by checking if the second run hits the cache (detectable via
    telemetry or internal stats, logic is opaque so we assume shorter time or stats).
    """
    db_path = tmp_path / "persist.db"

    # Run 1: Cold
    cache1 = SQLiteCache(db_path=db_path)
    # Clear to be sure
    cache1.clear()

    builder1 = SkeletonMapBuilder(cache=cache1, segment_id="test_seg")
    # Initial build
    result1 = builder1.build(minimal_file)
    assert result1.status == "miss" or result1.status == "generated", (
        f"Expected cold miss, got {result1.status}"
    )

    # Run 2: Warm (New instance, same DB)
    cache2 = SQLiteCache(db_path=db_path)
    builder2 = SkeletonMapBuilder(cache=cache2, segment_id="test_seg")

    result2 = builder2.build(minimal_file)

    # Assert Hit
    # NOTE: This implies SkeletonMapBuilder correctly logic for checking cache before parsing
    assert result2.status == "hit", f"Expected cache hit on second run, got {result2.status}"
    assert result2.symbols == result1.symbols
