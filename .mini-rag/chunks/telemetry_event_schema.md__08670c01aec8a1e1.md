### Reserved Keys

The following keys are **reserved** and cannot be overridden by `extra_fields`:

- `ts`: Timestamp (ISO 8601 UTC)
- `run_id`: Unique run identifier
- `segment_id`: SHA-256 hash (8 chars) of segment path (privacy)
- `cmd`: Command/event type
- `args`: Command arguments (sanitized)
- `result`: Command result metadata
- `timing_ms`: Elapsed time in milliseconds
- `tokens`: Token usage estimation
- `warnings`: Warning messages
- `x`: Namespace for extra fields
