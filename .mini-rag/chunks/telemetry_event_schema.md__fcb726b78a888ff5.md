## Security & Redaction Policy

1. **Paths:** Always use `_relpath(repo_root, path)` to log relative paths. NEVER log absolute paths or URIs with user/system info.
2. **Segment:** Log `segment_id` (SHA-256 hash prefix), not `segment_path` (prevents path leakage).
3. **Content:** Do not log file content. Log hashes (SHA-256), sizes, and line ranges only.
4. **Secrets:** Do not log API keys, tokens, or credentials in any field.
5. **Reserved Keys:** `ts`, `run_id`, `segment_id`, `cmd`, `args`, `result`, `timing_ms`, `tokens`, `warnings`, `x` are protected. Extra fields go under `x` namespace.
6. **External Files:** Files outside workspace are logged as `external/<hash8>-<name>` for privacy + uniqueness.

---
