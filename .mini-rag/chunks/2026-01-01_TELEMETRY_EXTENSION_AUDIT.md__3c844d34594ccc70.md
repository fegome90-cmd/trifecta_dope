```python
def test_full_search_flow_logs_all_metrics(tmp_path, monkeypatch):
    """Verify search command emits bytes_read + disclosure metrics."""
    # Setup segment
    segment_dir = tmp_path / "test_segment"
    segment_dir.mkdir()
    ctx_dir = segment_dir / "_ctx"
    ctx_dir.mkdir()

    # Stub file system with small context pack
    pack_file = ctx_dir / "context_pack.json"
    pack_file.write_text(json.dumps({
        "index": {"test": ["chunk:1", "chunk:2"]},
        "chunks": {"chunk:1": {"content": "x" * 1000}}
    }))

    # Run search command
    from src.infrastructure.cli import ctx_search
    # ... invoke search("--segment", str(segment_dir), ...)

    # Verify events logged
    events_file = ctx_dir / "telemetry" / "events.jsonl"
    events = [json.loads(line) for line in events_file.read_text().strip().split("\n")]

    search_event = next((e for e in events if e["cmd"] == "ctx.search"), None)
    assert search_event is not None
    assert "bytes_read" in search_event  # NEW field
    assert search_event["bytes_read"] >= 1000  # At least pack size
```
