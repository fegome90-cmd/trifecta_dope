## Output Format (JSONL)

Each command run produces a JSON entry with **typed fields** (v1.1+):

```json
{
  "timestamp": "2026-01-02T11:45:00Z",
  "command": "uv run trifecta ctx get -s . --ids prime:abc,skill:xyz --pd-report",
  "returncode": 0,
  "success": true,
  "pd_report": {
    "v": "1",
    "stop_reason": "complete",
    "chunks_returned": 1,
    "chunks_requested": 1,
    "chars_returned_total": 512,
    "strong_hit": 0,
    "support": 0
  }
}
```

**Note**: Numeric fields (`chunks_returned`, `chunks_requested`, `chars_returned_total`, `strong_hit`, `support`) are **int**, not strings.

Or on failure:

```json
{
  "timestamp": "2026-01-02T11:45:00Z",
  "command": "uv run trifecta ctx sync -s /tmp/uninit",
  "returncode": 1,
  "success": false,
  "error_card": {
    "code": "SEGMENT_NOT_INITIALIZED",
    "class": "Precondition",
    "cause": "Missing _ctx/trifecta_config.json"
  },
  "error_prompt": "❌ Command Failed: ...\n\nRecovery Steps:\n1. ..."
}
```
