```json
{
  "schema_version": 1,
  "run_id": "run_1735772400",
  "created_at": "2026-01-01T12:00:00Z",
  "segment": "trifecta_dope",
  "command": {
    "name": "ctx search",
    "args": {
      "query": "validate segment",
      "segment": ".",
      "limit": 5
    }
  },
  "environment": {
    "python_version": "3.12.1",
    "uv_version": "0.1.18",
    "os": "Linux",
    "cwd": "/workspaces/trifecta_dope"
  },
  "tool_calls": [
    {
      "id": "tc_001",
      "parent_id": null,
      "name": "ctx.search",
      "args": {"query": "validate segment"},
      "result": {
        "hits": [
          {"id": "agent:39151e4814", "score": 0.50, "preview": "..."}
        ]
      },
      "timing_ms": 45,
      "timestamp": "2026-01-01T12:00:01.123Z",
      "execution_order": 1
    }
  ],
  "file_reads": [
    {
      "path": "_ctx/context_pack.json",
      "sha256": "abc123...",
      "lines_read": [1, 156],
      "char_count": 28989,
      "redacted": false
    }
  ],
  "file_writes": [
    {
      "path": "_ctx/session_trifecta_dope.md",
      "operation": "append",
      "lines_added": 8,
      "sha256_after": "def456..."
    }
  ],
  "policies_applied": {
    "source": "_ctx/ctx_bundle_rules.yaml",
    "sha256": "789abc...",
    "violations": 0
  },
  "metadata": {
    "sha256_digest": "bundle_hash_xyz",
    "bundle_size_bytes": 45678,
    "finalized_at": "2026-01-01T12:00:05.000Z
