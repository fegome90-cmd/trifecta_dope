### Tool Runtime

```python
def get_context(chunk_id: str) -> str:
    """Get full text of a chunk by ID."""
    pack = load_json("context_pack.json")
    for chunk in pack["chunks"]:
        if chunk["id"] == chunk_id:
            return chunk["text"]
    raise ValueError(f"Chunk not found: {chunk_id}")
```

---
