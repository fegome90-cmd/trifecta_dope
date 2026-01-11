### A.2 Event Format (JSONL)

**Example from events.jsonl line 1:**
```json
{
  "ts": "2025-12-29T22:06:52.060304+00:00",
  "run_id": "run_1767046012",
  "segment": "/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope",
  "cmd": "ctx.sync",
  "args": {"segment": "."},
  "result": {"status": "ok"},
  "timing_ms": 2,
  "warnings": []
}
```

**Fields:**
- `ts` (ISO 8601 UTC): Event timestamp (wall-clock, NOT monotonic)
- `run_id` (str): Unique identifier per CLI invocation (format: `run_{unix_timestamp}`)
- `segment` (str): Absolute path to target segment
- `cmd` (str): Command name (e.g., "ctx.search", "ctx.get", "ctx.sync")
- `args` (dict): Sanitized arguments (truncated to 120 chars max per `_sanitize_args`)
- `result` (dict): Output summary (status, hit count, chunks returned, etc.)
- `timing_ms` (int): Total elapsed time in milliseconds
- `warnings` (list): List of warning strings (max 5 in last_run.json)

**Note:** `args` field currently EXCLUDES sensitive data:
- Query/task text: truncated to 120 chars (line 206: `safe[k] = v[:120]`)
- IDs, segments, limits: passed as-is
- Unknown args: silently dropped (line 213: "Skip unknown args for safety")
