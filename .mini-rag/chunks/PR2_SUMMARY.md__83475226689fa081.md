### Sample events.jsonl (sanitized, 5 lines)

```json
{"ts": "2026-01-01T07:02:49Z", "run_id": "run_1767250969", "segment_id": "b64328bb", "cmd": "ast.parse", "args": {}, "result": {"status": "ok", "symbols_count": 0}, "timing_ms": 0, "x": {"file": "/workspaces/trifecta_dope/demo_pr2_sample.py", "content_sha8": "2dfc080c", "skeleton_bytes": 2, "cache_hit": false}}

{"ts": "2026-01-01T07:02:49Z", "run_id": "run_1767250969", "segment_id": "b64328bb", "cmd": "selector.resolve", "args": {"query": "sym://python/Demo"}, "result": {"status": "not_resolved", "resolved": false}, "timing_ms": 0, "x": {"symbol_query": "Demo", "resolved": false, "matches": 0, "ambiguous": false}}
```
