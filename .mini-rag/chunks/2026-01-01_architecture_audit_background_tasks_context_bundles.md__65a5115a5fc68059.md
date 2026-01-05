### 4.4 `task_state.json` (Background Task State)

```json
{
  "schema_version": 1,
  "task_id": "task_abc123",
  "command": {
    "name": "ctx build",
    "args": {"segment": "."}
  },
  "state": "RUNNING",
  "state_history": [
    {"state": "PENDING", "timestamp": "2026-01-01T12:05:00Z"},
    {"state": "RUNNING", "timestamp": "2026-01-01T12:05:01Z"}
  ],
  "started_at": "2026-01-01T12:05:00Z",
  "updated_at": "2026-01-01T12:05:15Z",
  "heartbeat_last": "2026-01-01T12:05:15Z",
  "process": {
    "pid": 12345,
    "cwd": "/workspaces/trifecta_dope",
    "env": {
      "TRIFECTA_TELEMETRY_LEVEL": "lite"
    }
  },
  "output": {
    "log_path": "_ctx/tasks/task_abc123/output.log",
    "log_size_bytes": 4567,
    "last_lines": ["Building context pack...", "7 chunks created"]
  },
  "result": null,
  "error": null,
  "timeout_at": "2026-01-01T12:15:00Z"
}
```

**State Transitions**:
- `PENDING → RUNNING`: Task spawn success.
- `RUNNING → DONE`: Exit code 0.
- `RUNNING → FAILED`: Exit code != 0.
- `RUNNING → TIMEOUT`: Heartbeat > 10min stale.
- `RUNNING → CANCELLED`: SIGTERM received.

---
