### ⚠️ Origin Separation Issue (PII Redaction)
- **Finding**: 97% of events (2058/2114) have `<ABS_PATH_REDACTED>` in the segment path.
- **Impact**: Impossible to distinguish **Real User CLI** vs **Pytest Harness** executions historically.
- **Result**: Global latency metrics are dominated by sub-millisecond unit tests.
- **Correction**: Future telemetry must include a non-PII `context: "user|test"` field.
