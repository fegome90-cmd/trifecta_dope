```python
# tests/unit/test_path_hygiene.py
def test_context_pack_sanitized_dump_no_pii():
    """Unit: sanitized_dump() elimina paths absolutos."""
    from src.domain.context_models import TrifectaPack
    pack = TrifectaPack(
        repo_root=Path("/Users/felipe/Developer/agent_h"),
        segment=".",
        schema_version=1,
        digest=[],
        index=[],
        chunks=[]
    )
    json_str = pack.sanitized_dump()
    assert "/Users/" not in json_str, f"Found /Users/ in: {json_str}"
    assert "/home/" not in json_str
    assert "file://" not in json_str
    assert "<REPO_ROOT>" in json_str
```

**Integration test (CRÍTICO):**
