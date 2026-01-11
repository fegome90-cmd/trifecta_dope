```json
  {
    "schema_version": 1,
    "run_id": "run_1735772400",
    "created_at": "2026-01-01T12:00:00Z",
    "command": "trifecta ctx search",
    "args": {"query": "validate", "segment": ".", "limit": 5},
    "fp_gate_result": {
      "status": "ok",
      "validation": {"passed": true, "errors": [], "warnings": []}
    },
    "tool_calls": [
      {
        "id": "tc_001",
        "name": "ctx.search",
        "args": {"query": "validate"},
        "result": {"hits": 3},
        "timing_ms": 45,
        "timestamp": "2026-01-01T12:00:01Z"
      }
    ],
    "pcc_metrics": {
      "path_correct": true,
      "false_fallback": false,
      "safe_fallback": false,
      "feature_map_source": "_ctx/prime_trifecta_dope.md"
    },
    "file_reads": [
      {"path": "_ctx/context_pack.json", "lines": [1, 156], "char_count": 28989}
    ],
    "sha256_digest": "abc123...",
    "policies_applied": "ctx_bundle_rules.yaml"
  }
  ```
- [ ] Policy file `_ctx/ctx_bundle_rules.yaml` con allowlist/denylist/limits:
